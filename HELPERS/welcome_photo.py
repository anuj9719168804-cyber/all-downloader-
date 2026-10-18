"""
Welcome photo for /start.

The photo is taken from a message in a Telegram channel/group the bot is a
member of, and its file_id is cached. The welcome text is then sent as the
photo's caption (photo on top, text below). If the photo can't be loaded, or
the text is longer than Telegram's 1024-character caption limit, the bot falls
back to the normal text-only welcome (photo first, text in a separate message
when needed).

Settings (environment variables, no change to CONFIG/config.py):
  WELCOME_PHOTO_CHAT_ID     chat id of the channel, e.g. -1004457510571
                            (for t.me/c/4457510571/3 the id is -100 + 4457510571)
  WELCOME_PHOTO_MESSAGE_ID  message id of the photo post, e.g. 3
Set WELCOME_PHOTO_CHAT_ID to an empty value to disable the photo.
"""
import os
import threading

from pyrogram import enums

from HELPERS.logger import logger
from HELPERS.safe_messeger import safe_send_message

CAPTION_LIMIT = 1024  # Telegram caption limit (characters)

_DEFAULT_CHAT_ID = "-1004457510571"
_DEFAULT_MESSAGE_ID = "3"

_cache = {"file_id": None}
_lock = threading.Lock()


def _source():
    """Return (chat_id, message_id) or None if the photo is disabled/misconfigured."""
    chat_raw = os.getenv("WELCOME_PHOTO_CHAT_ID", _DEFAULT_CHAT_ID).strip()
    msg_raw = os.getenv("WELCOME_PHOTO_MESSAGE_ID", _DEFAULT_MESSAGE_ID).strip()
    if not chat_raw:
        return None
    try:
        return int(chat_raw), int(msg_raw)
    except ValueError:
        logger.error(f"welcome_photo: invalid WELCOME_PHOTO_CHAT_ID/WELCOME_PHOTO_MESSAGE_ID: {chat_raw!r}/{msg_raw!r}")
        return None


def get_welcome_photo_file_id(app):
    """Return the cached Telegram file_id of the welcome photo, loading it once."""
    with _lock:
        if _cache["file_id"]:
            return _cache["file_id"]
        src = _source()
        if not src or app is None:
            return None
        chat_id, message_id = src
        try:
            msg = app.get_messages(chat_id, message_id)
            photo = getattr(msg, "photo", None)
            if photo and getattr(photo, "file_id", None):
                _cache["file_id"] = photo.file_id
            else:
                logger.warning(f"welcome_photo: message {message_id} in {chat_id} has no photo")
        except Exception as e:
            # Usually: bot is not a member of the channel, or the message was deleted.
            logger.error(f"welcome_photo: could not load photo from {chat_id}/{message_id}: {e}")
        return _cache["file_id"]


def send_welcome(app, chat_id, text, message=None, reply_markup=None):
    """
    Send the /start welcome text, with the welcome photo above it when available.
    Falls back to a plain text message if no photo can be used.
    """
    file_id = get_welcome_photo_file_id(app)
    if file_id and len(text) <= CAPTION_LIMIT:
        try:
            app.send_photo(
                chat_id,
                file_id,
                caption=text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=reply_markup,
            )
            return
        except Exception as e:
            logger.error(f"welcome_photo: send_photo with caption failed, falling back to text: {e}")

    if file_id and len(text) > CAPTION_LIMIT:
        try:
            app.send_photo(chat_id, file_id)
        except Exception as e:
            logger.error(f"welcome_photo: send_photo failed: {e}")

    kwargs = {"parse_mode": enums.ParseMode.HTML}
    if message is not None:
        kwargs["message"] = message
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    safe_send_message(chat_id, text, **kwargs)
