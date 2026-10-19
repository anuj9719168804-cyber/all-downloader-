"""
Admin commands ported from fbot:

  /ban <user_id>      ban a user (or reply to their message with /ban)
  /unban <user_id>    unban a user
  /broadcast <text>   send text to every registered user
  /broadcast          (as a reply to any message) copy that message to every user

Also installs a guard that runs before every other handler (group -1):
  * registers every private user so they are reachable by broadcast
  * stops banned users from using the bot (messages and buttons)
"""
import threading
import time

from pyrogram import Client, filters, StopPropagation, enums
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid

from CONFIG.config import Config
from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from DATABASE.bot_users_db import (
    register_user,
    is_banned,
    set_banned,
    get_broadcast_targets,
    mark_unreachable,
)

app = get_app()

BANNED_TEXT = "🚫 You have been banned from using this bot."
UNBANNED_TEXT = "✅ You have been unbanned. You can use the bot again."
BROADCAST_DELAY = 0.05      # seconds between messages (keeps us under Telegram's limits)
FLOOD_RETRIES = 5

_ban_notice_sent = {}       # user_id -> last time we told a banned user (avoid spamming them)
BAN_NOTICE_INTERVAL = 3600


def _is_admin(_, __, message) -> bool:
    return bool(message.from_user) and message.from_user.id in Config.ADMIN


ADMIN_FILTER = filters.create(_is_admin, name="BanBroadcastAdminFilter")


def _parse_user_id(message):
    """Return the target user id from '/cmd <id>' or from a replied-to message, else None."""
    parts = (message.text or "").split()
    if len(parts) >= 2 and parts[1].lstrip("-").isdigit():
        return int(parts[1])
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    return None


# ---------------------------------------------------------------------
# Guard: runs before all other handlers
# ---------------------------------------------------------------------

@app.on_message(filters.private, group=-1)
def _user_guard(client, message):
    if not message.from_user:
        return
    uid = message.from_user.id
    register_user(uid)
    if uid in Config.ADMIN or not is_banned(uid):
        return

    now = time.time()
    if now - _ban_notice_sent.get(uid, 0) > BAN_NOTICE_INTERVAL:
        _ban_notice_sent[uid] = now
        try:
            message.reply_text(BANNED_TEXT)
        except Exception:
            pass
    raise StopPropagation


@app.on_callback_query(group=-1)
def _callback_guard(client, callback_query):
    uid = callback_query.from_user.id if callback_query.from_user else None
    if uid is None or uid in Config.ADMIN or not is_banned(uid):
        return
    try:
        callback_query.answer(BANNED_TEXT, show_alert=True)
    except Exception:
        pass
    raise StopPropagation


# ---------------------------------------------------------------------
# /ban and /unban
# ---------------------------------------------------------------------

@app.on_message(filters.command("ban") & filters.private & ADMIN_FILTER)
def ban_cmd(client, message):
    target = _parse_user_id(message)
    if target is None:
        return message.reply_text(
            "⚠️ Usage: <code>/ban &lt;user_id&gt;</code> (or reply to a user's message with /ban)",
            parse_mode=enums.ParseMode.HTML,
        )
    if target in Config.ADMIN:
        return message.reply_text("⚠️ Can't ban an admin.")

    saved = set_banned(target, True)
    note = "" if saved else "\n⚠️ Database unavailable: ban is only active in this session."
    message.reply_text(f"🚫 <code>{target}</code> has been banned.{note}", parse_mode=enums.ParseMode.HTML)
    try:
        client.send_message(target, BANNED_TEXT)
    except Exception as e:
        logger.warning(f"[BAN] couldn't notify {target}: {e}")


@app.on_message(filters.command("unban") & filters.private & ADMIN_FILTER)
def unban_cmd(client, message):
    target = _parse_user_id(message)
    if target is None:
        return message.reply_text(
            "⚠️ Usage: <code>/unban &lt;user_id&gt;</code> (or reply to a user's message with /unban)",
            parse_mode=enums.ParseMode.HTML,
        )

    saved = set_banned(target, False)
    note = "" if saved else "\n⚠️ Database unavailable: unban is only active in this session."
    message.reply_text(f"✅ <code>{target}</code> has been unbanned.{note}", parse_mode=enums.ParseMode.HTML)
    _ban_notice_sent.pop(target, None)
    try:
        client.send_message(target, UNBANNED_TEXT)
    except Exception as e:
        logger.warning(f"[UNBAN] couldn't notify {target}: {e}")


# ---------------------------------------------------------------------
# /broadcast
# ---------------------------------------------------------------------

def _send_one(client, user_id, text, from_chat_id, message_id):
    """Send to one user. Returns 'success', 'unreachable' or 'failed'."""
    for _ in range(FLOOD_RETRIES):
        try:
            if text is not None:
                client.send_message(user_id, text, parse_mode=enums.ParseMode.DISABLED)
            else:
                client.copy_message(chat_id=user_id, from_chat_id=from_chat_id, message_id=message_id)
            return "success"
        except FloodWait as e:
            wait = getattr(e, "value", None) or getattr(e, "x", None) or 30
            time.sleep(wait + 1)
        except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
            mark_unreachable(user_id)
            return "unreachable"
        except Exception as e:
            logger.warning(f"[BROADCAST] failed for {user_id}: {e}")
            return "failed"
    return "failed"


def _progress_text(total, done, success, unreachable, failed, final=False):
    title = "📣 <b>Broadcast done.</b>" if final else "📣 <b>Broadcast in progress...</b>"
    lines = [title, ""]
    if not final:
        lines.append(f"👥 Total: {total}")
        lines.append(f"💫 Done: {done}/{total}")
    lines += [
        f"✅ Success: {success}",
        f"🚫 Unreachable (blocked/deleted, skipped next time): {unreachable}",
        f"❌ Failed: {failed}",
    ]
    return "\n".join(lines)


def _run_broadcast(client, admin_chat_id, status_id, targets, text, from_chat_id, message_id):
    total = len(targets)
    done = success = unreachable = failed = 0

    for uid in targets:
        result = _send_one(client, uid, text, from_chat_id, message_id)
        done += 1
        if result == "success":
            success += 1
        elif result == "unreachable":
            unreachable += 1
        else:
            failed += 1

        if done % 20 == 0 or done == total:
            try:
                client.edit_message_text(
                    admin_chat_id, status_id,
                    _progress_text(total, done, success, unreachable, failed),
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass
        time.sleep(BROADCAST_DELAY)

    try:
        client.edit_message_text(
            admin_chat_id, status_id,
            _progress_text(total, done, success, unreachable, failed, final=True),
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        pass
    logger.info(f"[BROADCAST] finished: total={total} success={success} unreachable={unreachable} failed={failed}")


@app.on_message(filters.command("broadcast") & filters.private & ADMIN_FILTER)
def broadcast_cmd(client, message):
    reply = message.reply_to_message
    parts = (message.text or "").split(None, 1)
    text = parts[1] if len(parts) > 1 else None

    if text is None and reply is None:
        return message.reply_text(
            "⚠️ Usage: <code>/broadcast &lt;message&gt;</code>\n"
            "(or reply to any message with <code>/broadcast</code> to send a copy of it)",
            parse_mode=enums.ParseMode.HTML,
        )

    targets = get_broadcast_targets()
    if not targets:
        return message.reply_text("⚠️ No users to broadcast to (or the database is unavailable).")

    status = message.reply_text(f"📣 Broadcasting to {len(targets)} users...")
    # Text wins if both text and a reply are given (same as fbot).
    from_chat_id = message.chat.id
    message_id = reply.id if (reply is not None and text is None) else None
    threading.Thread(
        target=_run_broadcast,
        args=(client, message.chat.id, status.id, targets, text, from_chat_id, message_id),
        daemon=True,
    ).start()
