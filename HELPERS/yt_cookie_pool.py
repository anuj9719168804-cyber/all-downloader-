"""YouTube cookie pool (ported from ak-yt's yt_auth.py).

Several Netscape cookie files (one per YouTube account) live in one folder. A download takes the next account
that is not cooling down. When YouTube answers with a bot-check ("Sign in to confirm you're not a bot", 403 on
the account) that account is put on a cooldown and the retry uses another one.

  * YT_COOKIE_POOL_DIR            folder with *.txt cookie files (default: yt_cookies_pool next to the project)
  * YT_COOKIE_COOLDOWN_MINUTES    cooldown for an account that hit a bot-check (default 60)
  * Rate limits (HTTP 429) are per server IP, not per account, so they do NOT rotate accounts.

Pure stdlib. Fails soft: with no pool folder or no valid file, acquire() returns None and the caller keeps its
normal cookie handling.
"""
import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parents[1]
POOL_DIR = Path(os.getenv("YT_COOKIE_POOL_DIR", "") or (_BASE_DIR / "yt_cookies_pool"))
COOLDOWN_MIN = max(1, int(os.getenv("YT_COOKIE_COOLDOWN_MINUTES", "60") or 60))
MAX_FILE_BYTES = 5 * 1024 * 1024

_BOT_MARKERS = (
    "sign in to confirm",
    "not a bot",
    "confirm you're not a bot",
    "http error 403",
    "403: forbidden",
    "login required",
)

_lock = threading.Lock()
_rr = 0  # round-robin cursor
_STATE = POOL_DIR / "pool_state.json"


def is_bot_error(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in _BOT_MARKERS)


def _valid(p: Path) -> bool:
    try:
        if not p.is_file() or p.stat().st_size == 0 or p.stat().st_size > MAX_FILE_BYTES:
            return False
        head = p.read_text(encoding="utf-8", errors="ignore")[:4000]
        return "youtube" in head.lower() and ("# netscape" in head.lower() or "\t" in head)
    except OSError:
        return False


def list_accounts() -> list:
    if not POOL_DIR.is_dir():
        return []
    return sorted(p for p in POOL_DIR.glob("*.txt") if _valid(p))


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    try:
        POOL_DIR.mkdir(parents=True, exist_ok=True)
        _STATE.write_text(json.dumps(state), encoding="utf-8")
    except OSError as e:
        logger.warning(f"[YT_POOL] could not save state: {e}")


def is_cooling(path) -> bool:
    st = _load_state().get(Path(path).name, 0)
    return time.time() < float(st or 0)


def acquire(exclude=()) -> str | None:
    """Next usable account (round-robin, skipping cooling and excluded ones). None if the pool is empty/exhausted."""
    global _rr
    accounts = list_accounts()
    if not accounts:
        return None
    excl = {str(Path(x).name) for x in exclude if x}
    with _lock:
        n = len(accounts)
        for i in range(n):
            p = accounts[(_rr + i) % n]
            if p.name in excl or is_cooling(p):
                continue
            _rr = (_rr + i + 1) % n
            return str(p)
    logger.warning("[YT_POOL] every account is cooling down or excluded")
    return None


def mark_bot_check(path, minutes: float | None = None) -> None:
    """Put an account on cooldown after a bot-check. Only files that belong to the pool are touched."""
    if not path:
        return
    p = Path(path)
    if p.parent.resolve() != POOL_DIR.resolve():
        return
    with _lock:
        state = _load_state()
        state[p.name] = time.time() + float(minutes or COOLDOWN_MIN) * 60
        _save_state(state)
    logger.warning(f"[YT_POOL] {p.name} hit a bot-check, cooling down for {minutes or COOLDOWN_MIN} min")


def in_pool(path) -> bool:
    if not path:
        return False
    try:
        return Path(path).resolve().parent == POOL_DIR.resolve()
    except OSError:
        return False


def status() -> list:
    state = _load_state()
    now = time.time()
    out = []
    for p in list_accounts():
        until = float(state.get(p.name, 0) or 0)
        out.append({"name": p.name, "cooling": now < until,
                    "minutes_left": max(0, int((until - now) / 60)) if now < until else 0})
    return out
