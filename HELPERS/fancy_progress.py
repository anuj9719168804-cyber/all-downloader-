# -*- coding: utf-8 -*-
"""fbot-style progress bar / progress box shared by every download & upload status message.

Looks like:

    📥 ꜰᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴠɪᴀ ᴍᴀɪɴ ᴇɴɢɪɴᴇ

    ╭━━━━❰Progress❱━➣
    ┣⪼ 🎬 File: name
    ┣⪼ [⬢⬢⬢⬢⬡⬡⬡⬡⬡⬡]
    ┣⪼ ✅ 41.2%
    ┣⪼ 💾 12.00 MB / 29.10 MB
    ┣⪼ ⚡ 2.4 MB/s
    ┣⪼ 🕐 Elapsed: 5s
    ┣⪼ ⏳ ETA: 7s
    ╰━━━━━━━━━━━━━━━➣
"""
import re
import html as _html

FILLED = "⬢"
EMPTY = "⬡"

_SMALLCAPS_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ",
)
_TAG_OR_MENTION_RE = re.compile(r"(<[^>]+>|@[A-Za-z][A-Za-z0-9_]{3,31})")


def smallcaps_html(text):
    """Small-caps plain text; HTML tags, <code>...</code> contents and @mentions stay untouched."""
    if not isinstance(text, str):
        return text
    out, in_code = [], 0
    for part in _TAG_OR_MENTION_RE.split(text):
        if part.startswith("<") and part.endswith(">"):
            low = part.lower()
            if low.startswith("<code"):
                in_code += 1
            elif low.startswith("</code"):
                in_code = max(0, in_code - 1)
            out.append(part)
        elif part.startswith("@"):
            out.append(part)
        else:
            out.append(part if in_code else part.translate(_SMALLCAPS_MAP))
    return "".join(out)


def progress_bar(pct, width=10):
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        pct = 0.0
    filled = max(0, min(width, int(width * pct / 100)))
    return FILLED * filled + EMPTY * (width - filled)


def human_size(n):
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def human_speed(n):
    n = float(n or 0)
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB/s"


def human_time(seconds):
    try:
        seconds = max(0, int(seconds))
    except (TypeError, ValueError):
        return "—"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def hms(seconds):
    try:
        seconds = max(0, int(round(float(seconds))))
    except (TypeError, ValueError):
        return str(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def build_info_header(msgs, total_process, number, title, video_id, duration_secs=None, time_fmt=None):
    """Header shown above the progress box (same as the upload message):

        📶 Total Progress / Video: 1 / 1
        📋 Video Info / Number / Title / ID / Video duration
    """
    esc = lambda v: _html.escape(str(v)) if v not in (None, "") else "—"
    head = (total_process or "").rstrip("\n") + "\n"
    head += f"<b>{msgs.DOWN_UP_VIDEO_INFO_MSG}</b>\n"
    head += f"<blockquote><b>{msgs.DOWN_UP_NUMBER_MSG}:</b> {esc(number)}</blockquote>\n"
    head += f"<blockquote><b>{msgs.DOWN_UP_TITLE_MSG}:</b> {esc(title)}</blockquote>\n"
    head += f"<blockquote><b>{msgs.DOWN_UP_ID_MSG}:</b> {esc(video_id)}</blockquote>\n"
    try:
        if duration_secs and time_fmt:
            head += f"\n<b>{msgs.DOWN_UP_VIDEO_DURATION_MSG}</b> <i>{time_fmt(float(duration_secs) * 1000)}</i>\n"
    except Exception:
        pass
    return head


def build_progress_text(downloading, name, percent, current, total, speed=None, eta=None,
                        elapsed=0, quality=None, duration=None, prefix="", connections=0):
    """Return the fbot-style progress box (HTML).

    downloading: True -> "Downloading", False -> "Uploading".
    prefix: optional text shown above the box (e.g. the playlist "video 2/5" line); not small-capsed.
    connections: kept for compatibility (the header and footer are always shown, like Fbot).
    """
    emoji = "📥" if downloading else "📤"
    verb = "Downloading" if downloading else "Uploading"
    word = "download" if downloading else "upload"
    try:
        current = float(current or 0)
        total = float(total or 0)
        speed = float(speed or 0)
    except (TypeError, ValueError):
        current, total, speed = 0.0, 0.0, 0.0
    if not speed and elapsed and elapsed > 0:
        speed = current / elapsed
    if eta is None and speed > 0 and total:
        eta = (total - current) / speed
    total_str = human_size(total) if total else "?"

    # Fbot style: the "Fast ... via Main Engine" header and the "Hyper ... connections" footer are always shown
    head = f"Fast {verb} via Main Engine"
    lines = [f"{emoji} <b>{head}</b>", "", "╭━━━━❰Progress❱━➣"]
    if name:
        lines.append(f"┣⪼ 🎬 File: <code>{_html.escape(str(name))}</code>")
    if duration:
        lines.append(f"┣⪼ ⏱ Duration: {hms(duration) if isinstance(duration, (int, float)) else _html.escape(str(duration))}")
    if quality:
        lines.append(f"┣⪼ 🎞 Quality: {_html.escape(str(quality))}")
    lines += [
        f"┣⪼ [{progress_bar(percent)}]",
        f"┣⪼ ✅ {float(percent or 0):.1f}%",
        f"┣⪼ 💾 {human_size(current)} / {total_str}",
        f"┣⪼ ⚡ {human_speed(speed)}",
        f"┣⪼ 🕐 Elapsed: {human_time(elapsed)}",
        f"┣⪼ ⏳ ETA: {human_time(eta) if eta is not None else '—'}",
        "╰━━━━━━━━━━━━━━━➣",
    ]
    lines += ["", f"⚡ Hyper {word} connections active"]
    text = smallcaps_html("\n".join(lines))
    return (f"{prefix}\n" if prefix else "") + text
