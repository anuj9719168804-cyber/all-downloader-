"""
YouTube search, ported from fbot's ytsearch.py (sync Pyrogram version for all-downloader).

Commands / triggers:
  /search <query>   and   /yts <query>  -> paged YouTube results
  plain text "yt <query>", "youtube <query>", "search <query>", "<query> on yt", or any
  non-link text in a private chat (after the link handling found nothing) -> same search

Tapping a result number starts the normal download flow (video_url_extractor) for that video,
so the quality menu, ranges and subtitles work exactly as when a link is sent.

Note: the old /search (inline @vid helper) is replaced by this.
"""

import re
import threading
import uuid

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from HELPERS.app_instance import get_app
from HELPERS.logger import logger

try:
    import yt_dlp as _yt_dlp
except ImportError:  # pragma: no cover
    _yt_dlp = None

# ── Config ────────────────────────────────────────────────────────────────────
SEARCH_CHUNK_SIZE = 30   # results fetched per yt-dlp call (first page of results)
SEARCH_PAGE_SIZE = 10    # results shown per Telegram page

# ── State: cache_key -> {query, results, exhausted} ───────────────────────────
_SEARCH_CACHE = {}
_cache_lock = threading.Lock()

# Anything that looks like a link is never treated as a search query
_URL_HINT = re.compile(r"https?://|www\.|t\.me/|magnet:\?|\b[a-z0-9-]+\.[a-z]{2,}(?:/|\s|$)", re.IGNORECASE)

_YT_TRIGGER = r"(?:yt|yts|youtube)"
_YT_SEARCH_PATTERNS = [
    re.compile(rf"(?i)^\s*{_YT_TRIGGER}\s+search\s+(.+)$"),
    re.compile(rf"(?i)^\s*search\s+(.+?)\s+on\s+{_YT_TRIGGER}\s*$"),
    re.compile(rf"(?i)^\s*{_YT_TRIGGER}\s+(.+)$"),
    re.compile(rf"(?i)^\s*(.+?)\s+on\s+{_YT_TRIGGER}\s*$"),
    re.compile(r"(?i)^\s*search\s+(.+)$"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def _trim_cache(limit=500):
    with _cache_lock:
        while len(_SEARCH_CACHE) > limit:
            _SEARCH_CACHE.pop(next(iter(_SEARCH_CACHE)), None)


def _search_youtube_sync(query, chunk_size=SEARCH_CHUNK_SIZE):
    """Flat metadata-only YouTube search (no per-video fetch)."""
    if _yt_dlp is None:
        raise RuntimeError("yt-dlp not installed")
    with _yt_dlp.YoutubeDL({
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "default_search": "ytsearch",
    }) as ydl:
        info = ydl.extract_info(f"ytsearch{chunk_size}:{query}", download=False)
    entries = (info or {}).get("entries") or []
    results = []
    for entry in entries:
        if not entry or not entry.get("id"):
            continue
        dur = entry.get("duration")
        dur_str = ""
        if isinstance(dur, (int, float)) and dur > 0:
            m_, s = divmod(int(dur), 60)
            h, m_ = divmod(m_, 60)
            dur_str = f"{h}:{m_:02d}:{s:02d}" if h else f"{m_:02d}:{s:02d}"
        results.append({
            "id": entry["id"],
            "title": (entry.get("title") or "Untitled")[:70],
            "uploader": entry.get("uploader") or entry.get("channel") or "",
            "duration": dur_str,
        })
    return results


def _results_text(query, results, page, exhausted):
    start = page * SEARCH_PAGE_SIZE
    end = min(start + SEARCH_PAGE_SIZE, len(results))
    lines = [f"🔍 <b>YouTube Search:</b> <i>{query}</i>\n"]
    for i, r in enumerate(results[start:end], start=start + 1):
        meta = " — ".join(x for x in (r["uploader"], r["duration"]) if x)
        lines.append(f"{i}. {r['title']}" + (f"\n    <i>{meta}</i>" if meta else ""))
    if not (exhausted and end >= len(results)):
        lines.append("\n<i>Tap a number to download.</i>")
    return "\n".join(lines)


def _results_kb(results, page, exhausted, cache_key):
    start = page * SEARCH_PAGE_SIZE
    end = min(start + SEARCH_PAGE_SIZE, len(results))

    rows, row = [], []
    for abs_idx in range(start, end):
        row.append(InlineKeyboardButton(str(abs_idx + 1), callback_data=f"ytsr:{abs_idx}:{cache_key}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"ytsrpg:{page - 1}:{cache_key}"))
    nav.append(InlineKeyboardButton(f"Page {page + 1}", callback_data="ytsr:noop:x"))
    if not exhausted or end < len(results):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"ytsrpg:{page + 1}:{cache_key}"))
    rows.append(nav)
    return InlineKeyboardMarkup(rows)


def _is_private(message):
    chat_type = getattr(getattr(message, "chat", None), "type", "")
    return str(chat_type).lower().endswith("private")


# ── Core search flow ──────────────────────────────────────────────────────────
def _do_search(app, chat_id, query):
    if _yt_dlp is None:
        app.send_message(chat_id, "❌ <b>yt-dlp not installed.</b>", parse_mode=ParseMode.HTML)
        return

    try:
        status = app.send_message(chat_id, "🔍 <b>Searching YouTube...</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"[search] could not send status message: {e}")
        return

    try:
        results = _search_youtube_sync(query)
    except Exception as e:
        try:
            app.edit_message_text(chat_id, status.id,
                                  f"❌ <b>Search failed:</b>\n<code>{e}</code>", parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if not results:
        try:
            app.edit_message_text(chat_id, status.id,
                                  f"❌ <b>No results for:</b> <i>{query}</i>", parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    cache_key = uuid.uuid4().hex[:12]
    exhausted = len(results) < SEARCH_CHUNK_SIZE
    with _cache_lock:
        _SEARCH_CACHE[cache_key] = {"query": query, "results": results, "exhausted": exhausted}
    _trim_cache()

    try:
        app.edit_message_text(
            chat_id, status.id,
            _results_text(query, results, page=0, exhausted=exhausted),
            parse_mode=ParseMode.HTML,
            reply_markup=_results_kb(results, 0, exhausted, cache_key),
        )
    except Exception as e:
        logger.warning(f"[search] couldn't render results message: {e}")


def _extract_yt_query(text):
    stripped = text.strip()
    for pat in _YT_SEARCH_PATTERNS:
        m = pat.match(stripped)
        if m:
            q = m.group(1).strip()
            if q:
                return q
    return None


# ── Public entry points ───────────────────────────────────────────────────────
def search_command(app, message):
    """/search <query> and /yts <query> (called from url_distractor)."""
    parts = (getattr(message, "text", None) or "").split(None, 1)
    if len(parts) < 2 or not parts[1].strip():
        app.send_message(
            message.chat.id,
            "🔍 <b>Usage:</b> <code>/search &lt;song or video name&gt;</code>\n"
            "<i>e.g.</i> <code>/search Believer Imagine Dragons</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    _do_search(app, message.chat.id, parts[1].strip())


def try_plain_text_search(app, message):
    """Plain text that is not a link -> YouTube search. Returns True if a search was run.

    Only in private chats, and only for text that is not a command and not a link.
    """
    if _yt_dlp is None or not _is_private(message):
        return False
    text = (getattr(message, "text", None) or getattr(message, "caption", None) or "").strip()
    if not text or text.startswith("/"):
        return False
    if _URL_HINT.search(text):
        return False
    query = _extract_yt_query(text) or text
    if not (2 <= len(query) <= 120):
        return False
    _do_search(app, message.chat.id, query)
    return True


# ── Callbacks (registered on the app instance at import, same as the other modules) ──
app = get_app()


@app.on_callback_query(filters.regex(r"^ytsr:noop:"))
def cb_noop(client, callback_query):
    callback_query.answer()


@app.on_callback_query(filters.regex(r"^ytsr:(\d+):([a-f0-9]{12})$"))
def cb_select(client, callback_query):
    match = callback_query.matches[0]
    idx = int(match.group(1))
    cache_key = match.group(2)

    with _cache_lock:
        cached = _SEARCH_CACHE.get(cache_key)
    if not cached:
        return callback_query.answer("⌛ Search expired — please search again.", show_alert=True)
    results = cached["results"]
    if idx < 0 or idx >= len(results):
        return callback_query.answer("Invalid selection.", show_alert=True)

    # Telegram needs the callback answered within ~5s; the download flow can take longer.
    callback_query.answer("⏳ Loading qualities...")

    video_url = f"https://www.youtube.com/watch?v={results[idx]['id']}"
    try:
        from HELPERS.safe_messeger import fake_message_with_context
        from URL_PARSERS.video_extractor import video_url_extractor
        fm = fake_message_with_context(video_url, callback_query.from_user.id, context_message=callback_query.message)
        # The quality menu replies to fm.id and every menu button later reads
        # callback_query.message.reply_to_message (must be a REAL message holding the URL).
        # fake_message has id=0, which made the buttons fail with "Original message not found",
        # so post the link as a real message and reply to that one.
        try:
            sent_kwargs = {}
            thread_id = getattr(callback_query.message, "message_thread_id", None)
            if thread_id:
                sent_kwargs["message_thread_id"] = thread_id
            link_msg = client.send_message(callback_query.message.chat.id, video_url, **sent_kwargs)
            fm.id = link_msg.id
            fm._original_message = link_msg
        except Exception as send_err:
            logger.warning(f"[search] could not post link message, menu may not work: {send_err}")
        video_url_extractor(client, fm)
    except Exception as e:
        logger.error(f"[search] could not start download for {video_url}: {e}")


@app.on_callback_query(filters.regex(r"^ytsrpg:(\d+):([a-f0-9]{12})$"))
def cb_page(client, callback_query):
    match = callback_query.matches[0]
    page = int(match.group(1))
    cache_key = match.group(2)

    with _cache_lock:
        cached = _SEARCH_CACHE.get(cache_key)
    if not cached:
        return callback_query.answer("⌛ Search expired — please search again.", show_alert=True)

    results = cached["results"]
    query = cached["query"]
    exhausted = cached.get("exhausted", False)
    page_start = page * SEARCH_PAGE_SIZE

    if not exhausted and page_start >= len(results):
        callback_query.answer("⏳ Loading more results...")
        try:
            # Ask yt-dlp for a larger window (the same first N would only repeat old results).
            wanted = len(results) + SEARCH_CHUNK_SIZE
            more = _search_youtube_sync(query, chunk_size=wanted)
            existing_ids = {r["id"] for r in results}
            new_items = [r for r in more if r["id"] not in existing_ids]
            if not new_items or len(more) < wanted:
                exhausted = True
                cached["exhausted"] = True
            results.extend(new_items)
        except Exception as e:
            return callback_query.answer(f"Error: {e}", show_alert=True)
    else:
        callback_query.answer()

    try:
        callback_query.message.edit_text(
            _results_text(query, results, page=page, exhausted=exhausted),
            parse_mode=ParseMode.HTML,
            reply_markup=_results_kb(results, page, exhausted, cache_key),
        )
    except Exception as e:
        logger.warning(f"[search] pagination edit failed: {e}")
        try:
            callback_query.answer("Couldn't refresh — try again in a moment.", show_alert=True)
        except Exception:
            pass
