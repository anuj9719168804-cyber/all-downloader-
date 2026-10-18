# Bot identity helper
#
# Config.BOT_NAME must be the bot's Telegram USERNAME (letters, digits, "_", no spaces, no "@"),
# e.g. "AKDownloaderProBot" - NOT the display name. It is used in:
#   - the /search button   tg://msg?text=@vid &to=@<BOT_NAME>   (Telegram rejects the button if invalid)
#   - "@bot" mentions in captions, and /cmd@bot clean-up in groups
# If it is wrong (spaces, typo, display name) we take the real username from Telegram instead.

import re

_USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{3,31}$")


def is_valid_username(name) -> bool:
    return bool(name) and bool(_USERNAME_RE.match(str(name).lstrip("@").strip()))


def ensure_bot_username(app=None) -> str:
    """Return a valid bot username ('' if it cannot be found) and repair Config.BOT_NAME in memory."""
    from CONFIG.config import Config

    current = str(getattr(Config, "BOT_NAME", "") or "").lstrip("@").strip()
    if is_valid_username(current):
        return current

    if app is None:
        try:
            from HELPERS.app_instance import get_app
            app = get_app()
        except Exception:
            app = None

    username = ""
    if app is not None:
        try:
            me = getattr(app, "me", None) or app.get_me()
            username = (getattr(me, "username", "") or "").strip()
        except Exception:
            username = ""

    if is_valid_username(username):
        try:
            from HELPERS.logger import logger
            logger.warning(f"Config.BOT_NAME={current!r} is not a valid username - using @{username} from Telegram. "
                           f"Set BOT_NAME = {username!r} in CONFIG/config.py to silence this.")
        except Exception:
            pass
        Config.BOT_NAME = username
        return username
    return ""
