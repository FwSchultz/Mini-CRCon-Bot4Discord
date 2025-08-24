<div align="center">

  <img src="https://github.com/FwSchultz/assets/blob/main/bots/FwS-Bots/Bot.png" alt="logo" width="200" height="auto" />
  <h1>**A lightweight Discord bot to manage and control a Hell Let Loose server via CRCON.**</h1>
  
<!-- Badges -->
<p>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/FwSchultz/Mini-CRCon-Bot4Discord" alt="contributors" />
  </a>
  <a href="">
    <img src="https://img.shields.io/github/last-commit/FwSchultz/Mini-CRCon-Bot4Discord" alt="last update" />
  </a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/network/members">
    <img src="https://img.shields.io/github/forks/FwSchultz/Mini-CRCon-Bot4Discord" alt="forks" />
  </a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/stargazers">
    <img src="https://img.shields.io/github/stars/FwSchultz/Mini-CRCon-Bot4Discord" alt="stars" />
  </a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/issues/">
    <img src="https://img.shields.io/github/issues/FwSchultz/Mini-CRCon-Bot4Discord" alt="open issues" />
  </a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/FwSchultz/Mini-CRCon-Bot4Discord.svg" alt="license" />
  </a>
</p>
   
<h4>
    <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord">Documentation</a>
  <span> · </span>
    <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/issues/">Report Bug</a>
  <span> · </span>
    <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/issues/">Request Feature</a>
  </h4>

[German version](readme_DE.md)

</div>
<br />

## 📑 Table of Contents
- [About the Project](#-about-the-project)  
- [Tech Stack](#-tech-stack)  
- [Environment Variables & Tokens](#-environment-variables--tokens)  
- [Requirements](#-requirements)  
- [Getting Started](#-getting-started)  
  - [Create Discord Bot and Set Permissions](#1-create-discord-bot-and-set-permissions)  
  - [Set up CRCON API Token and Permissions](#2-setup-crcon-api-token-and-permissions)  
  - [Clone Repository](#3-clone-repository)  
  - [Copy Templates (`dev.*`) to Active Files](#4-copy-templates-dev-to-active-files)  
  - [Edit Configuration Files](#5-edit-configuration-files)  
  - [Install Dependencies](#6-install-dependencies)  
  - [Run the Bot](#7-run-the-bot)  
- [Virtual Environments (Optional)](#-virtual-environments-optional)  
- [Usage](#-usage)  
- [Commands](#-commands)  
- [Roadmap](#-roadmap)  
- [License](#-license)  
- [Contact](#-contact)  

---

## 🚀 About the Project
The **Mini-CRCON Bot** provides an admin panel in Discord to control a Hell Let Loose server via the CRCON API.

**Goals:**
- Simple user interface for admins and moderators  
- Secure, reliable API communication with retries and error handling  
- Clean, minimalist control panel in the Discord channel  

---

## 🛠 Tech Stack
- **Python** 3.10+  
- **discord.py** (buttons, modals, selects, persistent views)  
- **requests** (HTTP client with retries)  
- **PyYAML** (`config.yml` configuration)  
- **python-dotenv** (`.env` secrets management)  

---

## 🔑 Environment Variables & Tokens

All secrets are stored in `.env`:

```env
# Discord
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
ADMIN_ROLE_IDS=111111111111111111,222222222222222222

# CRCON / API
API_BASE_URL=https://crcon.example.com
API_TOKEN=YOUR_CRCON_API_TOKEN

# Logging
LOG_LEVEL=INFO
```

---

## 📦 Requirements

You need Python 3.10 or higher. For Linux beginners (Ubuntu/Debian-based systems):

```bash
sudo apt update && sudo apt install python3 python3-pip -y
```

Check the Python version with:

```bash
python3 --version
```

If the version is < 3.10, see [Virtual Environments (Optional)](#-virtual-environments-optional) for installing newer versions.

---

## ⚙️ Getting Started

This guide targets Linux beginners. We’ll install the script without a virtual environment (venv) to keep it simple — venv is optional. **Important:** Without Discord and CRCON tokens and correct permissions, the bot will not work. You must adjust `.env` and `config.yml`.

### 1) Create Discord Bot and Set Permissions
- Go to the [Discord Developer Portal](https://discord.com/developers/applications).
- Create a **NEW APPLICATION**, add a **Bot**.
- Enable **Message Content Intent** (under Bot > Privileged Gateway Intents).
- Reset the token via the **Reset Token** button (blue button).
- Copy the **Bot Token** and store it securely — you need it for `.env`.
- Invite the bot to your server: Use the **Installation** menu (left sidebar) then choose Guild Install under Scopes `bot` and `applications.commands`.
- Choose these **Permissions** (without them the bot won’t work correctly):
  - View Channels  
  - Send Messages  
  - Embed Links  
  - Attach Files (for the bot’s banner) 
  - Read Message History  
  - Manage Messages (so the bot can clean the channel; otherwise it only deletes its own messages)  

### 2) [Setup CRCON API Token](https://github.com/MarechJ/hll_rcon_tool/wiki/Developer-Guides-%E2%80%90-CRCON-API) and Permissions
- Create an API token in your CRCON instance (DJANGO) with at least these permissions (otherwise features will be missing):
  - `get_players` → api | rcon user | **Can view get_players endpoint** (name, steam ID, VIP status and sessions) for all connected players
  - `get_detailed_players` → api | rcon user | **Can view get_detailed_players endpoint**
  - `message_player` → api | rcon user | **Can message players**
  - `set_map` → api | rcon user | **Can change the current map**
  - `kick` → api | rcon user | **Can kick players**
  - `punish` → api | rcon user | **Can punish players**
  - `switch_player_now` → api | rcon user | **Can immediately switch players**
- Copy the token and the base URL (e.g. https://crcon.example.com) — you need both for `.env`.

### 3) Clone Repository
Open a terminal and clone the repo:

```bash
git clone https://github.com/FwSchultz/Mini-CRCon-Bot4Discord.git
cd Mini-CRCon-Bot4Discord
```

If git is missing: `sudo apt install git -y`.

### 4) Copy Templates (`dev.*`) to Active Files
Copy the templates:

```bash
cp dev.env .env
cp dev.config.yml config.yml
```

### 5) Edit Configuration Files
- Open `.env` with an editor (e.g. `nano .env` or any text editor):
  - Replace `YOUR_DISCORD_BOT_TOKEN` with your bot token.
  - Set `CONTROL_CHANNEL_ID` to your Discord channel ID (Right-click > **Copy ID**; enable Developer Mode in Discord first).
  - Set `ADMIN_ROLE_IDS` to your admin role IDs (comma-separated).
  - Replace `https://crcon.example.com` and `YOUR_CRCON_API_TOKEN` with your values.
- Open `config.yml` (e.g. `nano config.yml` or a text editor) and adjust as needed:

<details>
<summary>Show config.yml</summary>

```yaml
app:
  # Ob die Buttons permanent registriert werden sollen (empfohlen)
  use_persistent_views: true
  # Kanal, in dem das Steuerungs-Panel stehen soll
  control_channel_id: 1223342343542346554
  # Log-Channel-ID (optional)
  log_channel_id: 1234567768677767667

ui:
  # Text des Hauptpanels
  panel_title: "Steuerungs-Panel"
  panel_intro: "Wähle eine Aktion. Missbrauch führt zum Entzug von Rechten."
  panel_color: 0x2b2d31

  # Optionales Theme (Farben als Hex oder "0x…")
  theme:
    primary: "0x2B2D31"   # dunkles Grau
    accent:  "0x5865F2"   # Discord Blurple
    success: "0x57F287"   # Grün
    danger:  "0xED4245"   # Rot

  icons:
    panel_message: "💬"
    panel_map: "🗺️"
    panel_kick: "🔨"
    panel_punish: "⚠️"
    panel_switch: "🔁"

    msg_one: "👤"
    msg_allies: "🔵"
    msg_axis: "🔴"
    msg_all: "📣"
    back: "↩️"

  banner:
    enabled: true
    # Lokales Bild (relativ zum Projektordner)
    path: "assets/panel_banner.png"
    # Alternativ per URL:
    # url: "https://example.com/dein-banner.png"

api:
  debug: true
  timeout_seconds: 20
  retries:
    total: 2
    backoff_factor: 0.3

messaging:
  enabled: true
  # Sicherheits-Cooldown in Millisekunden zwischen Einzel-PMs
  per_player_delay_ms: 120
  # Pagination ab X Spielern
  page_size: 25
  # Auto-Löschung von Bestätigungen (Sekunden)
  ephemeral_ttl_seconds: 20
  buttons:
    single: true
    allies: true
    axis: true
    all: true

map_switch:
  enabled: true
  button_label: "Map wechseln"
  ephemeral: false
  ttl_seconds: 15

kick_player:
  enable: true
  require_reason: true
  default_reason: "Regelverstoß"

punish_player:
  enable: true
  default_by: "Admin"

switch_player:
  enable: true
```
</details>

### 6) Install Dependencies
Install Python packages globally (without venv):

```bash
pip3 install -r requirements.txt
```

If pip is missing: `sudo apt install python3-pip -y`. Ensure `discord.py >= 2.2` is installed.

### 7) Run the Bot
Start the bot:

```bash
python3 bot.py
```

The bot deletes non-pinned messages in the control channel and posts the panel. If errors occur, set `LOG_LEVEL=DEBUG` in `.env` for more info.

### (Optional) Run as a SystemD Service
For continuous operation create `/etc/systemd/system/mini-crcon-bot.service`:

```ini
[Unit]
Description=Mini-CRCON Discord Bot
After=network-online.target
OnFailure=unit-status-mail@%n.service

[Service]
User=dein-benutzer  # Nicht root, erstelle einen dedizierten User
Type=simple
Restart=always
RestartSec=3
WorkingDirectory=/pfad/zum/repo/Mini-CRCon-Bot4Discord
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Run: `sudo systemctl daemon-reload && sudo systemctl start mini-crcon-bot`.

---

## 🔁 Virtual Environments (Optional)
> [!IMPORTANT]
> Virtual environments (venv) prevent conflicts between Python packages and are recommended for advanced users. Here’s a detailed guide to installing and using Python 3.10, 3.11, or 3.12 with venv.

1. Install venv: `sudo apt install python3-venv -y`.
2. Create and activate:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies: `pip install -r requirements.txt`.
4. Start: `python bot.py`.
5. Deactivate: `deactivate`.

For other Python versions (e.g. 3.12):

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-distutils                    python3.11 python3.11-venv python3.11-distutils                    python3.12 python3.12-venv python3.12-distutils
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 💡 Usage
The bot runs in Discord and is controlled via buttons/menus (Kick, Punish, Map Switch, Switch Player and Messaging).

---

## 🗺 Roadmap
- [x] Player messaging system  
- [x] Optional: Extend panel with moderation actions (Kick, Punish, Map Switch, Switch Player)
- [ ] Multi-language support (`translations.json`)  

---

## License
This project is licensed under the **MIT License**.

---

## Contact
Created by **Fw.Schultz**. For questions or suggestions, please create an issue on GitHub.

📧 **Contact:** [Discord](https://discord.com/users/275297833970565121)
