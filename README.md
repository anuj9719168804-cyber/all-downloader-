# 🎬 Universal Video Downloader ❤️

A Telegram bot that downloads videos, audio, and images from hundreds of websites and sends them straight to the chat. It is built on **Pyrogram (kurigram)** and **yt-dlp**, with **gallery-dl** for image galleries, **FFmpeg** for processing, and a **FastAPI web dashboard** for administration. The whole stack runs with Docker Compose.

> ⚠️ **Responsible use:** Only download content you have the right to download. Respect copyright, the terms of service of each platform, and the laws of your country. DRM-protected services (Netflix, Disney+, and similar) are blocked by design.

---

## Table of Contents

1. [Features](#-features)
2. [Supported Sources](#-supported-sources)
3. [Commands Reference](#-commands-reference)
4. [Quick Start (Docker)](#-quick-start-docker)
5. [Manual Installation (without Docker)](#-manual-installation-without-docker)
6. [Configuration](#-configuration)
7. [Cookies & Private Content](#-cookies--private-content)
8. [Proxy & Network](#-proxy--network)
9. [Web Dashboard](#-web-dashboard)
10. [Limits & Restrictions](#-limits--restrictions)
11. [Languages & Messages](#-languages--messages)
12. [Maintenance Scripts](#-maintenance-scripts)
13. [Project Structure](#-project-structure)
14. [Troubleshooting](#-troubleshooting)
15. [Security](#-security)
16. [Contributing](#-contributing)
17. [License](#-license)

---

## ✨ Features

### 📥 Downloading
- **Send any link, get the file.** Paste a URL and the bot detects the source, picks the right engine, and uploads the result.
- **Automatic engine routing.** Videos go through **yt-dlp**; image posts and galleries go through **gallery-dl**. Some domains are routed straight to gallery-dl.
- **Audio extraction** with `/audio URL`.
- **Direct stream links** with `/link`, so you can open a file in a player without downloading it through Telegram.
- **Thumbnail download** for videos when the source provides one.
- **Multiple URLs at once.** In quality-selection mode (`/format` → ask) you can send up to **10 URLs** in one message, one per line or space-separated.
- **Live streams.** Live recordings can be downloaded in chunks by size and sent as they are produced. Optional download "from start" is available through `/args`.

### 📋 Playlists & Ranges
- Download a **range** from a playlist or channel with a suffix on the URL: `URL*1*5` (first 5), `URL*-1*-5` (last 5), `URL*3*` (from 3 to the end).
- Or use the `/vid` shortcut: `/vid 3-7 URL` and `/vid -3-7 URL`.
- Bare YouTube playlist links are supported (up to a configurable maximum).
- `/playlist` shows how playlists work.

### 🖼 Images & Galleries
- `/img URL` downloads all images from a post or profile.
- Ranges work too: `/img 11-20 URL` and `/img 11- URL` (from item 11 to the end).
- A configurable cap on total files per request (see [Limits](#-limits--restrictions)).

### 🎛 Quality & Format Control
- `/format` opens a menu for resolution, codec, and container:
  - **Resolution:** 144p up to 4320p (8K), or `best`, `ask`, or a specific format ID (`id 134`).
  - **Codecs:** AVC / H.264, AV1, VP9.
  - **Containers:** MP4 or MKV.
  - **HDR:** on/off.
- `ask` mode shows a per-video menu before downloading so you can choose the format each time.
- `/list URL` shows every format the source offers.
- `/split` sets the maximum part size for large files (100 MB to 2 GB). Files bigger than the limit are cut into parts with FFmpeg.

### 💬 Subtitles & Dubs
- `/subs off|ru|en|auto`: embed subtitles in the video. The `auto` option uses automatically generated captions.
- Paid option: burning (hard-coding) subtitles into MP4 is charged in Telegram Stars; MKV embedding is free.
- `/dubs off|ru|en`: choose an audio/dub track when the source provides several.
- **📝 sub only** button: download only the subtitle file.

### 🏷 Captions & Tags
- Every upload gets a caption with the source link and the bot's `@username`.
- Add tags to a link (`URL #tag1#tag2`); tags appear in the caption.
- `/tags` lists all tags you have used.
- Reply to a video with text to change its caption.

### 🔗 Action Buttons ("Always Ask" menu)
When enabled, the bot shows buttons after a link is detected:
- Pick a quality or codec.
- **Embed** a player link (for supported sites).
- **VLC** (Android and iOS): copy a stream URL and open it in VLC.
- **Browser**: open the source page.
- **Try gallery-dl** when yt-dlp fails on an image post.
- **Next / Prev** to page through long format lists.
- **Close**.

### ⌨️ Keyboard & Menus
- Optional reply keyboard with shortcuts. Layouts: `off`, `1x3`, `2x3`, `full` (`/keyboard`).
- `/settings` opens a menu with every setting in one place.
- `/start`, `/help` and inline help panels for each command.
- Bot command menu is published to Telegram on startup.

### 🔍 Search
- `/search` gives you an inline search through **@vid** so you can find videos without leaving the chat.

### 🔞 NSFW Handling
- Content from adult sites or with adult keywords is detected using curated domain and keyword lists.
- `/nsfw on|off` blurs such media when it is sent.
- Some NSFW features are **paid** (1 ⭐ Telegram Star per use, as listed in the bot's help).

### 🍪 Cookies & Private Videos
- Upload a `*.txt` cookie file (Netscape format) for age-restricted or private content.
- `/cookie [service]` downloads cookies from a configured URL for YouTube, TikTok, X/Twitter, Instagram, Facebook, VK, or a custom source. `/cookie youtube 1` selects a source by index.
- `/cookies_from_browser` extracts cookies from a browser.
- `/check_cookie` validates a cookie file (YouTube cookies are tested against a known video).
- `/save_as_cookie` saves pasted text as your cookie file.
- YouTube supports multiple cookie sources with round-robin or random selection, and automatic fallback when one stops working.

### 🌐 Proxy
- `/proxy on|off` enables proxies for all downloads, or only automatically when YouTube blocks a request (AUTO mode).
- Up to two proxies can be configured. Selection is round-robin or random.
- Optional country selection and free-proxy sources.

### 📊 Usage & Logs
- `/usage` shows your download history.
- `/mediainfo on|off` toggles sending technical media information (codec, bitrate, streams) with each file.
- `/log` (admin) gets a user's logs.

### 🧹 Cleaning
- `/clean` deletes your downloaded media files.
- `/clean all` deletes everything the bot stores for you.
- `/clean cookies|logs|tags|format|split|mediainfo|sub|keyboard` clears individual settings or data.

### ⚙️ Arguments (`/args`)
Advanced yt-dlp hook options are set through a grouped menu, for example live-stream start behaviour.

### 👥 Groups
- Works in groups as well as in private chats.
- Only groups listed in `ALLOWED_GROUP` are served.
- Commands can be addressed to the bot with `/command@BotName`, so several bots can share one group.
- Group admins can be granted command access through `ADMIN_GROUP`.

### 🛡 Protection & Stability
- **Rate limiting** per user and per command (`HELPERS/rate_limiter.py`, `HELPERS/command_limiter.py`).
- **Anti-bot protection** with temporary bans for abusive patterns.
- **Channel guard**: requires users to join a subscription channel, and watches the channel's admin log.
- **Blocked domains**: DRM services, messengers, banking, and other non-media sites are refused.
- **Upload guard**: limits concurrent uploads and detects stalled ones.
- **Admin block/unblock/ignore/ban commands** for users.
- **FloodWait handling**: on startup and during operation the bot waits out Telegram flood limits instead of crashing.
- **Graceful shutdown** on SIGINT/SIGTERM, closing HTTP sessions and database connections.

### 🧰 Infrastructure
- **Docker Compose** stack with bot, dashboard, PO-token provider, Cloudflare WARP tunnel, and an optional cookie web server.
- **YouTube PO token provider** (`bgutil-ytdlp-pot-provider`) to reduce YouTube bot-detection errors.
- **Node.js 22** runtime for yt-dlp's YouTube challenge solver (EJS), so 720p+ and 4K formats are not dropped.
- **Persistent cookies in MongoDB** (`HELPERS/mongo_cookies.py`), so cookies survive redeploys.
- **Optional Firebase** for the video/playlist/image cache, with automatic cache reload on a schedule (`USE_FIREBASE`, `RELOAD_CACHE_EVERY`).
- **Cache** of previously downloaded media, so repeated links can be answered instantly.
- **Systemd unit files** for running without Docker (`_etc/systemd/`).
- **Backup and restore** scripts.
- **Health endpoint** at `/health`.

---

## 🌍 Supported Sources

The bot uses yt-dlp's extractor list, so any site yt-dlp supports works. The file `TXT/supported_sites.txt` contains about 1,480 site entries. Popular examples include:

| Category | Examples |
|---|---|
| Video platforms | YouTube (videos, Shorts, playlists), Vimeo, Dailymotion, Rumble, BitChute |
| Social | TikTok, Instagram (posts, reels, stories), Facebook, X / Twitter, Reddit, Bluesky, VK, Threads |
| Music & audio | SoundCloud, Bandcamp, Audius, Mixcloud, Podcast platforms |
| News & TV | BBC, CNN, NBC, ARD, ZDF, Arte, and many regional broadcasters |
| Images / galleries | Instagram, Pinterest, Reddit, and any site supported by gallery-dl |
| Other | Bilibili, Niconico, and many more |

Some sites need cookies or a proxy to work (for example YouTube age-restricted videos or Instagram stories). See [Cookies](#-cookies--private-content).

---

## 📖 Commands Reference

Commands work in private chats and, where enabled, in allowed groups.

### Basic
| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/help` | Show the help message |
| `/lang` | Change language (the bot currently ships English messages) |
| `/keyboard off\|1x3\|2x3\|full` | Choose the reply keyboard layout |
| `/settings` | Open the all-in-one settings menu |
| `/usage` | Your download history |
| `/search` | Inline search through @vid |

### Downloading
| Command | Description |
|---|---|
| `URL` | Download a video, image, or gallery from any link |
| `/vid [FROM-TO] URL` | Download a video, optionally a playlist range |
| `/audio [FROM-TO] URL` | Extract audio only |
| `/img [FROM-TO] URL` | Download images from a page or profile |
| `/link [quality] URL` | Get direct stream links (`144`–`4320`, `720p`, `1080p`, `4k`, `8k`, or best) |
| `/list URL` | List all available formats for a URL |
| `/playlist` | Explain how to download playlists |

### Quality & Output
| Command | Description |
|---|---|
| `/format [quality]` | Set resolution: `144`–`4320`, `720p`, `1080p`, `4k`, `8k`, `best`, `ask`, or `id 134` |
| `/split 100mb-2000mb` | Set the maximum part size (100 MB to 2 GB) |
| `/subs off\|ru\|en\|auto` | Subtitle embedding |
| `/dubs off\|ru\|en` | Dub / audio track selection |
| `/mediainfo on\|off` | Send media information with each file |
| `/args` | Advanced yt-dlp hook options (grouped menu) |

### Cookies
| Command | Description |
|---|---|
| `/cookie [service] [index]` | Download cookies from a configured source |
| `/cookies_from_browser` | Extract cookies from a browser |
| `/check_cookie` | Validate your cookie file |
| `/save_as_cookie` | Save pasted text as cookie file (or upload a `.txt`) |

### Proxy, Tags, NSFW, Cleaning
| Command | Description |
|---|---|
| `/proxy on\|off` | Enable or disable proxy for downloads |
| `/tags` | Show all your tags |
| `/nsfw on\|off` | Blur NSFW media on or off |
| `/clean [all\|cookies\|logs\|tags\|format\|split\|mediainfo\|sub\|keyboard]` | Delete media, data, or settings |

### Admin
| Command | Description |
|---|---|
| `/broadcast` | Send a message to all users |
| `/block_user`, `/unblock_user` | Block or unblock a user |
| `/ignore_user`, `/unignore_user` | Silently ignore or restore a user |
| `/ban_time` | Set a ban duration |
| `/log` | Get a user's logs |
| `/all` | List or inspect users |
| `/run_time` | Show how long the bot has been running |
| `/reload_cache`, `/auto_cache` | Reload the cache manually or toggle automatic reloads |
| `/uncache` | Remove an item from the cache |

### Inline & Shortcut Syntax

```text
https://example.com/video                 → download
https://example.com/video #funny #cats    → download with tags
https://youtube.com/playlist?list=...*1*5 → first 5 videos
https://youtube.com/playlist?list=...*-1*-5 → last 5 videos
/vid 3-7 https://...                      → same as URL*3*7
/img 11- https://instagram.com/user       → from item 11 to the end
/format 1080p                             → set quality
/format id 134                            → use a specific format ID
```

---

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker and Docker Compose v2
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Telegram API ID and API hash from [my.telegram.org](https://my.telegram.org)
- Your own Telegram numeric user ID (for admin rights)

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/all-downloader.git
cd all-downloader
```

### 2. Create the `.env` file
Docker Compose reads `.env` as environment variables for every service. Example:

```env
TZ=Europe/Moscow
DASHBOARD_PORT=5555
```

Put your bot settings in `CONFIG/config.py` (see [Configuration](#-configuration)).

### 3. Start the stack
```bash
docker compose up -d --build
```

This starts:

| Service | Container | Purpose |
|---|---|---|
| `bot` | `tg-ytdlp-bot` | The Telegram bot (`magic.py`) |
| `dashboard` | `tg-ytdlp-dashboard` | Web admin panel on port **5555** |
| `bgutil-provider` | `tg-ytdlp-bgutil-provider` | YouTube PO token provider |
| `warp` | `tg-ytdlp-warp` | Cloudflare WARP WireGuard tunnel; the bot's network runs through it |
| `configuration-webserver` | `tg-ytdlp-configuration-webserver` | *Optional* Caddy server that hosts cookie files |

### 4. (Optional) Start the cookie web server
```bash
docker compose --profile configuration-webserver up -d
```
Put your cookie files in `docker/configuration-webserver/site/cookies/`. The bot reads them at `http://localhost/cookies/<file>.txt`.

### 5. Check the logs
```bash
docker compose logs -f bot
```

### Updating
```bash
docker compose down
git pull
docker compose up -d --build
```
Or use `UPDATE.sh` / `scripts/UPDATE_DOCKER.sh` for guided updates.

---

## 🛠 Manual Installation (without Docker)

### System requirements
- **Python 3.11+**
- **FFmpeg** and **MediaInfo**
- **Node.js 22+** (for yt-dlp's YouTube solver)
- **Git**
- Optional: `aria2`, `rsync`, and fonts for non-Latin subtitles (Noto, Amiri, CJK, emoji)

### Ubuntu / Debian example
```bash
sudo apt update
sudo apt install -y python3 python3-venv git ffmpeg mediainfo aria2 rsync fonts-noto-core fonts-noto-color-emoji

# Node.js 22 (NodeSource)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

git clone https://github.com/<your-username>/all-downloader.git
cd all-downloader
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Run the bot
```bash
python magic.py
```

### Run the dashboard
```bash
python -m uvicorn web.dashboard_app:app --host 0.0.0.0 --port 5555
```

### Run as a service (systemd)
Unit files are in `_etc/systemd/system/`:
- `tg-ytdlp-bot.service`: the bot
- `tg-ytdlp-dashboard.service`: the dashboard

```bash
sudo cp _etc/systemd/system/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tg-ytdlp-bot tg-ytdlp-dashboard
```
Edit the `WorkingDirectory` and `ExecStart` paths in the files to match your install location first.

---

## ⚙️ Configuration

All main settings are in **`CONFIG/config.py`** (class `Config`). Limits are in **`CONFIG/limits.py`**, and command names in **`CONFIG/commands.py`**. Domain lists are in **`CONFIG/domains.py`**.

### Required settings

| Setting | Meaning |
|---|---|
| `BOT_TOKEN` | Token from @BotFather |
| `API_ID` / `API_HASH` | Telegram API credentials |
| `ADMIN` | List of admin user IDs |
| `BOT_NAME` | Display name of the bot |
| `BOT_MENTION` | Bot username (without `@`) used in captions |
| `ADMIN_USERNAME` | Contact shown in help and credits |

### Channels & logs

| Setting | Meaning |
|---|---|
| `LOGS_ID`, `LOGS_VIDEO_ID`, `LOGS_NSFW_ID`, `LOGS_IMG_ID`, `LOGS_PAID_ID` | Channels for log messages (can all be the same channel) |
| `LOG_EXCEPTION` | Channel for exception reports |
| `SUBSCRIBE_CHANNEL` / `SUBSCRIBE_CHANNEL_URL` | Channel users must join (leave empty to disable) |
| `CHANNEL_GUARD_SESSION_STRING` | User session used to read the channel's admin log (bots cannot read it). Generate with `python generate_session_string.py` |

### Access control

| Setting | Meaning |
|---|---|
| `ALLOWED_GROUP` | Group IDs the bot serves (empty = no groups) |
| `ADMIN_GROUP` | Groups whose admins can use admin commands |
| `ALLOWED_USERS` | Restrict private chat to these user IDs (empty = everyone) |

### Cookies, proxies, YouTube

| Setting | Meaning |
|---|---|
| `COOKIE_URL`, `YOUTUBE_COOKIE_URL`, `YOUTUBE_COOKIE_URL_1…10`, `INSTAGRAM_COOKIE_URL`, `TIKTOK_COOKIE_URL`, `FACEBOOK_COOKIE_URL`, `TWITTER_COOKIE_URL`, `VK_COOKIE_URL` | Where `/cookie` downloads cookie files from |
| `YOUTUBE_COOKIE_ORDER` | `round_robin` or `random` |
| `SHARE_ADMIN_COOKIES` | If `True`, users use the admin's cookie file |
| `PROXY_TYPE`, `PROXY_IP`, `PROXY_PORT`, `PROXY_USER`, `PROXY_PASSWORD` | First proxy |
| `PROXY_2_*` | Second proxy |
| `PROXY_SELECT` | `round_robin` or `random` |
| `YOUTUBE_POT_ENABLED`, `YOUTUBE_POT_BASE_URL` | PO token provider settings |
| `YOUTUBE_POT_DISABLE_INNERTUBE` | Disable the innertube client if tokens stop working |

### Database & cache

| Setting | Meaning |
|---|---|
| `USE_FIREBASE` | Enable the Firebase-backed cache |
| `FIREBASE_CONF`, `FIREBASE_USER`, `FIREBASE_PASSWORD` | Firebase project settings |
| `RELOAD_CACHE_EVERY` | Hours between automatic cache reloads |
| `AUTO_CACHE_RELOAD_ENABLED` | Enable scheduled cache reloads |
| `FIREBASE_CACHE_FILE` | Local cache dump (`dump.json`) |

### Environment variables

Some behaviour is controlled by environment variables (read with `os.getenv`):

| Variable | Default | Purpose |
|---|---|---|
| `TG_BOT_WORKERS` | `10` | Pyrogram handler workers |
| `TG_MAX_TRANSMISSIONS` | `10` | Parallel chunks per upload |
| `BUTTON_STYLE` | on | Set to `off` to disable colored buttons |
| `ASK_INSTANT_CARD` | — | Show the "Always Ask" card instantly |
| `TG_YTDLP_BG_WORKERS`, `TG_YTDLP_BG_INFLIGHT` | auto | Background worker counts |
| `MONGO_DB_NAME` | — | MongoDB database name for cookie storage |
| `WELCOME_PHOTO_CHAT_ID`, `WELCOME_PHOTO_MESSAGE_ID` | — | Welcome photo source |
| `BOT_CONTAINER_NAME`, `WARP_CONTAINER_NAME`, `DASHBOARD_CONTAINER_NAME` | `tg-ytdlp-*` | Container names used by the dashboard |
| `DASHBOARD_PORT` | `5555` | Dashboard port |
| `FREE_PROXY_SOURCES`, `FREE_PROXY_TEST_URL` | — | Free proxy list sources and test URL |

---

## 🍪 Cookies & Private Content

Some content needs a logged-in session. Ways to provide cookies:

1. **Upload** a Netscape-format `cookie.txt` to the bot as a document.
2. **Paste** the content and use `/save_as_cookie`.
3. **Host** cookie files on the configuration web server and use `/cookie <service>`.
4. **Extract** from a browser with `/cookies_from_browser` (only works where the bot can reach the browser profile).

Each user gets a personal cookie file under `users/<user_id>/cookie.txt`. If `SHARE_ADMIN_COOKIES` is `True`, users without their own file use the admin's.

To check a cookie file, use `/check_cookie`. For YouTube, the bot tests it against a known public video and falls back to the next configured URL if the test fails.

> Never share your cookie files publicly. They give full access to the account they belong to.

---

## 🌐 Proxy & Network

- **Per user:** `/proxy on` or `/proxy off`. AUTO mode uses the proxy only when YouTube returns an error.
- **Global:** configure `PROXY_*` in `CONFIG/config.py`.
- **Free proxies:** `HELPERS/free_proxy.py` can fetch and test public proxy lists. Use with care, as free proxies are unreliable and can log traffic.
- **WARP:** the `warp` container runs a Cloudflare WireGuard tunnel (`wgcf`) that the bot's network uses. Its health check requires the WireGuard interface to be up.

---

## 📊 Web Dashboard

The dashboard runs on **http://localhost:5555** (login required, with a lockdown mode after repeated failed logins).

**Overview & analytics**
- Active users, power users, top downloaders, top domains, top countries
- NSFW statistics (top users and domains)
- Playlist and multi-URL usage, format preferences
- Channel join statistics and channel events
- Suspicious users and blocked users
- Per-user download history

**Management**
- Block and unblock users
- Edit configuration values from the browser (`/api/update-config`)
- Update domain block/allow lists, from files or from URLs
- Update the lists in the background
- Restart the bot or dashboard service
- Rotate IP (for WARP)
- Update the download engines (yt-dlp, gallery-dl)
- Clean up a user's files

**System**
- CPU, memory, and disk metrics
- Installed package versions
- Health endpoint: `GET /health`

The dashboard talks to the Docker socket (`/var/run/docker.sock`) to restart containers. Protect it as you would any server admin panel: do not expose it to the public internet without HTTPS and a strong password.

---

## 📏 Limits & Restrictions

From `CONFIG/limits.py` (defaults):

| Limit | Default |
|---|---|
| Max file size | 8 GiB (`MAX_FILE_SIZE_GB`) |
| Concurrent single-URL downloads per user | 3 |
| Max video duration | 12 hours |
| Max images per `/img` request | 1000 |
| Max subtitle quality | 720p |
| Max subtitle duration / size | 90 min / 500 MB |
| Playlist items (bare link) | 100000 |
| Upload timeout | 20 min |
| Upload stall timeout | 4 min |
| Download timeout | 30 days |
| HTTP request timeout | 60 s |
| Max HTTP connection lifetime | 4 h |
| Max animation duration | 4 h |
| Image download wait per range / total / inactivity | 30 min / 4 h / 5 min |
| Concurrent uploads | Auto-detected from CPU count (2–8) |
| Live stream blocking | Disabled (`ENABLE_LIVE_STREAM_BLOCKING`) |

Admins can be exempt from limits with `TURN_OFF_LIMITS_FOR_ADMINS = True`.

**Blocked content:** DRM streaming services, messengers, banking and government sites, marketplaces, and other non-media domains are listed in `CONFIG/domains.py` and refused.

---

## 🗣 Languages & Messages

All bot texts live in `CONFIG/LANGUAGES/messages_*.py`. The code loads English (`messages_EN.py`) by default; the `Config.get_messages()` method is the single place to change which file is used. The repository includes message files for many languages (Arabic, Bengali, Chinese, French, German, Hausa, Indonesian, Italian, Japanese, Kazakh, Korean, Persian, Polish, Portuguese, Russian, Spanish, Tagalog, Thai, Turkish, Ukrainian, Urdu, Uzbek, and Vietnamese, among others). Note that the bot currently ships with language selection simplified to English only.

To add a language, copy `messages_EN.py` to `messages_XX.py`, translate the strings, and update `language_router.py`.

---

## 🧰 Maintenance Scripts

| Script | Purpose |
|---|---|
| `UPDATE.sh` | Update the bot from the Git repository (creates a backup first) |
| `scripts/UPDATE_DOCKER.sh` | Update the Docker deployment |
| `scripts/update_from_repo.py` | Pull and apply repository updates |
| `engines_updater.sh`, `scripts/engines_updater.sh` | Update the download engines (yt-dlp, gallery-dl) |
| `scripts/update_bgutil_provider.sh` | Update the PO token provider |
| `create_backup.py`, `scripts/create_backup.py` | Create a backup of data and config |
| `scripts/restore_from_backup.py` | Restore from a backup |
| `scripts/clean_fire_logs.py` | Remove old log files |
| `scripts/remove_domain_list_term.py` | Remove a term from the domain lists |
| `scripts/monitor_bot_resources.sh` | Watch CPU and memory usage |
| `scripts/configure_tcp_keepalive.sh` | Tune TCP keepalive for long connections |
| `scripts/health_server.py` | Health-check server |
| `scripts/generate_session_string.py`, `generate_session_string.py` | Create the user session for the channel guard |
| `PATCH/run_patch.py` | Apply the bundled patches (None-comparison and global-message fixes) |

---

## 🗂 Project Structure

```text
all-downloader/
├── magic.py                 # Main bot entry point (Pyrogram)
├── web/                     # FastAPI dashboard (app, templates, static files)
├── CONFIG/                  # Config, limits, commands, domains, messages, languages
├── COMMANDS/                # One module per command (/img, /format, /subs, /cookie, …)
├── DOWN_AND_UP/             # Download & upload pipeline (yt-dlp, gallery-dl, ffmpeg, sender)
├── URL_PARSERS/             # URL detection, normalising, playlist ranges, tags, routing
├── HELPERS/                 # Rate limiting, proxies, PO tokens, logging, caption, guards
├── DATABASE/                # Cache DB, Firebase init, Firebase dump downloader
├── services/                # Dashboard services: stats, auth, system metrics, lists
├── scripts/                 # Maintenance, update, backup, health scripts
├── PATCH/                   # Bundled code patches
├── docker/configuration-webserver/  # Caddy config and cookie site
├── warp/                    # Dockerfile + entrypoint for the WARP tunnel
├── _etc/systemd/            # systemd unit files
├── TXT/                     # Supported sites, command list, domain lists
├── tests/                   # Unit tests
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🧪 Testing

Tests live in `tests/` (currently `tests/test_stats_collector.py`). Run them from the project root with `python -m pytest tests/` (install `pytest` first).

---

## 🩺 Troubleshooting

| Problem | What to try |
|---|---|
| Bot does not reply | Check `docker compose logs -f bot`. Confirm `BOT_TOKEN` and that the bot is not blocked for your account. |
| "Sign-in" errors on startup | Telegram FloodWait: the bot waits and retries automatically. Wait a few minutes. |
| YouTube "Sign in to confirm you're not a bot" | Upload fresh cookies (`/save_as_cookie`), add a second YouTube cookie source, or enable a proxy with `/proxy on`. Check that `bgutil-provider` is running. |
| Only low resolutions (≤480p) on YouTube | Make sure Node.js 22+ is installed (required for the EJS solver). |
| Instagram/TikTok/Facebook private content fails | Provide cookies for that service. |
| Large file fails to upload | Reduce part size with `/split`, check disk space, and check the upload timeouts in `limits.py`. |
| Subtitles are missing or garbled | Install fonts (Noto, CJK, Amiri) and check `/subs`. |
| Dashboard shows nothing | Check `DASHBOARD_PORT`, the `dashboard` container logs, and that `/var/run/docker.sock` is mounted. |
| Command ignored in a group | Add the group ID to `ALLOWED_GROUP` and make sure the bot is an admin there. |
| Commands not showing in Telegram menu | Restart the bot; the menu is published on each start. |

---

## 🔐 Security

- **Never commit real secrets.** Move `BOT_TOKEN`, `API_HASH`, `CHANNEL_GUARD_SESSION_STRING`, database passwords, and proxy credentials into environment variables or a local `.env` file that is excluded from Git. If a token or session has ever been published, **rotate it** (revoke the bot token in @BotFather and terminate the session).
- Cookie files are equivalent to passwords. Keep them private.
- Put the dashboard behind HTTPS and a reverse proxy, or restrict it to a private network.
- Keep the Docker socket mount limited to the dashboard service.
- Report security issues privately as described in [SECURITY.md](SECURITY.md).

---

## 🤝 Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, code style, and the pull request process.

Quick outline:
1. Fork the repository and create a feature branch.
2. Make focused changes and add tests where practical.
3. Run the test suite.
4. Open a pull request describing the change.

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE).

---

## 🙏 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) and its contributors
- [gallery-dl](https://github.com/mikf/gallery-dl)
- [Pyrogram](https://github.com/pyrogram/pyrogram) / [kurigram](https://github.com/KurimuzonAkuma/kurigram)
- [FFmpeg](https://ffmpeg.org/), [MediaInfo](https://mediaarea.net/)
- [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider)
- Developer and maintainer: **@Anujedits76**
