"""Colored + emoji buttons for the whole bot (same look as fbot).

Telegram (Bot API 9.4+) can paint inline / reply-keyboard buttons blue ("primary"), green
("success") or red ("danger").  Instead of editing the ~300 places that build buttons, install()
wraps InlineKeyboardButton / KeyboardButton once at start-up and picks a color from the label:

    red    -> Close / Cancel / Back / Delete / Off ... (❌ 🔚 🔙 🗑 ⛔ 🚫)
    green  -> Next / Prev / Done / active toggles      (✅ ▶️ ◀️ ➡️ 🟢)
    blue   -> everything else

Labels that have no emoji at all get a fitting one in front (Close -> ❌ Close, Join Channel -> 📢 ...).
Labels that already start with an emoji are never touched.

Safe by design: if the installed Pyrogram fork has no ButtonStyle / `style` argument (older builds)
install() does nothing, and a button that rejects `style` is rebuilt without it. It can never break
the bot.  Set BUTTON_STYLE=off in the environment to disable it.
"""
import inspect
import logging
import os
import re

logger = logging.getLogger(__name__)

_installed = False

# --- emoji detection -------------------------------------------------------------------------
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF←-⇿⌀-⏿①-⓿■-➿⤀-⥿"
    "⬀-⯿〰〽㊗㊙©®‼⁉™ℹ️]"
)

_DANGER_EMOJI = set("❌✖⛔🚫🗑🔚🔙✘")
_SUCCESS_EMOJI = set("✅▶◀➡⬅⏭⏮🟢⏩⏪")

_DANGER_WORDS = re.compile(r"\b(close|cancel|back|delete|remove|clear|stop|off|exit|abort|disable[d]?)\b", re.I)
_SUCCESS_WORDS = re.compile(r"\b(next|prev|previous|done|confirm|ok|yes|on|enable[d]?|apply|save)\b", re.I)

# keyword -> emoji, used ONLY when the label has no emoji at all
_EMOJI_FOR_WORD = [
    (re.compile(r"\b(close|cancel)\b", re.I), "❌"),
    (re.compile(r"\bback\b", re.I), "🔙"),
    (re.compile(r"\bnext\b", re.I), "▶️"),
    (re.compile(r"\b(prev|previous)\b", re.I), "◀️"),
    (re.compile(r"\bdownload\b", re.I), "📥"),
    (re.compile(r"\bjoin\b", re.I), "📢"),
    (re.compile(r"\bbest\b", re.I), "⭐"),
    (re.compile(r"\b(delete|remove|clear)\b", re.I), "🗑"),
    (re.compile(r"\b(refresh|reload|retry)\b", re.I), "🔄"),
    (re.compile(r"\b(settings?|options?)\b", re.I), "⚙️"),
    (re.compile(r"\bhelp\b", re.I), "❓"),
    (re.compile(r"\bsearch\b", re.I), "🔍"),
    (re.compile(r"\b(open|link|stream)\b", re.I), "🔗"),
    (re.compile(r"\b(yes|ok|done|confirm|apply|save)\b", re.I), "✅"),
    (re.compile(r"\bno\b", re.I), "❌"),
]


def _has_emoji(text: str) -> bool:
    return bool(_EMOJI_RE.search(text or ""))


def add_emoji(text):
    """Prefix a fitting emoji when the label has none. Returns the text unchanged otherwise."""
    if not isinstance(text, str) or not text.strip() or _has_emoji(text) or len(text) > 40:
        return text
    if text.lstrip().startswith("/"):          # reply-keyboard command buttons must stay "/command"
        return text
    for rx, emoji in _EMOJI_FOR_WORD:
        if rx.search(text):
            return f"{emoji} {text}"
    return text


def pick_style(text, ButtonStyle):
    """Return the ButtonStyle member for a label (red / green / blue)."""
    text = text if isinstance(text, str) else ""
    # explicit emoji first
    first = next((c for c in text if c in _DANGER_EMOJI or c in _SUCCESS_EMOJI), None)
    if first in _DANGER_EMOJI:
        return ButtonStyle.DANGER
    if first in _SUCCESS_EMOJI:
        return getattr(ButtonStyle, "SUCCESS", ButtonStyle.PRIMARY)
    if _DANGER_WORDS.search(text):
        return ButtonStyle.DANGER
    if _SUCCESS_WORDS.search(text):
        return getattr(ButtonStyle, "SUCCESS", ButtonStyle.PRIMARY)
    return ButtonStyle.PRIMARY


def _wrap(cls, ButtonStyle):
    """Wrap cls.__init__ so a style (and emoji) is added when the caller gave none."""
    try:
        params = inspect.signature(cls.__init__).parameters
    except (TypeError, ValueError):
        return False
    if "style" not in params:
        return False
    orig = cls.__init__
    if getattr(orig, "_button_style_wrapped", False):
        return True

    def __init__(self, *args, **kwargs):
        args = list(args)
        try:
            if args and isinstance(args[0], str):
                args[0] = add_emoji(args[0])
            elif isinstance(kwargs.get("text"), str):
                kwargs["text"] = add_emoji(kwargs["text"])
            if kwargs.get("style") is None:
                label = args[0] if args and isinstance(args[0], str) else kwargs.get("text", "")
                kwargs["style"] = pick_style(label, ButtonStyle)
        except Exception:
            pass
        try:
            orig(self, *args, **kwargs)
        except TypeError:
            kwargs.pop("style", None)          # this build rejects `style`: plain button instead
            orig(self, *args, **kwargs)

    __init__._button_style_wrapped = True
    __init__.__wrapped__ = orig
    cls.__init__ = __init__
    return True


def install() -> bool:
    """Turn on colored buttons. Returns True when at least the inline buttons are styled."""
    global _installed
    if _installed:
        return True
    if os.getenv("BUTTON_STYLE", "on").strip().lower() in ("0", "off", "false", "no"):
        logger.info("[button_style] disabled by BUTTON_STYLE env")
        return False
    try:
        from pyrogram.enums import ButtonStyle
        from pyrogram.types import InlineKeyboardButton, KeyboardButton
    except Exception as e:                      # old pyrogram: no ButtonStyle -> nothing to do
        logger.info(f"[button_style] colored buttons not supported by this Pyrogram build ({e})")
        return False
    inline_ok = _wrap(InlineKeyboardButton, ButtonStyle)
    reply_ok = _wrap(KeyboardButton, ButtonStyle)
    _installed = inline_ok
    logger.info(f"[button_style] colored buttons: inline={inline_ok}, reply={reply_ok}")
    return inline_ok


def style_reply_rows(rows):
    """Turn rows of plain strings into styled KeyboardButtons (falls back to the plain strings)."""
    try:
        from pyrogram.enums import ButtonStyle
        from pyrogram.types import KeyboardButton
        if "style" not in inspect.signature(KeyboardButton.__init__).parameters:
            return rows
        return [[KeyboardButton(text=b, style=pick_style(b, ButtonStyle)) if isinstance(b, str) else b
                 for b in row] for row in rows]
    except Exception:
        return rows
