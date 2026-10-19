# -*- coding: utf-8 -*-
"""In-memory cache of the FULL yt-dlp info the quality menu already extracted.

fbot-style: the quality menu extracts the video once (that is the slow part: YouTube JS challenge etc.). When the
user taps a quality, the download re-uses that info instead of extracting again, so the progress bar starts moving
right away. Entries live 20 min, are per user + URL, and are only reused when the download goes out through the same
proxy (YouTube media URLs are bound to the IP that extracted them).
"""
import copy
import threading
import time

_TTL = 20 * 60
_MAX = 60
_lock = threading.Lock()
_store = {}


def _key(user_id, url):
    try:
        from DATABASE.cache_db import normalize_url_for_cache
        u = normalize_url_for_cache(url)
    except Exception:
        u = url
    return (user_id, u)


def _usable(info):
    return (isinstance(info, dict) and not info.get("error") and not info.get("entries")
            and bool(info.get("formats")) and not info.get("is_live"))


def put(user_id, url, info, proxy=None):
    try:
        if not _usable(info):
            return
        snap = copy.deepcopy(info)
        now = time.time()
        with _lock:
            for k in [k for k, v in _store.items() if now - v[0] > _TTL]:
                _store.pop(k, None)
            while len(_store) >= _MAX:
                _store.pop(min(_store, key=lambda k: _store[k][0]), None)
            _store[_key(user_id, url)] = (now, snap, proxy or None)
    except Exception:
        pass


def get(user_id, url, proxy=None):
    try:
        with _lock:
            hit = _store.get(_key(user_id, url))
        if not hit:
            return None
        ts, info, cached_proxy = hit
        if time.time() - ts > _TTL or (cached_proxy or None) != (proxy or None):
            return None
        return copy.deepcopy(info)
    except Exception:
        return None
