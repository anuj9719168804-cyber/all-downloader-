# #############################################################################################################################

import os
import re
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters
from HELPERS.safe_messeger import safe_send_message

from HELPERS.app_instance import get_app
from HELPERS.decorators import background_handler
from HELPERS.logger import send_to_logger, send_to_user
from HELPERS.limitter import is_user_in_channel, check_user, check_playlist_range_limits
from HELPERS.download_status import get_active_download, can_start_download
from HELPERS.filesystem_hlp import create_directory

from CONFIG.config import Config
from CONFIG.messages import safe_get_messages

from URL_PARSERS.tags import extract_url_range_tags, save_user_tags

from DOWN_AND_UP.down_and_audio import down_and_audio
from COMMANDS.link_cmd import link_command
from COMMANDS.proxy_cmd import proxy_command

# Get app instance for decorators
app = get_app()


def _check_access(message, *, require_channel: bool = True) -> bool:
    """Common access check for private-chat command handlers.
    
    Returns True if the user is allowed to proceed, False if a guard
    already sent a response or the user should be silently dropped.
    """
    user_id = message.chat.id
    is_admin = int(user_id) in Config.ADMIN
    text = getattr(message, 'text', '').strip() if hasattr(message, 'text') else ''
    is_ignore_command = text.startswith(Config.IGNORE_USER_COMMAND) or text.startswith(Config.UNIGNORE_USER_COMMAND)

    if not is_ignore_command:
        from DATABASE.firebase_init import is_user_ignored
        if is_user_ignored(message):
            return False

    if not is_admin:
        from DATABASE.firebase_init import is_user_blocked
        if is_user_blocked(message):
            return False

    if require_channel and not is_admin and not is_user_in_channel(app, message):
        return False

    return True


def _close_callback(callback_query, answer_msg_key: str, log_msg_key: str) -> None:
    """Handle a generic 'close' callback: delete message (or clear markup), answer, and log."""
    user_id = callback_query.from_user.id
    _messages = safe_get_messages(user_id)
    try:
        callback_query.message.delete()
    except Exception:
        callback_query.edit_message_reply_markup(reply_markup=None)
    callback_query.answer(getattr(_messages, answer_msg_key, ""))
    send_to_logger(callback_query.message, getattr(_messages, log_msg_key, ""))


# Keep only the callback handler for help close button
@app.on_callback_query(filters.regex(r"^help_msg\|"))
def help_msg_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        _close_callback(callback_query, "OTHER_HELP_CLOSED_MSG", "HELP_MESSAGE_CLOSED_LOG_MSG")


BOT_DISPLAY_NAME = "Universal Video Downloader"
BOT_USERNAME = "@UniversalVideosDownloadBot"


@app.on_callback_query(filters.regex(r"^start_menu\|"))
def start_menu_callback(app, callback_query):
    """Help / About buttons under the /start welcome message."""
    data = callback_query.data.split("|")[1]
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    try:
        callback_query.answer()
    except Exception:
        pass
    if data == "help":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Close", callback_data="help_msg|close")]
        ])
        safe_send_message(chat_id, safe_get_messages(user_id).HELP_MSG,
                          parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    elif data == "about":
        text = (
            "<blockquote>ℹ️ About</blockquote>\n\n"
            f"<blockquote>🤖 Name: {BOT_DISPLAY_NAME}\n"
            f"🔗 Username: {BOT_USERNAME}</blockquote>"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Help", callback_data="start_menu|help"),
             InlineKeyboardButton("❌ Close", callback_data="help_msg|close")]
        ])
        safe_send_message(chat_id, text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


#############################################################################################################################

# Command to Download Audio from a Video url
@app.on_message(filters.command("audio") & filters.private)
@background_handler(label="audio_command")
def audio_command_handler(app, message):
    user_id = message.chat.id
    is_admin = int(user_id) in Config.ADMIN

    if not _check_access(message):
        return

    if not can_start_download(user_id):
        safe_send_message(user_id, safe_get_messages(user_id).AUDIO_WAIT_MSG, reply_parameters=ReplyParameters(message_id=message.id))
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    text = message.text
    # Нормализация синтаксиса диапазона: 
    # поддержка «/audio 1-10 URL» → преобразуем во «/audio URL*1*10» для единого пайплайна
    try:
        parts = (text or '').split()
        if len(parts) >= 3 and parts[0].lower().startswith('/audio'):
            if re.match(r"^\d+-\d*$", parts[1]):
                rng = parts[1]
                start_str, end_str = rng.split('-')
                start_val = int(start_str)
                end_val = int(end_str) if end_str != '' else None
                if start_val and start_val >= 1:
                    url_candidate = ' '.join(parts[2:]).strip()
                    if end_val is not None:
                        text = f"/audio {url_candidate}*{start_val}*{end_val}"
                    else:
                        text = f"/audio {url_candidate}*{start_val}*"
    except Exception:
        pass
    url, _, _, _, tags, tags_text, tag_error = extract_url_range_tags(text)
    if tag_error:
        wrong, example = tag_error
        error_msg = safe_get_messages(user_id).OTHER_TAG_ERROR_MSG.format(wrong=wrong, example=example)
        safe_send_message(user_id, error_msg, reply_parameters=ReplyParameters(message_id=message.id))
        from HELPERS.logger import log_error_to_channel
        log_error_to_channel(message, error_msg)
        return
    if not url:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).OTHER_AUDIO_HINT_CLOSE_BUTTON_MSG, callback_data="audio_hint|close")]
        ])
        safe_send_message(
            user_id,
            safe_get_messages(user_id).AUDIO_HELP_MSG,
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=ReplyParameters(message_id=message.id),
            reply_markup=keyboard
        )
        send_to_logger(message, safe_get_messages(user_id).AUDIO_HELP_SHOWN_LOG_MSG)
        return
    save_user_tags(user_id, tags)
    
    # Extract playlist parameters from the message
    full_string = text or message.caption or ""
    _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
    # Правильное вычисление video_count для отрицательных индексов
    if video_start_with < 0 and video_end_with < 0:
        video_count = abs(video_end_with) - abs(video_start_with) + 1
    elif video_start_with > video_end_with:
        video_count = abs(video_start_with - video_end_with) + 1
    else:
        video_count = video_end_with - video_start_with + 1
    
    # Checking the range limit
    if not check_playlist_range_limits(url, video_start_with, video_end_with, app, message):
        return
    
    # Note: cached_video_info=None for direct calls (no optimization available)
    down_and_audio(app, message, url, tags, quality_key="mp3", playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with, format_override="ba", cached_video_info=None)


# /Link Command
@app.on_message(filters.command("link") & filters.private)
@background_handler(label="link_command")
def link_command_handler(app, message):
    if not _check_access(message):
        return
    link_command(app, message)

# /Proxy Command
@app.on_message(filters.command("proxy") & filters.private)
@background_handler(label="proxy_command")
def proxy_command_handler(app, message):
    if not _check_access(message, require_channel=False):
        return
    proxy_command(app, message)


# /Playlist Command
@app.on_message(filters.command("playlist") & filters.private)
@background_handler(label="playlist_command")
def playlist_command(app, message):
    user_id = message.chat.id

    if not _check_access(message):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(safe_get_messages(user_id).OTHER_PLAYLIST_HELP_CLOSE_BUTTON_MSG, callback_data="playlist_help|close")]
    ])
    safe_send_message(user_id, safe_get_messages(user_id).PLAYLIST_HELP_MSG, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard, message=message)
    send_to_logger(message, safe_get_messages(user_id).PLAYLIST_HELP_REQUESTED_LOG_MSG)

@app.on_callback_query(filters.regex(r"^playlist_help\|"))
def playlist_help_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        _close_callback(callback_query, "PLAYLIST_HELP_CLOSED_MSG", "PLAYLIST_HELP_CLOSED_LOG_MSG")

@app.on_callback_query(filters.regex(r"^userlogs_close\|"))
def userlogs_close_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        _close_callback(callback_query, "OTHER_LOGS_MESSAGE_CLOSED_MSG", "USERLOGS_CLOSED_MSG")

@app.on_callback_query(filters.regex(r"^audio_hint\|"))
def audio_hint_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        _close_callback(callback_query, "AUDIO_HELP_CLOSED_MSG", "AUDIO_HINT_CLOSED_LOG_MSG")


# ── Force Subscribe: pending URL helper ────────────────────────────────────

def _load_and_clear_pending_url(user_id):
    """Read users/<id>/pending_url.json (written by limitter._send_subscribe_prompt),
    delete it and return the saved URL (or None)."""
    import json as _json
    pf = os.path.join("users", str(user_id), "pending_url.json")
    try:
        if not os.path.exists(pf):
            return None
        with open(pf, "r") as f:
            data = _json.load(f)
        try:
            os.remove(pf)
        except Exception:
            pass
        return (data or {}).get("url")
    except Exception:
        return None


# ── Force Subscribe: "I've Joined" callback ──────────────────────────────────

@app.on_callback_query(filters.regex(r"^check_sub\|"))
def check_sub_callback(app, callback_query):
    """Handle '✅ I've Joined' button — re-check channel membership."""
    try:
        user_id = callback_query.from_user.id
        _messages = safe_get_messages(user_id)

        if not getattr(Config, 'SUBSCRIBE_CHANNEL', None):
            callback_query.answer("✅ No channel restriction.", show_alert=False)
            return

        from pyrogram.errors import UserNotParticipant
        from pyrogram.enums import ChatMemberStatus

        _VALID = (ChatMemberStatus.MEMBER, ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)

        try:
            member = app.get_chat_member(Config.SUBSCRIBE_CHANNEL, user_id)
            is_member = member.status in _VALID
        except UserNotParticipant:
            is_member = False
        except Exception as e:
            from HELPERS.logger import logger
            logger.error(f"check_sub: error checking membership for {user_id}: {e}")
            is_member = False

        if is_member:
            # Delete the subscription prompt message
            try:
                callback_query.message.delete()
            except Exception:
                try:
                    callback_query.edit_message_reply_markup(reply_markup=None)
                except Exception:
                    pass
            callback_query.answer(
                getattr(_messages, 'CHANNEL_JOINED_CHECK_BUTTON_MSG', '✅ Verified!'),
                show_alert=False
            )

            # Step 2 of the flow: membership confirmed -> show the language selection.
            # A saved pending URL (if any) is processed after the language is chosen
            # (see lang_callback in URL_PARSERS/url_extractor.py).
            from HELPERS.limitter import create_language_keyboard
            safe_send_message(
                chat_id=user_id,
                text=getattr(_messages, 'LANG_SELECTION_MSG', '<b>Choose language</b>'),
                reply_markup=create_language_keyboard(),
                parse_mode=enums.ParseMode.HTML
            )
        else:
            from HELPERS.limitter import get_subscribe_channel_url
            channel_url = get_subscribe_channel_url()
            callback_query.answer(
                getattr(_messages, 'CHANNEL_JOIN_STILL_NOT_MEMBER_MSG',
                    '❌ You are not subscribed yet. Please join first.').format(channel_url=channel_url),
                show_alert=True
            )
    except Exception as e:
        from HELPERS.logger import logger
        logger.error(f"check_sub_callback error: {e}")
        try:
            callback_query.answer("❌ Error checking subscription.", show_alert=True)
        except Exception:
            pass


# ── Auto-approve join requests for SUBSCRIBE_CHANNEL ────────────────────────

@app.on_chat_join_request()
def auto_approve_join_request(app, join_request):
    """Auto-approve join requests for the bot's subscribe channel."""
    try:
        from HELPERS.logger import logger
        if not getattr(Config, 'SUBSCRIBE_CHANNEL', None):
            return
        channel_id = join_request.chat.id
        user_id = join_request.from_user.id

        # Only auto-approve for our configured subscribe channel
        try:
            sub_channel_id = int(Config.SUBSCRIBE_CHANNEL)
        except (ValueError, TypeError):
            return

        if channel_id != sub_channel_id:
            return

        try:
            app.approve_chat_join_request(channel_id, user_id)
            logger.info(
                getattr(
                    __import__('CONFIG.logger_msg', fromlist=['LoggerMsg']).LoggerMsg,
                    'CHANNEL_JOIN_REQUEST_APPROVED_LOG_MSG',
                    'Auto-approved join request for user {user_id} in channel {channel_id}'
                ).format(user_id=user_id, channel_id=channel_id)
            )
        except Exception as e:
            logger.error(
                getattr(
                    __import__('CONFIG.logger_msg', fromlist=['LoggerMsg']).LoggerMsg,
                    'CHANNEL_JOIN_REQUEST_APPROVE_FAILED_LOG_MSG',
                    'Failed to auto-approve join request for user {user_id}: {error}'
                ).format(user_id=user_id, error=e)
            )
    except Exception as e:
        from HELPERS.logger import logger
        logger.error(f"auto_approve_join_request error: {e}")


