"""Telegram bot command menu (the list shown when the user taps the "Menu" button).

set_bot_menu(app) registers these with Telegram's setMyCommands on every start, so the menu always
matches the commands the bot actually handles. Each name must be lowercase letters/digits/underscores."""
import logging

from pyrogram.types import BotCommand

logger = logging.getLogger(__name__)

BOT_MENU_COMMANDS = [
    ("start", "🚀 Start the bot"),
    ("lang", "🌐 Change language"),
    ("help", "❓ Show help instructions"),
    ("keyboard", "⌨️ Show keyboard options"),
    ("settings", "⚙️ Show all bot commands"),
    ("add_bot_to_group", "➕ Add bot to a group"),
    ("clean", "🧹 Delete cookies and broken downloads"),
    ("vid", "🎬 Download video from link"),
    ("img", "🖼 Download image from link"),
    ("audio", "🎧 Extract audio from link"),
    ("search", "🔍 Find videos directly in bot"),
    ("cookie", "🍪 Download cookie from web"),
    ("cookies_from_browser", "🌎 Get cookies from browser"),
    ("playlist", "📃 Download playlists"),
    ("format", "🎞 Change quality and format options"),
    ("list", "📋 Show available formats for URL"),
    ("mediainfo", "📊 Enable or disable media info"),
    ("split", "✂️ Change split video part size"),
    ("subs", "💬 Enable or disable subtitle embedding"),
    ("link", "🔗 Get direct stream links"),
    ("proxy", "🛡 Enable or disable proxy"),
    ("check_cookie", "✅ Check and validate cookie"),
    ("save_as_cookie", "💾 Save text as cookie"),
    ("tags", "#️⃣ Get all your tags"),
    ("usage", "📈 Get all your logs"),
    ("nsfw", "🔞 Enable or disable NSFW blur"),
    ("args", "🧰 Change yt-dlp hook arguments"),
]


def set_bot_menu(app) -> None:
    """Publish the command menu to Telegram. Never raises: a failed menu update must not stop the bot."""
    try:
        app.set_bot_commands([BotCommand(cmd, desc[:256]) for cmd, desc in BOT_MENU_COMMANDS])
        logger.info(f"Bot command menu set ({len(BOT_MENU_COMMANDS)} commands).")
    except Exception as e:
        logger.warning(f"Could not set bot command menu: {e}")
