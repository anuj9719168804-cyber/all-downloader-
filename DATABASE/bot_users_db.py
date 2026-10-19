"""
MongoDB-backed user registry, bans and broadcast targets.

Why this exists: in local mode (USE_FIREBASE = False) the Firebase-style user/ban
lists are read from a static dump and cannot be written, so /block_user and
/broadcast had nothing reliable to work with. This module keeps its own
collection in the same MongoDB database used for cookies.

Collection: bot_users
  _id           user_id (int)
  first_seen    datetime
  last_seen     datetime
  banned        bool      (set by /ban, cleared by /unban)
  banned_at     datetime | None
  unreachable   bool      (broadcast got UserIsBlocked / PeerIdInvalid / deactivated)

Everything is best-effort: if MongoDB is down, bans fail open (users are not
blocked), registration is skipped and the bot keeps working.
"""
import threading
import time
from datetime import datetime

from HELPERS.logger import logger
from HELPERS.mongo_cookies import MONGO_URI, MONGO_DB_NAME

USERS_COLLECTION = "bot_users"
BAN_CACHE_TTL = 60          # seconds a ban status is cached in memory
RETRY_AFTER_FAIL = 60       # seconds before trying to reconnect after a failure

_lock = threading.Lock()
_col = None
_last_fail = 0.0
_ban_cache = {}             # user_id -> (banned: bool, expires_at: float)


def _get_col():
    """Return the collection, connecting lazily. Returns None if MongoDB is unavailable."""
    global _col, _last_fail
    if _col is not None:
        return _col
    if time.time() - _last_fail < RETRY_AFTER_FAIL:
        return None
    with _lock:
        if _col is not None:
            return _col
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
            client.admin.command("ping")
            col = client[MONGO_DB_NAME][USERS_COLLECTION]
            col.create_index("banned")
            col.create_index("unreachable")
            _col = col
            logger.info("[BOT-USERS] connected")
        except Exception as e:
            _last_fail = time.time()
            logger.warning(f"[BOT-USERS] MongoDB unavailable, retrying later: {e}")
            return None
    return _col


def register_user(user_id: int) -> None:
    """Remember a user so broadcasts can reach them. Cheap upsert, called on every private message."""
    col = _get_col()
    if col is None:
        return
    now = datetime.utcnow()
    try:
        col.update_one(
            {"_id": int(user_id)},
            {"$set": {"last_seen": now},
             "$setOnInsert": {"first_seen": now, "banned": False, "banned_at": None, "unreachable": False}},
            upsert=True,
        )
    except Exception as e:
        logger.warning(f"[BOT-USERS] register_user({user_id}) failed: {e}")


def is_banned(user_id: int) -> bool:
    """True if the user is banned. Cached for BAN_CACHE_TTL seconds. Fails open (False) on errors."""
    user_id = int(user_id)
    cached = _ban_cache.get(user_id)
    if cached and cached[1] > time.time():
        return cached[0]
    col = _get_col()
    if col is None:
        return False
    try:
        doc = col.find_one({"_id": user_id}, {"banned": 1})
        banned = bool(doc and doc.get("banned"))
    except Exception as e:
        logger.warning(f"[BOT-USERS] is_banned({user_id}) failed: {e}")
        return False
    _ban_cache[user_id] = (banned, time.time() + BAN_CACHE_TTL)
    return banned


def set_banned(user_id: int, banned: bool) -> bool:
    """Ban or unban a user. Returns False if the database could not be written."""
    user_id = int(user_id)
    col = _get_col()
    _ban_cache[user_id] = (banned, time.time() + BAN_CACHE_TTL)  # takes effect immediately in this process
    if col is None:
        return False
    now = datetime.utcnow()
    try:
        col.update_one(
            {"_id": user_id},
            {"$set": {"banned": banned, "banned_at": now if banned else None},
             "$setOnInsert": {"first_seen": now, "last_seen": now, "unreachable": False}},
            upsert=True,
        )
        return True
    except Exception as e:
        logger.warning(f"[BOT-USERS] set_banned({user_id}, {banned}) failed: {e}")
        return False


def get_broadcast_targets() -> list[int]:
    """All users who should receive a broadcast: not banned, and not known to be unreachable."""
    col = _get_col()
    if col is None:
        return []
    try:
        cursor = col.find(
            {"banned": {"$ne": True}, "unreachable": {"$ne": True}},
            {"_id": 1},
        )
        return [int(doc["_id"]) for doc in cursor]
    except Exception as e:
        logger.warning(f"[BOT-USERS] get_broadcast_targets failed: {e}")
        return []


def mark_unreachable(user_id: int) -> None:
    """Called when Telegram says the user blocked the bot or deleted the account."""
    col = _get_col()
    if col is None:
        return
    try:
        col.update_one({"_id": int(user_id)}, {"$set": {"unreachable": True}})
    except Exception as e:
        logger.warning(f"[BOT-USERS] mark_unreachable({user_id}) failed: {e}")
