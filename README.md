# 🤖 tg-ytdlp-bot (All Downloader)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Kurigram](https://img.shields.io/badge/Pyrogram_fork-Kurigram-green.svg)](https://github.com/KurimuzonAkuma/kurigram)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-Latest-red.svg)](https://github.com/yt-dlp/yt-dlp)
[![gallery-dl](https://img.shields.io/badge/gallery--dl-Latest-orange.svg)](https://github.com/mikf/gallery-dl)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> 🎥 **An advanced Telegram bot that downloads video, audio and images from 1,400+ websites.**

Send a link, pick a quality, get the file in Telegram. The bot is powered by **yt-dlp** (video/audio) and **gallery-dl** (images), and adds codec/container selection, multi-track audio & subtitles, trimming, direct stream links, proxy and cookie management, 25 interface languages, NSFW handling, Telegram Stars paid posts, a Firebase-backed user database and a live statistics dashboard.

Russian documentation: [README_RU.md](README_RU.md)

---

## 📋 Table of Contents

**For users**
1. [Features A–Z](#-features-a-z)
2. [Quick Start](#-quick-start)
3. [Commands](#-commands)
4. [Supported Languages](#-supported-languages)
5. [Troubleshooting](#-troubleshooting)

**For admins / self-hosters**
6. [Installation](#-installation)
7. [Configuration](#-configuration)
8. [Limits & Cooldowns](#-limits--cooldowns)
9. [Advanced Features](#-advanced-features)
10. [Admin Commands](#-admin-commands)
11. [Firebase Setup](#-firebase-setup)
12. [Statistics Dashboard](#-statistics-dashboard)
13. [Updating, Backup & Restore](#-updating-backup--restore)
14. [Maintenance](#-maintenance)
15. [Project Structure](#-project-structure)
16. [Contributing](#-contributing)
17. [License](#-license)
18. [Credits](#-credits)

---

# 👥 PART 1 — FOR USERS

## ✨ Features A–Z

| | Feature | What it does |
|---|---|---|
| **A** | **Always Ask menu** | Interactive quality picker with CODEC, DUBS, SUBS, TRIM and LINK buttons. |
| **A** | **Anti-bot protection** | Built-in helpers to bypass bot checks / blocks on supported sites. |
| **A** | **Args (`/args`)** | Per-user custom yt-dlp arguments through a grouped menu (boolean, select, numeric, text/JSON headers). |
| **A** | **Audio extraction (`/audio`)** | Download only the audio track of any supported link. |
| **A** | **Auto cache** | Periodic refresh of the local Firebase dump (`/auto_cache on/off/N`). |
| **B** | **Backup & restore** | Updater creates timestamped backups; interactive restore tool included. |
| **B** | **Broadcast** | Admins can send a message to all users (`/broadcast`). |
| **B** | **Block / unblock users** | Admin commands and dashboard buttons. |
| **C** | **Caching** | Already-downloaded media is reused (trimmed videos are never cached). |
| **C** | **Codec & container choice** | H.264/AVC, AV1, VP9 and MP4 / MKV. |
| **C** | **Cookies** | Download, validate, upload and extract cookies (`/cookie`, `/check_cookie`, `/save_as_cookie`, `/cookies_from_browser`). |
| **C** | **Channel guard / subscription** | Optional required-subscription channel check. |
| **C** | **Crontab cleanup** | Example cron job to wipe users' download folders daily. |
| **D** | **Dashboard** | FastAPI web panel with live stats, top users/domains, block/unblock. |
| **D** | **Direct links (`/link`)** | Get direct stream URLs (video + audio) for VLC, MX Player, Infuse, IINA, nPlayer, MPV or a browser. |
| **D** | **Docker support** | Bot + WARP + PO-token provider + dashboard + cookie web server via Docker Compose. |
| **D** | **Dubs (`/dubs`)** | Choose / embed alternative audio languages (multi-audio). |
| **E** | **Error handling** | Smart retries, document-mode fallback, graceful format/network failure handling. |
| **F** | **Firebase** | Realtime Database for users, logs and cache with a local JSON dump. |
| **F** | **Flood-wait protection** | Detects Telegram rate limits, informs the user and persists state. |
| **F** | **Format selection (`/format`)** | `720`, `4k`, `8k`, `best`, `ask`, or an exact format ID. |
| **F** | **FFmpeg processing** | Merge, trim, re-encode, split and embed tracks. |
| **G** | **Gallery-dl integration** | Image/gallery downloading from many platforms. |
| **G** | **Group mode** | Works in groups with `ADMIN_GROUP` / `ALLOWED_GROUP` and limit multipliers. |
| **H** | **Health server** | Lightweight health endpoint script for monitoring. |
| **I** | **Image downloads (`/img`)** | Direct image URLs, albums, ranges, cloud storage links. |
| **I** | **Inline search (`/search`)** | Find videos from any chat via `@vid <query>`. |
| **K** | **Keyboard (`/keyboard`)** | Reply keyboard modes: `off`, `1x3`, `2x3`, `full`. |
| **L** | **Languages (`/lang`)** | 25 fully translated interface languages. |
| **L** | **Limits** | File size, duration, playlist, multi-URL, rate and command limits in one file. |
| **L** | **Live-stream downloader** | Live stream support with duration limit and blocking switch. |
| **L** | **List formats (`/list`)** | Show all available formats and export them as a text file. |
| **M** | **MediaInfo (`/mediainfo`)** | Optionally send technical file info with each download. |
| **M** | **Multi-URL queue** | Up to 10 URLs per message (20 in groups) with progress "URL: X / Y". |
| **M** | **Multi-track MKV** | Several audio languages + several subtitle tracks in one MKV. |
| **M** | **MongoDB cookies helper** | Optional cookie storage via MongoDB (`pymongo`). |
| **N** | **NSFW management** | Auto-detection, `#nsfw` tag, spoiler blur, whitelist/greylist/blacklist. |
| **P** | **Paid posts (Telegram Stars)** | NSFW content can be sent as paid posts; price set by `NSFW_STAR_COST`. |
| **P** | **Playlists & ranges** | `url*1*3` ranges and `/vid 3-7 <url>` shortcut. |
| **P** | **PO Token provider** | bgutil provider to bypass YouTube "Sign in to confirm you're not a bot". |
| **P** | **Proxy (`/proxy`)** | Up to 2 proxies, round-robin or random, per-user on/off. Free-proxy helper included. |
| **R** | **Rate limiting** | Per-minute/hour/day URL limits plus exponential command cooldowns. |
| **S** | **Split (`/split`)** | Split large videos into 100 MB – 2 GB parts. |
| **S** | **Subtitles (`/subs`)** | Language selection, auto-generated/translated subs, soft (MKV) or hard (MP4) embedding. |
| **S** | **Stats collector** | In-memory live statistics fed by DB hooks. |
| **S** | **systemd services** | Ready-made units for the bot and the dashboard. |
| **T** | **Tags** | `url#tag1#tag2` adds tags to captions; `/tags` lists them. |
| **T** | **Thumbnails** | Automatic thumbnail / cover preparation (including 320×320 paid-post covers). |
| **T** | **Trim** | Cut a time range `HH:MM:SS-HH:MM:SS` with FFmpeg. |
| **U** | **Updater scripts** | One-command code update for local and Docker setups, with automatic backups. |
| **U** | **Usage (`/usage`)** | Personal usage logs and statistics. |
| **V** | **Video downloads (`/vid`)** | Paste a link or use `/vid <url>`. |
| **W** | **WARP container** | Cloudflare WARP (WireGuard) network namespace for the bot. |
| **Y** | **YouTube cookies (multi-source)** | Up to 10 cookie sources with automatic validation and fallback. |
| **Z** | **Zero-config for users** | Just send a link — everything else is optional. |

---

## 🚀 Quick Start

1. **Send a video link** to the bot.
2. **Choose the quality** from the interactive menu.
3. **Receive the file** in Telegram.

Single link:
```
https://youtube.com/watch?v=dQw4w9WgXcQ
```

Multiple links (works when a fixed quality is set with `/format`):
```
https://youtube.com/watch?v=video1
https://youtube.com/watch?v=video2
https://youtube.com/watch?v=video3
```

Add tags to a link:
```
https://youtu.be/STeeOaX2FBs#music#favorite
```

**Supported platforms:** YouTube, TikTok, Instagram, Twitter/X, Facebook, VK, Vimeo, Twitch, Dailymotion, Bilibili and 1,400+ more (full list in [`TXT/supported_sites.txt`](TXT/supported_sites.txt)).

---

## 📌 Commands

### Basic
| Command | Description | Example |
|---|---|---|
| `/start` | Start the bot | `/start` |
| `/help` | Show help | `/help` |
| `/settings` | Open settings menu | `/settings` |
| `/usage` | Your usage logs/statistics | `/usage` |
| `/tags` | List all your `#tags` | `/tags` |
| `/lang` | Change interface language | `/lang en` |
| `/add_bot_to_group` | Terms of use / how to add the bot to a group | `/add_bot_to_group` |

### Downloading
| Command | Description | Example |
|---|---|---|
| *Any URL* | Auto-detect and download | `https://youtube.com/watch?v=...` |
| `/vid` | Download video | `/vid https://...` |
| `/vid <a>-<b>` | Playlist range shortcut | `/vid 3-7 https://youtube.com/playlist?list=...` |
| `/audio` | Audio only | `/audio https://...` |
| `/img` | Images / galleries | `/img https://instagram.com/p/...` |
| `/link` | Direct stream links | `/link 720 https://...` |
| `/playlist` | How to download playlists | `/playlist` |
| `/search` | Inline search helper (`@vid query`) | `/search` |

### Format & quality
| Command | Description | Example |
|---|---|---|
| `/format` | Quality / codec / container | `/format 720`, `/format 4k`, `/format best`, `/format ask`, `/format id 134` |
| `/list` | Show all formats for a URL | `/list https://...` |
| `/split` | Split size (100mb–2gb) | `/split 500mb` |
| `/mediainfo` | Toggle MediaInfo output | `/mediainfo on` |
| `/subs` | Subtitle settings | `/subs en auto`, `/subs ru`, `/subs off` |
| `/dubs` | Audio dub settings | `/dubs ru`, `/dubs off` |

### Cookies, proxy & advanced
| Command | Description | Example |
|---|---|---|
| `/cookie` | Download cookies from the web | `/cookie youtube`, `/cookie youtube 3`, `/cookie tiktok`, `/cookie x` |
| `/check_cookie` | Validate your current cookies | `/check_cookie` |
| `/save_as_cookie` | Save text / upload a `.txt` as your cookie | `/save_as_cookie` |
| `/cookies_from_browser` | Extract cookies from a server browser | `/cookies_from_browser` |
| `/proxy` | Turn proxy on/off | `/proxy on` |
| `/args` | Custom yt-dlp arguments | `/args` |
| `/keyboard` | Reply keyboard layout | `/keyboard full` |
| `/nsfw` | NSFW blur on/off | `/nsfw off` |
| `/clean` | Remove your stored files/settings | `/clean args`, `/clean nsfw`, `/clean proxy`, `/clean flood_wait` |

### Quick-setup cheat sheet
```bash
/format 720          # 720p or lower
/format 4k           # 4K or lower
/format ask          # always ask
/subs en auto        # English, auto-generated / translated
/keyboard 2x3        # default keyboard
/split 1gb           # split into 1 GB parts
/proxy on            # use proxy
```

---

## 🌍 Supported Languages

25 languages with full interface translation. Switch with `/lang <code>` or use `/lang` for a menu.

| Code | Language | Code | Language | Code | Language |
|---|---|---|---|---|---|
| `en` | English | `ru` | Русский | `ar` | العربية |
| `in` | हिन्दी (Hindi) | `zh` | 中文 | `es` | Español |
| `fr` | Français | `bn` | বাংলা | `pt` | Português |
| `ur` | اردو | `id` | Bahasa Indonesia | `ja` | 日本語 |
| `tl` | Filipino | `ha` | Hausa | `vi` | Tiếng Việt |
| `it` | Italiano | `de` | Deutsch | `tr` | Türkçe |
| `ko` | 한국어 | `pl` | Polski | `uk` | Українська |
| `fa` | فارسی | `th` | ไทย | `uz` | Oʻzbek |
| `kk` | Қазақ | | | | |

---

## 🔧 Troubleshooting

**Bot does not start**
- Check every required field in `CONFIG/config.py`.
- Make sure the bot is an **admin** in all log channels.
- Python **3.11+** is required.

**YouTube videos fail to download**
- Run `/check_cookie`, then `/cookie youtube` to fetch fresh cookies.
- The video may be age-restricted, private or IP-blocked — try `/proxy on`.
- Enable the PO Token provider (see [Installation](#-installation)).

**Firebase connection errors**
- Verify project credentials and Realtime Database rules.
- Check the server's network connection.

**Language does not change**
- Confirm the language file exists in `CONFIG/LANGUAGES/`.
- Use `/lang` to reset; restart the bot if files were updated.

---

# 👨‍💼 PART 2 — FOR ADMINS & SELF-HOSTERS

## 🛠️ Installation

### 🚢 Option A — Docker (recommended)

Runs the bot, WARP network, PO-token provider and dashboard in containers.

**Requirements:** Docker + Docker Compose, a Linux server/VPS (Ubuntu/Debian recommended).

**1. Clone and create the config**
```bash
git clone <your-repo-url> tg-ytdlp-bot
cd tg-ytdlp-bot
cp CONFIG/_config.py CONFIG/config.py     # if a template exists; otherwise edit CONFIG/config.py
```

Fill at least: `BOT_NAME`, `BOT_NAME_FOR_USERS`, `ADMIN`, `ADMIN_USERNAME`, `API_ID`, `API_HASH`, `BOT_TOKEN`, all `LOGS_*` channels, and optionally `ADMIN_GROUP`, `ALLOWED_GROUP`, `ALLOWED_USERS`, `SUBSCRIBE_CHANNEL`, `SUBSCRIBE_CHANNEL_URL`.

**2. Environment file**
```bash
cp .env.example .env     # set COMPOSE_PROJECT_NAME and TZ (e.g. Asia/Kolkata)
```

**3. Start**
```bash
docker compose build warp
docker compose up -d --build
```

Services started (see `docker-compose.yml`):
| Service | Purpose |
|---|---|
| `bot` | The Telegram bot (`magic.py`), runs inside the WARP network namespace |
| `warp` | Cloudflare WARP / WireGuard network layer |
| `bgutil-provider` | YouTube PO-token provider (`:4416`) |
| `dashboard` | FastAPI statistics panel (`:5555`) |
| `configuration-webserver` | *Optional* Caddy server for cookie files — start with `docker compose --profile configuration-webserver up -d` |

Cookie files are served at `http://localhost/cookies/<file>` inside the shared network namespace.

> ⚠️ Add the bot as **admin** to all configured channels.

### 🖥️ Option B — Manual (no Docker)

**Prerequisites:** Python 3.11+, Linux, FFmpeg, mediainfo, rsync, Node.js 22+, (optional) Chromium and Docker.

```bash
git clone <your-repo-url> tg-ytdlp-bot && cd tg-ytdlp-bot
chmod +x *.sh

sudo apt update
sudo apt install -y git python3.11 python3-pip python3.11-venv mediainfo rsync ffmpeg nodejs

python3.11 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt

node --version     # must be v22+. Otherwise install from NodeSource:
# curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs
```

**Optional – PO Token Provider (YouTube bypass):**
```bash
docker run -d --name bgutil-provider -p 4416:4416 --init --restart unless-stopped brainicism/bgutil-ytdlp-pot-provider
python3.11 -m pip install -U bgutil-ytdlp-pot-provider
```
```python
YOUTUBE_POT_ENABLED = True
YOUTUBE_POT_BASE_URL = "http://127.0.0.1:4416"
YOUTUBE_POT_DISABLE_INNERTUBE = False
```
If the provider is unreachable the bot silently falls back to normal YouTube extraction.

**Run:**
```bash
source venv/bin/activate
python3.11 magic.py
```

### Optional: extra fonts (Arabic / CJK / Indic subtitles)
```bash
sudo apt install fonts-noto-core fonts-noto-extra fonts-kacst fonts-kacst-one \
                 fonts-noto-cjk fonts-indic fonts-noto-color-emoji fontconfig libass9
sudo fc-cache -fv
```

### Optional: yt-dlp binary for `/cookies_from_browser`
Download the matching binary from the yt-dlp releases page, rename to `yt-dlp`, `chmod +x`, and symlink to `/usr/local/bin/yt-dlp`. A desktop environment and a supported browser must also be installed on the server.

---

## ⚙️ Configuration

All settings live in `CONFIG/config.py`.

```python
# Bot
BOT_NAME = "your_bot_name"
BOT_NAME_FOR_USERS = "tg-ytdlp-bot"
ADMIN = [123456789]                    # admin user IDs
ADMIN_USERNAME = "@your_username"
ADMIN_GROUP = [-1001234567890]         # groups with NO limits
ALLOWED_GROUP = [-1001234567891]       # groups with multiplied limits
ALLOWED_USERS = []                     # private-chat whitelist (empty = everyone)
API_ID = 12345678
API_HASH = "your_api_hash"
BOT_TOKEN = "123456:ABC..."

# Channels
LOGS_ID = -100...            # main log
LOGS_VIDEO_ID = -100...      # video log
LOGS_NSFW_ID = -100...       # NSFW log
LOGS_IMG_ID = -100...        # image log
LOGS_PAID_ID = -100...       # paid-content log
LOG_EXCEPTION = -100...      # error log
SUBSCRIBE_CHANNEL = -100...  # 0 or empty = no forced subscription
SUBSCRIBE_CHANNEL_URL = "https://t.me/your_channel"

# Cookies
COOKIE_URL = "https://your-domain.com/cookies/cookie.txt"
YOUTUBE_COOKIE_URL   = "https://your-domain.com/cookies/youtube.txt"
YOUTUBE_COOKIE_URL_1 = "https://your-domain.com/cookies/youtube-1.txt"
# ... up to YOUTUBE_COOKIE_URL_9

# Proxy (up to 2)
PROXY_TYPE = "http"          # http, https, socks4, socks5, socks5h
PROXY_IP = "X.X.X.X"
PROXY_PORT = 3128
PROXY_USER = "username"
PROXY_PASSWORD = "password"
PROXY_2_TYPE = "socks5"
PROXY_2_IP = "X.X.X.X"
PROXY_2_PORT = 3128
PROXY_2_USER = "username"
PROXY_2_PASSWORD = "password"
PROXY_SELECT = "round_robin"  # or "random"

# Firebase
USE_FIREBASE = True
FIREBASE_USER = "your-email@gmail.com"
FIREBASE_PASSWORD = "your-firebase-password"
FIREBASE_CONF = {
    "apiKey": "...", "authDomain": "...", "projectId": "...",
    "storageBucket": "...", "messagingSenderId": "...", "appId": "...",
    "databaseURL": "https://your-project-default-rtdb.firebaseio.com"
}

# Dashboard
DASHBOARD_PORT = 5555
DASHBOARD_USERNAME = "admin"
DASHBOARD_PASSWORD = "CHANGE_ME"

# Cache auto-refresh (hours)
RELOAD_CACHE_EVERY = 24
```

### Getting credentials
1. **Bot token** — talk to [@BotFather](https://t.me/BotFather) → `/newbot`.
2. **API ID / Hash** — [my.telegram.org](https://my.telegram.org) → *API development tools*.
3. **Channel / group IDs** — add the bot as admin, then use [@userinfobot](https://t.me/userinfobot). Channel/supergroup IDs start with `-100`.
4. **Your user ID** — [@UserInfoToBot](https://t.me/UserInfoToBot); add it to `ADMIN`.

### Cookie files (Docker)
```
TXT/cookie.txt                                  # default cookie for everybody
docker/configuration_webserver/site/cookies/
├── cookie.txt  youtube.txt  youtube-1.txt ... youtube-10.txt
├── instagram.txt  facebook.txt  tiktok.txt  twitter.txt  vk.txt
```
Cookies must be in **Netscape format**, max **100 KB** per file.

**Exporting YouTube cookies that stay valid:** open a private/incognito window, log in, open `https://www.youtube.com/robots.txt` in the same tab, export `youtube.com` cookies with the *Cookie-Editor* extension, then close the incognito window.

---

## ⏳ Limits & Cooldowns

Edit `CONFIG/limits.py` (restart the bot after changes).

| Area | Settings |
|---|---|
| Downloads & subtitles | `MAX_FILE_SIZE_GB`, `MAX_VIDEO_DURATION`, `MAX_SUB_*`, `GROUP_MULTIPLIER` |
| Multi-URL | `MAX_MULTI_URL_LIMIT` (default 10; ×`GROUP_MULTIPLIER` in groups) |
| Images & live streams | `MAX_IMG_*`, `MAX_IMG_TOTAL_WAIT_TIME`, `ENABLE_LIVE_STREAM_BLOCKING`, `MAX_LIVE_STREAM_DURATION` |
| Cookie cache | `COOKIE_CACHE_DURATION`, `COOKIE_CACHE_MAX_LIFETIME`, `YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR` |
| Rate limits | `RATE_LIMIT_PER_MINUTE/HOUR/DAY`, `RATE_LIMIT_COOLDOWN_*` (5 / 60 / 1440 min) |
| Commands | `COMMAND_LIMIT_PER_MINUTE`, `COMMAND_COOLDOWN_MULTIPLIER` (exponential) |
| NSFW monetization | `NSFW_STAR_COST` (Telegram Stars) |
| Admin bypass | `TURN_OFF_LIMITS_FOR_ADMINS` |

### 👑 Admin & group behaviour

When `TURN_OFF_LIMITS_FOR_ADMINS = True`:
- **Admins (`ADMIN`)** — no size/duration/playlist/rate/command/image/live-stream limits; NSFW is free (no Stars).
- **`ADMIN_GROUP`** — same as admins; `GROUP_MULTIPLIER` not applied; subscription check disabled.
- **`ALLOWED_GROUP`** — limits multiplied by `GROUP_MULTIPLIER` (default 2×); NSFW always free; subscription check disabled.
- A group listed in both lists is treated as `ADMIN_GROUP`.

When `False`, admins and admin groups follow normal limits (admin groups get `GROUP_MULTIPLIER`).

---

## 🎯 Advanced Features

### 🎬 Always Ask menu
- **📼 CODEC** — AVC (H.264), AV1, VP9; MP4 / MKV container; qualities filter dynamically.
- **📹 DUBS** — pick audio languages (flags, pagination, **ALL**, **OFF**). Shown only if multiple languages exist.
- **💬 SUBS** — original / auto-generated / translated subs, pagination, **ALL DUBS**, **OFF**.
- **✂️ TRIM** — cut `HH:MM:SS-HH:MM:SS` (e.g. `00:52:40-00:57:41`), frame-accurate with automatic re-encode fallback; trimmed videos are never cached.
- **☑️ LINK** — toggle direct-link mode; quality buttons return stream URLs honoring all filters.

### 🎧 Multi-track MKV
- Embeds all selected audio languages as separate tracks; original audio is always mapped first.
- Language codes preserved (`zh-Hans`, `en-US`, …); best audio per language (OPUS > AAC > MP3).
- Subtitles: original, auto-generated and translated; VTT/JSON3/SRV3/TTML → SRT, UTF-8 guaranteed, soft-muxed.
- Partial-success handling: tracks that downloaded are still embedded.
- Retry logic with proxy rotation for subtitle rate limiting.

### 💬 Subtitles logic
- **MKV** → soft-muxed tracks (no quality loss). **MP4** → hard-embedded subs (universal playback).
- Auto mode, Always-Ask mode and fast language detection with an optimized yt-dlp client.

### 📦 Multi-URL queue
Works only with a fixed quality (not Always Ask). Private chats: 10 URLs, groups: 20, admins: unlimited. Progress shown as `URL: X / Y`.

### 🔗 Direct links (`/link`)
```bash
/link https://...        # best
/link 720 https://...    # 720p or lower
/link 4k https://...     # 4K or lower
```
Falls back to the best available quality, returns separate video/audio URLs when needed, supports proxy and cookies.
Player buttons: 🌐 Browser, 🎬 VLC (iOS), 🎬 VLC (Android).

**Link template syntax**
| Pattern | Meaning |
|---|---|
| `https://example.com` | Single video (first item of a playlist) |
| `https://example.com*1*3` | Playlist items 1–3 |
| `https://example.com*1*3*name` | Items 1–3 named `name - Part 1`, `name - Part 2` … |

### 🏷️ Tags
`https://site.com/video#tag1#tag2` — tags (letters, digits, `_`) are appended to the caption and stored in `users/<id>/tags.txt`. `/tags` prints them all.

### 🖼️ Image downloads
Direct image URLs, Imgur, Flickr, DeviantArt, Pinterest, Instagram, Twitter/X, Reddit, Google Drive, Dropbox, Mega.nz, album ranges.

### ⚙️ `/args` — custom yt-dlp options
Grouped menu: ✅/❌ Boolean · 📋 Select · 🔢 Numeric · 📝🔧 Text/JSON. Example: Referer, User-Agent, custom headers, retries, timeout, fragment retries, output template.

### 📋 `/list`
Lists format IDs, resolution, codec and size, explains how to use `/format id <ID>`, and exports the full list as a text file.

### 🍪 Cookie management
- Up to **10 YouTube cookie sources** with automatic fallback.
- Validation: format check → size check (<100 KB) → real YouTube test → auth-vs-network error analysis.
- Source URLs are hidden from users; temp files cleaned after validation.
- Browser extraction through `/cookies_from_browser`.

### 🌐 Proxy
Global + per-user switch (`users/<id>/proxy.txt`), up to 2 proxies, `round_robin` or `random` selection, works with cookies, direct links and subtitle downloads.

### ⌨️ Keyboard modes
`off` · `1x3` (`/clean /cookie /settings`) · `2x3` (default) · `full` (emoji). Saved in `keyboard.txt`.

### 🔞 NSFW management
- Detection by domain and keyword (titles, descriptions, captions).
- Auto `#nsfw` tag, Telegram spoiler blur, user toggle `/nsfw on|off`.
- Three-level lists in `CONFIG/domains.py`: **WHITELIST** (never checked), **GREYLIST** (skip domain list, still keyword-checked), **BLACKLIST** (always blocked).
- Files: `TXT/porn_domains.txt`, `TXT/porn_keywords.txt`, `TXT/supported_sites.txt`.

### 💳 Paid posts (Telegram Stars) & groups
- NSFW can be sent as paid posts in private chats; cover auto-resized to 320×320.
- Price: `NSFW_STAR_COST`. Free for admins (when limits are off) and always free in groups.
- Add the bot as admin to a group to use all commands there.

### ⏱️ Flood-wait protection
Auto-detects Telegram limits, notifies users with an estimated wait, persists state across restarts, logs events for admins.

### 🛡️ Error handling
Smart retries, fallback to document mode, dynamic disk-space estimation, graceful format/network degradation.

### 🔍 Inline search
Type `@vid your query` in any chat. On mobile `/search` opens a pre-filled chat; on desktop type it manually.

---

## 🧑 Admin Commands

| Command | Description |
|---|---|
| `/block_user <id>` / `/unblock_user <id>` | Block / unblock a user |
| `/all_users` · `/all_blocked` · `/all_unblocked` | List users |
| `/run_time` | Bot uptime |
| `/log <id>` | Get a user's logs |
| `/broadcast` | Reply to a message to send it to all users |
| `/reload_cache` | Reload Firebase cache |
| `/auto_cache on\|off\|N` | Auto-refresh cache (N = 1–168 hours; saved to `RELOAD_CACHE_EVERY`) |
| `/update_porn` | Run the porn-list update script |
| `/reload_porn` | Hot-reload porn domains, keywords and supported sites |
| `/check_porn <url>` | Check a URL with a detailed explanation |
| `/uncache` | Clear subtitle cache |
| `/lang` | Language menu |

---

## 🔥 Firebase Setup

1. **Create a project** in the [Firebase Console](https://console.firebase.google.com/) and copy the web config from *Project Settings*.
2. **Create a Realtime Database** (test mode first is fine).
3. **Enable Authentication → Email/Password** and create a user.
4. **Lock down rules:**
```json
{
  "rules": {
    ".read":  "auth != null && auth.token.email === 'YOUREMAIL@gmail.com'",
    ".write": "auth != null && auth.token.email === 'YOUREMAIL@gmail.com'"
  }
}
```
5. Put the values in `FIREBASE_CONF`, `FIREBASE_USER`, `FIREBASE_PASSWORD`.

---

## 📊 Statistics Dashboard

A FastAPI service with a multi-tab UI and REST API (`web/dashboard_app.py`).

```bash
./venv/bin/python -m uvicorn web.dashboard_app:app --host 0.0.0.0 --port 5555
```
Open `http://<host>:5555`. In Docker it starts automatically.

**Shows:** active users (live), top downloads (day/week/month/all-time), countries, gender/age heuristics, popular domains, NSFW sources, playlist lovers, persistent users (≥10 URLs/day for 7 days), channel join/leave log (48 h), blocked users with one-click unblock.

**Data sources:** `dump.json` (refreshed by `DATABASE/download_firebase.py`), DB write hooks (`firebase_init.py`, `logger.py`, `StatsAwareDBAdapter`) and Telegram `getChat` (cached).

**REST endpoints:** `/api/active-users`, `/api/top-downloaders`, `/api/block-user`, `/api/channel-events`, `/health`, …

**Security:** change the default credentials, put it behind HTTPS (Nginx/Traefik), use an IP allow-list or SSH port-forwarding.

---

## 🔄 Updating, Backup & Restore

The updater clones the upstream repo, updates `.py`, `.sh`, Docker files, docs, `requirements.txt`, `CONFIG/LANGUAGES/` and `web/`, **keeps** your `CONFIG/config.py`, `CONFIG/domains.py`, `.env`, `script.sh`, `TXT/`, `users/`, `cookies/`, `_backup/`, sessions and logs, and stores backups as `*.backup_YYYYMMDD_HHMM` in `_backup/`.

**Local install**
```bash
./scripts/UPDATE.sh
# or
python3.11 scripts/update_from_repo.py --show-excluded
python3.11 scripts/update_from_repo.py
systemctl restart tg-ytdlp-bot
```

**Docker install**
```bash
chmod +x scripts/UPDATE_DOCKER.sh
./scripts/UPDATE_DOCKER.sh                  # full update
./scripts/UPDATE_DOCKER.sh --skip-update    # rebuild only
./scripts/UPDATE_DOCKER.sh --no-cache       # clean build
./scripts/UPDATE_DOCKER.sh --help
```
`--remove-volumes` also deletes the `warp-data` volume (WireGuard config) — use with care.

Manual and partial updates:
```bash
docker compose down && docker compose build && docker compose up -d
docker compose up -d --build bot dashboard
docker compose pull bgutil-provider && docker compose up -d bgutil-provider
docker compose ps && docker compose logs -f bot
curl http://localhost:5555/health
```

**Restore from backup**
```bash
python3.11 scripts/restore_from_backup.py                       # interactive (↑/↓, Enter, q)
python3.11 scripts/restore_from_backup.py --list
python3.11 scripts/restore_from_backup.py --timestamp YYYYMMDD_HHMM
```

---

## 🧹 Maintenance

**Daily cleanup of user downloads (cron)**
```bash
0 0 * * * /usr/bin/find /path/to/tg-ytdlp-bot/users -type f ! -name "cookie.txt" ! -name "logs.txt" -delete
```

**systemd autostart**
```bash
sudo cp _etc/systemd/system/tg-ytdlp-bot.service       /etc/systemd/system/
sudo cp _etc/systemd/system/tg-ytdlp-dashboard.service /etc/systemd/system/
# edit WorkingDirectory / ExecStart paths first
sudo systemctl daemon-reload
sudo systemctl enable --now tg-ytdlp-bot tg-ytdlp-dashboard
journalctl -u tg-ytdlp-bot -f
```

**Helper scripts (`scripts/`)**: `UPDATE.sh`, `UPDATE_DOCKER.sh`, `update_from_repo.py`, `restore_from_backup.py`, `create_backup.py`, `engines_updater.sh`, `update_bgutil_provider.sh`, `generate_session_string.py`, `clean_fire_logs.py`, `monitor_bot_resources.sh`, `configure_tcp_keepalive.sh`, `health_server.py`, `remove_domain_list_term.py`.

**Remove everything Docker-related**
```bash
docker stop tg-ytdlp-warp tg-ytdlp-dashboard tg-ytdlp-bot tg-ytdlp-bgutil-provider
docker rm   tg-ytdlp-warp tg-ytdlp-dashboard tg-ytdlp-bot tg-ytdlp-bgutil-provider
docker system prune -a --volumes
```

---

## 🗂️ Project Structure

```
all-downloader/
├── magic.py                 # Bot entry point
├── COMMANDS/                # Command handlers (/vid, /format, /subs, /cookie, /proxy, /args, /nsfw, ...)
├── CONFIG/                  # config.py, limits.py, domains.py, messages, LANGUAGES/ (25 languages)
├── DATABASE/                # Firebase init, cache DB, dump downloader
├── DOWN_AND_UP/             # Download & upload engines (yt-dlp, gallery-dl, ffmpeg, live streams, sender, Always-Ask menu)
├── HELPERS/                 # Proxy, cookies, limiter, anti-bot, logging, safe messenger, PO token, NSFW detection...
├── URL_PARSERS/             # URL normalizer, extractors, tags, thumbnails, engine router
├── services/                # Auth, lists, stats collector, system service
├── web/                     # FastAPI dashboard (templates + static)
├── scripts/                 # Update / backup / restore / maintenance scripts
├── warp/                    # Cloudflare WARP container
├── docker/                  # Caddy cookie web server + cookie templates
├── TXT/                     # Cookie, porn lists, supported_sites, commands
├── _etc/systemd/system/     # systemd units
├── tests/                   # Unit tests
├── Dockerfile · docker-compose.yml · requirements.txt
└── LICENSE · CONTRIBUTING.md · SECURITY.md · README_RU.md
```

**Main dependencies:** `kurigram`, `yt-dlp[default,curl-cffi]`, `gallery-dl`, `bgutil-ytdlp-pot-provider`, `firebase-admin`, `pymongo[srv]`, `fastapi`, `uvicorn`, `jinja2`, `aiohttp`, `aiofiles`, `moviepy`, `pillow`, `psutil`, `tldextract`, `TgCrypto-pyrofork`.

---

## 🤝 Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git clone https://github.com/<your-username>/tg-ytdlp-bot.git
cd tg-ytdlp-bot
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3.11 magic.py
```

1. Fork the repo
2. `git checkout -b feature/amazing-feature`
3. `git commit -m "Add amazing feature"`
4. `git push origin feature/amazing-feature`
5. Open a Pull Request

Security issues: see [SECURITY.md](SECURITY.md).

---

## 📄 License

Distributed under the **GNU General Public License v3.0** — see [LICENSE](LICENSE).

---

## 🙏 Credits

- **Original author:** [upekshaip](https://github.com/upekshaip)
- **Lead developer & contributor:** [chelaxian](https://github.com/chelaxian)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — video extraction
- [gallery-dl](https://github.com/mikf/gallery-dl) — image extraction
- [Kurigram / Pyrogram fork](https://github.com/KurimuzonAkuma/kurigram) — Telegram MTProto client
- [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) — YouTube PO tokens

## 💖 Support

⭐ Star the repo · 🐛 report bugs · 💡 suggest features · 📢 share with others.

> ⚠️ **Disclaimer:** Download only content you have the right to download and respect each platform's Terms of Service and local copyright laws.
