# -*- coding: utf-8 -*-
"""Generic web-page media detection (port of fbot's page_extract).

When yt-dlp cannot extract a link (unsupported site / plain web page with a player), the page is fetched and
scanned for HLS (.m3u8), DASH (.mpd), direct video/audio/file links and embedded players (<iframe>), and the
result is shown as numbered buttons. Picking one sends that media URL through the normal Always-Ask quality
menu / download pipeline (with the page as Referer). Embedded players are scanned one level deeper (max 2).

No browser sniffing (fbot's Chrome step) here; pages whose player only loads streams via JS after load are
not covered.
"""
import html
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

import requests
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyParameters

from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from HELPERS import page_media as pm

app = get_app()

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
MAX_PAGE_BYTES = 6 * 1024 * 1024
MAX_LINKS = 40
MAX_BUTTONS = 20
MAX_DEPTH = 2
STORE_TTL = 1800
PLACEHOLDER_MAX_BYTES = 64 * 1024     # "videos" smaller than this are teaser/placeholder clips

_STORE = {}
_REFERERS = {}                        # media url -> page url (hotlink-protected files need the page as Referer)
_lock = threading.Lock()


def get_referer(url):
    """Referer yt-dlp should use for this URL (the page it was found on, else the URL itself)."""
    return _REFERERS.get(url, url)


def _ssrf_ok(url):
    try:
        from URL_PARSERS.thumbnail_downloader import _validate_url_for_ssrf
        return bool(_validate_url_for_ssrf(url)[0])
    except Exception:
        return False


def _fetch_page(url):
    """-> (final_url, content_type, text) or raises RuntimeError with a short reason."""
    if not _ssrf_ok(url):
        raise RuntimeError("This address can't be opened.")
    try:
        r = requests.get(url, timeout=(10, 20), stream=True, allow_redirects=True,
                         headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                                  "Accept-Language": "en-US,en;q=0.8"})
    except requests.RequestException as e:
        raise RuntimeError(f"Couldn't open the page: {str(e)[:150]}")
    try:
        if r.status_code >= 400:
            raise RuntimeError(f"The page answered HTTP {r.status_code}.")
        final = r.url
        if not _ssrf_ok(final):
            raise RuntimeError("This address can't be opened.")
        ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype and not ("html" in ctype or "xml" in ctype or ctype.startswith("text/")):
            return final, ctype, ""
        buf = bytearray()
        for chunk in r.iter_content(64 * 1024):
            buf.extend(chunk)
            if len(buf) >= MAX_PAGE_BYTES:
                break
        enc = r.encoding or "utf-8"
        return final, ctype, bytes(buf).decode(enc, errors="replace")
    finally:
        r.close()


_VERIFY_KINDS = {"video", "audio", "file", "hls", "dash"}


def _check_one(item):
    """Does the link really return media? One small ranged GET (drops templates, 404 and HTML error pages)."""
    try:
        if not _ssrf_ok(item["url"]):
            return False
        r = requests.get(item["url"], timeout=(5, 8), stream=True, allow_redirects=True,
                         headers={"User-Agent": UA, "Range": "bytes=0-511",
                                  "Referer": item.get("referer", "")})
        try:
            if r.status_code not in (200, 206):
                return False
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            head = next(r.iter_content(512), b"") or b""
            cr = r.headers.get("Content-Range", "")
            if "/" in cr and cr.rsplit("/", 1)[1].isdigit():
                item["size"] = int(cr.rsplit("/", 1)[1])
            elif r.status_code == 200 and (r.headers.get("Content-Length") or "").isdigit():
                item["size"] = int(r.headers["Content-Length"])
        finally:
            r.close()
        if ctype.startswith("text/html") or ctype.startswith("application/json"):
            return False
        if item["kind"] == "hls":
            return head.lstrip().startswith(b"#EXTM3U")
        if item["kind"] == "dash":
            return b"<MPD" in head or b"<mpd" in head
        return len(head) > 0 and not head.lstrip().lower().startswith((b"<!doctype", b"<html"))
    except Exception:
        return False


def _verify(items):
    to_check = [i for i in items if i["kind"] in _VERIFY_KINDS][:40]
    if not to_check:
        return items
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(_check_one, to_check))
    ok = {id(i) for i, good in zip(to_check, results) if good}
    kept = [i for i in items if i["kind"] not in _VERIFY_KINDS or id(i) in ok]
    return pm.drop_tiny_videos(kept, PLACEHOLDER_MAX_BYTES)


def scan(url):
    """-> {"direct": url} for a file link, else {"page", "title", "links"}. Raises RuntimeError on fetch failure."""
    final, ctype, text = _fetch_page(url)
    if not text and ctype:
        return {"direct": final}
    items = pm.extract_candidates(text, final) if text else []
    for it in items:
        it["referer"] = final
    items = pm.main_only(_verify(items))
    return {"page": final, "title": pm.page_title(text),
            "links": pm.sort_candidates(items)[:MAX_LINKS]}


def _put(entry):
    now = time.time()
    with _lock:
        for k in [k for k, v in _STORE.items() if now - v["ts"] > STORE_TTL]:
            _STORE.pop(k, None)
        if len(_STORE) > 300:
            for k in list(_STORE)[:100]:
                _STORE.pop(k, None)
        token = uuid.uuid4().hex[:10]
        _STORE[token] = {**entry, "ts": now}
    return token


def _render(token, res, depth):
    links = res["links"]
    shown = links[:MAX_BUTTONS]
    host = html.escape(urlsplit(res["page"]).hostname or "")
    lines = [f"🔍 <b>Found {len(links)} media link(s)</b>", f"🌐 <code>{host}</code>"]
    if res.get("title"):
        lines.append(f"📝 {html.escape(res['title'])}")
    if depth:
        lines.append(f"↳ <i>embedded player, level {depth}</i>")
    lines.append("")
    for i, c in enumerate(shown, 1):
        lines.append(f"<b>{i}.</b> {html.escape(pm.display_label(c))} · "
                     f"<code>{html.escape(pm.short_name(c['url']))}</code>")
    if len(links) > len(shown):
        lines.append(f"<i>…and {len(links) - len(shown)} more (showing the best {len(shown)}).</i>")
    lines.append("\nTap a number to download it.")
    rows, row = [], []
    for i, c in enumerate(shown):
        row.append(InlineKeyboardButton(f"{i + 1}. {pm.display_label(c)[:22]}", callback_data=f"gpg|{token}|{i}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("❌ Close", callback_data=f"gpg|{token}|x")])
    return "\n".join(lines), InlineKeyboardMarkup(rows)


def _edit(chat_id, msg_id, text, markup=None):
    try:
        app.edit_message_text(chat_id, msg_id, text, parse_mode=enums.ParseMode.HTML, reply_markup=markup,
                              disable_web_page_preview=True)
    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" not in str(e):
            logger.warning(f"[generic-page] edit failed: {e}")


def _start_download(orig, media_url, page_url):
    """Run a found media link through the normal Always-Ask menu, with the page as Referer."""
    _REFERERS[media_url] = page_url
    if len(_REFERERS) > 500:
        for k in list(_REFERERS)[:100]:
            _REFERERS.pop(k, None)
    from DOWN_AND_UP.always_ask_menu import ask_quality_menu
    threading.Thread(target=ask_quality_menu, args=(app, orig, media_url, []), daemon=True).start()


def try_generic_scan(message, url, depth=0, status_msg_id=None):
    """Scan `url` and show what was found. Returns True if buttons (or a direct-file hand-off) were shown;
    False when nothing playable was found (the caller then shows its normal error)."""
    chat_id = message.chat.id
    try:
        res = scan(url)
    except Exception as e:
        logger.info(f"[generic-page] scan failed for {url}: {e}")
        return False
    if res.get("direct"):
        _start_download(message, res["direct"], url)
        return True
    if not res["links"]:
        return False
    token = _put({"uid": chat_id, "orig": message, "page": res["page"], "links": res["links"], "depth": depth})
    text, markup = _render(token, res, depth)
    if status_msg_id:
        _edit(chat_id, status_msg_id, text, markup)
    else:
        app.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML, reply_markup=markup,
                         reply_parameters=ReplyParameters(message_id=message.id),
                         disable_web_page_preview=True)
    return True


@app.on_callback_query(filters.regex(r"^gpg\|"))
def generic_pick(client, cb):
    parts = (cb.data or "").split("|")
    if len(parts) != 3:
        return cb.answer("Invalid choice.", show_alert=True)
    ent = _STORE.get(parts[1])
    if not ent or time.time() - ent["ts"] > STORE_TTL:
        _STORE.pop(parts[1], None)
        return cb.answer("This list has expired. Send the link again.", show_alert=True)
    if cb.from_user.id != ent["uid"]:
        return cb.answer("Only the person who sent this link can pick from this list.", show_alert=True)
    if cb.message is None:
        return cb.answer("Send the link again.", show_alert=True)
    chat_id, msg_id = cb.message.chat.id, cb.message.id
    if parts[2] == "x":
        _STORE.pop(parts[1], None)
        cb.answer()
        return _edit(chat_id, msg_id, "❌ Closed.")
    try:
        link = ent["links"][int(parts[2])]
    except (ValueError, IndexError):
        return cb.answer("This link is no longer in the list.", show_alert=True)
    cb.answer("Starting…")
    if link["kind"] == "page":
        if ent["depth"] >= MAX_DEPTH:
            return _edit(chat_id, msg_id, "⚠️ Too many nested players. Open that embed link in your browser instead.")
        _edit(chat_id, msg_id, "🔍 <b>Scanning the embedded player…</b>")
        if not try_generic_scan(ent["orig"], link["url"], ent["depth"] + 1, status_msg_id=msg_id):
            _edit(chat_id, msg_id, "❌ No playable media found in that player.")
        return
    _edit(chat_id, msg_id, "⬇️ Starting download…")
    _start_download(ent["orig"], link["url"], ent["page"])
