"""YouTube download fallback, used only after yt-dlp failed on a YouTube link.

yt-dlp stays the primary path (it lists qualities and downloads).  When it fails for a reason that is not a
permanent video error (private / removed / age-gated / members-only), this module asks a Piped API instance for
a ready progressive stream (video + audio in one file) and returns its URL.  The caller downloads that URL with
yt-dlp's generic extractor.

- Piped API base:  PIPED_API_BASE  (default https://pipedapi.kavin.rocks, set it to any Piped instance you trust)
- Title:           YouTube Data API via HELPERS.yt_api (needs YT_API_KEY), otherwise the title Piped returns.
- Everything fails soft: None is returned and the caller reports the original yt-dlp error.
"""
import logging
import os
import re
import urllib.parse

import requests

logger = logging.getLogger(__name__)

PIPED_API_BASE = (os.getenv("PIPED_API_BASE") or "https://pipedapi.kavin.rocks").rstrip("/")
TIMEOUT = float(os.getenv("YT_FALLBACK_TIMEOUT", "15") or 15)
MAX_HEIGHT = int(os.getenv("YT_FALLBACK_MAX_HEIGHT", "720") or 720)

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def video_id(url: str):
    """11-character YouTube id from youtu.be, watch?v=, shorts/, embed/ or live/ links."""
    try:
        p = urllib.parse.urlparse(url)
    except Exception:
        return None
    host = (p.netloc or "").lower()
    cand = None
    if "youtu.be" in host:
        cand = p.path.strip("/").split("/")[0]
    elif "youtube" in host:
        parts = [x for x in p.path.split("/") if x]
        if parts and parts[0] in ("shorts", "embed", "live", "v") and len(parts) > 1:
            cand = parts[1]
        else:
            cand = (urllib.parse.parse_qs(p.query).get("v") or [None])[0]
    return cand if cand and _ID_RE.match(cand) else None


def _title_from_data_api(vid: str):
    try:
        from HELPERS import yt_api
        if not yt_api.enabled():
            return None
        return (yt_api.video_details([vid]).get(vid) or {}).get("title")
    except Exception as e:
        logger.debug(f"[YT_FALLBACK] Data API title lookup failed: {e}")
        return None


def resolve_stream(url: str):
    """-> (direct_url, title) or None.  Picks the best progressive mp4-style stream up to MAX_HEIGHT."""
    vid = video_id(url)
    if not vid:
        return None
    try:
        r = requests.get(f"{PIPED_API_BASE}/streams/{vid}", timeout=TIMEOUT,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            logger.warning(f"[YT_FALLBACK] Piped API HTTP {r.status_code} for {vid}")
            return None
        data = r.json()
    except Exception as e:
        logger.warning(f"[YT_FALLBACK] Piped API error for {vid}: {e}")
        return None

    if data.get("error"):
        logger.warning(f"[YT_FALLBACK] Piped API says: {str(data.get('error'))[:200]}")
        return None

    # Progressive streams have audio and video together (videoOnly is False).
    candidates = []
    for s in data.get("videoStreams") or []:
        if s.get("videoOnly") or not s.get("url"):
            continue
        h = int(s.get("height") or 0)
        if h and h <= MAX_HEIGHT:
            candidates.append((h, s["url"]))
    if not candidates:
        logger.warning(f"[YT_FALLBACK] no progressive stream <= {MAX_HEIGHT}p for {vid}")
        return None
    candidates.sort(key=lambda t: t[0], reverse=True)
    best_url = candidates[0][1]

    title = _title_from_data_api(vid) or data.get("title")
    logger.info(f"[YT_FALLBACK] using Piped progressive stream {candidates[0][0]}p for {vid}")
    return best_url, title
