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
</div>

<br />

<!-- Table of Contents -->
---

## 📑 Table of Contents
- [About the Project](#about-the-project)  
- [Tech Stack](#tech-stack)  
- [Environment Variables & Tokens](#environment-variables--tokens)  
- [Requirements](#requirements)  
- [Getting Started](#getting-started)  
  - [Create a Discord Bot](#create-a-discord-bot)  
  - [Clone Repository](#clone-repository)  
  - [Copy Templates (`dev.*`) to Active Files](#copy-templates-dev-to-active-files)  
  - [Setup Virtual Environment](#setup-virtual-environment)  
  - [Run the Bot](#run-the-bot)  
- [Virtual Environments & Installing Extra Python Versions](#virtual-environments--installing-extra-python-versions)  
- [Usage](#usage)  
- [Commands](#commands)  
- [Roadmap](#roadmap)  
- [License](#license)  
- [Contact](#contact)  

---

## 🚀 About the Project
The **Mini-CRCON Bot** provides an admin panel inside Discord to interact with a running Hell Let Loose server via the CRCON API.

**Goals:**
- Simple UI for admins and moderators  
- Secure, reliable API communication with retries and error handling  
- Clean and minimal control panel channel in Discord  

---

## 🛠 Tech Stack
- **Python** 3.10+  
- **discord.py** (buttons, modals, selects, persistent views)  
- **requests** (HTTP client with retries)  
- **PyYAML** (`config.yml` configuration)  
- **python-dotenv** (`.env` credential management)  

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

### 🔐 Discord Bot Permissions
When creating your bot in the [Discord Developer Portal](https://discord.com/developers/applications):  

**Scopes**  
- `bot`  
- `applications.commands`  

**Bot Permissions**  
- ✅ View Channels  
- ✅ Send Messages  
- ✅ Embed Links  
- ✅ Attach Files (required if you send banners or images)  
- ✅ Read Message History  
- ✅ Manage Messages (required so the bot can clean up the panel channel; without it, it can only delete its own messages)  

---

### 🔐 CRCON API Permissions
Create the CRCON API token with at least these permissions:  

- `get_players` → api | rcon user | Can view get_players endpoint (name, steam ID, VIP status and sessions) for all connected players
- `get_detailed_players` → api | rcon user | Can view get_detailed_players endpoint
- `message_player` → api | rcon user | Can message players
- `set_map` → api | rcon user | Can change the current map
- `kick` → api | rcon user | Can kick players
- `punish` → api | rcon user | Can punish players
- `switch_player_now` → api | rcon user | Can immediately switch players 

---

## 📦 Requirements

```bash
sudo apt update && sudo apt install python3 python3-venv python3-pip -y
```

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip wheel
pip install -r requirements.txt
```

Ensure `discord.py >= 2.2` is installed.

---

## ⚙️ Getting Started

### 1) Create a Discord Bot
- Create an application in the Developer Portal, add a **Bot**, enable **Message Content Intent**, copy the **Bot Token**.  
- Invite the bot using scopes `bot` and `applications.commands` and the permissions listed above.

### 2) Clone Repository
```bash
git clone https://github.com/FwSchultz/Mini-CRCon-Bot4Discord
cd Discord-VIP-Exchanger
```

### 3) Copy Templates (`dev.*`) to Active Files
Use the provided development templates and rename them:

**Linux/macOS**
```bash
cp dev.env .env
cp dev.config.yml config.yml
```

**Windows (PowerShell)**
```powershell
Copy-Item dev.env .env
Copy-Item dev.config.yml config.yml
```

> Edit `.env` (tokens, channel IDs) and `config.yml` (UI text, panel title, feature toggles).

### 4) Setup Virtual Environment
Pick your installed Python version (examples below). Each line creates, activates, installs, and then deactivates:

```bash
python3.10 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
```

### 5) Run the Bot
```bash
# Linux/macOS
source venv/bin/activate
python bot.py
```

```powershell
# Windows PowerShell
.env\Scripts\Activate.ps1
python bot.py
```

On startup the bot will:
- Clear non‑pinned messages in the control channel  
- Post the **control panel** with buttons and menus  

### (Optional) Run as a Systemd Service
```ini
[Unit]
Description=Mini-CRCON Discord Bot
After=network.target

[Service]
User=botuser
WorkingDirectory=/home/botuser/mini-crcon
ExecStart=/home/botuser/mini-crcon/venv/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🔁 Virtual Environments & Installing Extra Python Versions

### Check your current Python versions
```bash
python3 -V
python3.10 -V  # if installed
python3.11 -V
python3.12 -V
```

### Ubuntu/Debian – Install additional versions (via deadsnakes)
```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-distutils                     python3.11 python3.11-venv python3.11-distutils                     python3.12 python3.12-venv python3.12-distutils
```

Create a venv with a specific version:
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -U pip wheel
pip install -r requirements.txt
```

Re-create venv after upgrading Python:
```bash
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Fedora/RHEL/CentOS
```bash
# Fedora
sudo dnf install -y python3.12 python3.12-pip python3.12-venv

# RHEL/CentOS (use EPEL or Software Collections as needed)
sudo yum install -y python3
```

### Windows
Use the **py launcher** to pick a version and create a venv:
```powershell
py -3.12 -m venv venv
.env\Scripts\Activate.ps1
pip install -U pip wheel
pip install -r requirements.txt
```

> Tip: Install multiple Windows Python versions from python.org; `py -0p` lists installed versions.

---

## 💡 Usage
The bot runs in Discord and is controlled via:  
- **Buttons & menus** (send messages to single players, allies, axis, or all)  
- **Slash commands** (e.g., `/panel`, `/diag`)  

---

## ⌨️ Commands
Control Panel buttons:
- **Message → One Player** (with pagination if >25 players)  
- **Message → Allies**  
- **Message → Axis**  
- **Message → All**  

---

## 🗺 Roadmap
- [x] Player messaging system  
- [x] API diagnostics command  
- [x] Extended moderation features (kick/ban/switch/map change from Discord panel)  
- [ ] Multilingual support (`translations.json`)  


---

## 📄 License
This project is licensed under the **MIT License**.

---

## 📬 Contact
Created by **Fw.Schultz**.  
For questions or suggestions, open a GitHub issue.  

📧 Discord: [Fw.Schultz](https://discord.com/users/275297833970565121)  
