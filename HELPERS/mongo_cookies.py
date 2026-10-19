# -*- coding: utf-8 -*-
"""Persist every user's cookie.txt in MongoDB (same idea as fbot's bot_settings), so cookies survive
redeploys / container restarts.

- On startup: cookies missing on disk are restored from MongoDB  (restore_all)
- While running: a background watcher uploads new/changed users/<id>/cookie.txt files (sync loop)
- /clean cookies and /clean all remove the user's copy from MongoDB too (delete_user_cookie)

Needs `pymongo` and env MONGO_URI (+ optional MONGO_DB_NAME, default "all_downloader").
Everything is best-effort: if MongoDB is unreachable the bot just keeps working with local files.
"""
import os
import time
import hashlib
import threading
from datetime import datetime

from HELPERS.logger import logger

# Same cluster as fbot (override with the MONGO_URI env var - recommended).
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://Anujedit:Anujedit@cluster0.7cs2nhd.mongodb.net/?appName=Cluster0",
)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "all_downloader")
COLLECTION = "user_cookies"
USERS_DIR = "users"
SYNC_INTERVAL = 30          # seconds between scans
STABLE_AFTER = 10           # only upload files untouched for this long (skip transient test overwrites)
MAX_BYTES = 1024 * 1024

_col = None
_col_lock = threading.Lock()
_seen = {}                  # user_id -> sha1 of what MongoDB already holds
_started = False


def _get_col():
    global _col
    if _col is not None:
        return _col
    with _col_lock:
        if _col is not None:
            return _col
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
            client.admin.command("ping")
            _col = client[MONGO_DB_NAME][COLLECTION]
            logger.info("[MONGO-COOKIES] connected")
        except Exception as e:
            logger.warning(f"[MONGO-COOKIES] disabled, MongoDB unavailable: {e}")
            _col = None
    return _col


def _cookie_path(user_id):
    return os.path.join(USERS_DIR, str(user_id), "cookie.txt")


def save_user_cookie(user_id, data=None):
    """Upload one user's cookie.txt (data=bytes optional). Returns True on success."""
    col = _get_col()
    if col is None:
        return False
    try:
        path = _cookie_path(user_id)
        if data is None:
            if not os.path.isfile(path):
                return False
            with open(path, "rb") as f:
                data = f.read()
        if not data or len(data) > MAX_BYTES:
            return False
        sha = hashlib.sha1(data).hexdigest()
        if _seen.get(int(user_id)) == sha:
            return True
        col.update_one({"_id": int(user_id)},
                       {"$set": {"cookie": data, "sha1": sha, "updated_at": datetime.utcnow()}},
                       upsert=True)
        _seen[int(user_id)] = sha
        return True
    except Exception as e:
        logger.warning(f"[MONGO-COOKIES] save failed for {user_id}: {e}")
        return False


def delete_user_cookie(user_id):
    """Remove the user's cookie from MongoDB (used by /clean). Best effort."""
    try:
        _seen.pop(int(user_id), None)
        col = _get_col()
        if col is not None:
            col.delete_one({"_id": int(user_id)})
    except Exception as e:
        logger.warning(f"[MONGO-COOKIES] delete failed for {user_id}: {e}")


def restore_user_cookie(user_id):
    """Write the user's cookie.txt from MongoDB if the file is missing. Returns True if restored."""
    col = _get_col()
    if col is None:
        return False
    try:
        path = _cookie_path(user_id)
        if os.path.isfile(path):
            return False
        doc = col.find_one({"_id": int(user_id)})
        if not doc or not doc.get("cookie"):
            return False
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(bytes(doc["cookie"]))
        _seen[int(user_id)] = doc.get("sha1") or hashlib.sha1(bytes(doc["cookie"])).hexdigest()
        return True
    except Exception as e:
        logger.warning(f"[MONGO-COOKIES] restore failed for {user_id}: {e}")
        return False


def restore_all():
    col = _get_col()
    if col is None:
        return 0
    n = 0
    try:
        for doc in col.find({}, {"_id": 1}):
            if restore_user_cookie(doc["_id"]):
                n += 1
        logger.info(f"[MONGO-COOKIES] restored {n} cookie file(s) from MongoDB")
    except Exception as e:
        logger.warning(f"[MONGO-COOKIES] restore_all failed: {e}")
    return n


def _scan_once():
    if not os.path.isdir(USERS_DIR):
        return
    now = time.time()
    for name in os.listdir(USERS_DIR):
        if not name.lstrip("-").isdigit():
            continue
        path = _cookie_path(name)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) >= STABLE_AFTER:
                save_user_cookie(int(name))
        except Exception:
            continue


def _loop():
    while True:
        try:
            _scan_once()
        except Exception as e:
            logger.debug(f"[MONGO-COOKIES] scan error: {e}")
        time.sleep(SYNC_INTERVAL)


def start():
    """Call once at bot start: restore missing cookies, then keep syncing in the background."""
    global _started
    if _started:
        return
    _started = True
    try:
        restore_all()
    except Exception as e:
        logger.warning(f"[MONGO-COOKIES] startup restore error: {e}")
    threading.Thread(target=_loop, name="mongo-cookie-sync", daemon=True).start()
