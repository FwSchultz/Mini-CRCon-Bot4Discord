<div align="center">

  <img src="https://github.com/FwSchultz/assets/blob/main/bots/FwS-Bots/Bot.png" alt="logo" width="200" height="auto" />
  <h1>**Ein kleiner Mini Discord-Bot zur Verwaltung und Steuerung eines Hell Let Loose-Servers über das CRCON.**</h1>
  
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

[English version](readme.md)

</div>
<br />

## 📑 Inhaltsverzeichnis
- [Über das Projekt](#über-das-projekt)  
- [Technologie-Stack](#technologie-stack)  
- [Umgebungsvariablen & Tokens](#umgebungsvariablen--tokens)  
- [Voraussetzungen](#voraussetzungen)  
- [Erste Schritte](#erste-schritte)  
  - [Discord-Bot erstellen und Berechtigungen setzen](#discord-bot-erstellen-und-berechtigungen-setzen)  
  - [CRCON API-Token und Berechtigungen einrichten](#crcon-api-token-und-berechtigungen-einrichten)  
  - [Repository klonen](#repository-klonen)  
  - [Vorlagen (`dev.*`) in aktive Dateien kopieren](#vorlagen-dev-in-aktive-dateien-kopieren)  
  - [Konfigurationsdateien bearbeiten](#konfigurationsdateien-bearbeiten)  
  - [Abhängigkeiten installieren](#abhängigkeiten-installieren)  
  - [Bot starten](#bot-starten)  
- [Virtuelle Umgebungen (Optional)](#virtuelle-umgebungen-optional)  
- [Nutzung](#nutzung)  
- [Befehle](#befehle)  
- [Roadmap](#roadmap)  
- [Lizenz](#lizenz)  
- [Kontakt](#kontakt)  

---

## 🚀 Über das Projekt
Der **Mini-CRCON Bot** stellt ein Admin-Panel in Discord bereit, um einen Hell Let Loose Server über die CRCON-API zu steuern.

**Ziele:**
- Einfache Benutzeroberfläche für Admins und Moderatoren  
- Sichere, zuverlässige API-Kommunikation mit Wiederholungen und Fehlerbehandlung  
- Sauberes, minimalistisches Kontrollpanel im Discord-Kanal  

---

## 🛠 Technologie-Stack
- **Python** 3.10+  
- **discord.py** (Buttons, Modals, Selects, persistente Views)  
- **requests** (HTTP-Client mit Wiederholungen)  
- **PyYAML** (`config.yml` Konfiguration)  
- **python-dotenv** (`.env` Verwaltung von Zugangsdaten)  

---

## 🔑 Umgebungsvariablen & Tokens

Alle geheimen Daten werden in `.env` gespeichert:

```env
# Discord
DISCORD_TOKEN=DEIN_DISCORD_BOT_TOKEN
ADMIN_ROLE_IDS=111111111111111111,222222222222222222

# CRCON / API
API_BASE_URL=https://crcon.example.com
API_TOKEN=DEIN_CRCON_API_TOKEN

# Logging
LOG_LEVEL=INFO
```

---

## 📦 Voraussetzungen

Du benötigst Python 3.10 oder höher. Für Linux-Anfänger (Ubuntu/Debian-basierte Systeme):

```bash
sudo apt update && sudo apt install python3 python3-pip -y
```

Prüfe die Python-Version mit:

```bash
python3 --version
```

Falls die Version < 3.10 ist, siehe [Virtuelle Umgebungen (Optional)](#virtuelle-umgebungen-optional) für die Installation neuerer Versionen.

---

## ⚙️ Erste Schritte

Diese Anleitung ist für Linux-Anfänger mit wenig Erfahrung. Wir installieren das Script ohne virtuelle Umgebung (venv), um es einfach zu halten – venv ist optional. **Wichtig:** Ohne Discord- und CRCON-Tokens sowie korrekte Berechtigungen funktioniert der Bot nicht. Du musst `.env` und `config.yml` anpassen.

### 1) Discord-Bot erstellen und Berechtigungen setzen
- Gehe zum [Discord Developer Portal](https://discord.com/developers/applications).
- Erstelle eine **NEW APPLICATTION**, füge einen **Bot** hinzu.
- Aktiviere **Message Content Intent** (unter Bot > Privileged Gateway Intents).
- Reste den Token - über **Reset Token** Button (blauer Button)
- Kopiere den **Bot Token** und speichere ihn sicher – du brauchst ihn für die `.env`.
- Lade den Bot in deinen Server ein: Nutze den **Installation Button** (linke Spalte) dann unten Guild Install unter Scopes `bot` und `applications.commands`.
- Wähle diese **Permissions** (ohne sie funktioniert der Bot nicht richtig):
  - View Channels  
  - Send Messages  
  - Embed Links  
  - Attach Files (für den Banner vom Bot) 
  - Read Message History  
  - Manage Messages (damit der Bot den Kanal aufräumen kann; sonst löscht er nur eigene Nachrichten)  

### 2) [CRCON API-Token](https://github.com/MarechJ/hll_rcon_tool/wiki/Developer-Guides-%E2%80%90-CRCON-API)  und Berechtigungen einrichten
- Erstelle einen API-Token in deiner CRCON-Instanz (DJANGO) mit mindestens diesen Berechtigungen (sonst fehlen Funktionen)
  - `get_players` → api | rcon user | **Can view get_players endpoint** (name, steam ID, VIP status and sessions) for all connected players
  - `get_detailed_players` → api | rcon user | **Can view get_detailed_players endpoint**
  - `message_player` → api | rcon user | **Can message players**
  - `set_map` → api | rcon user | **Can change the current map**
  - `kick` → api | rcon user | **Can kick players**
  - `punish` → api | rcon user | **Can punish players**
  - `switch_player_now` → api | rcon user | **Can immediately switch players**
- Kopiere den Token und die Base-URL (z.B. https://crcon.example.com) – beide brauchst du für `.env`.


### 3) Repository klonen
Öffne ein Terminal und klone das Repo:

```bash
git clone https://github.com/FwSchultz/Mini-CRCon-Bot4Discord.git
cd Mini-CRCon-Bot4Discord
```

Falls git fehlt: `sudo apt install git -y`.

### 4) Vorlagen (`dev.*`) in aktive Dateien kopieren
Kopiere die Vorlagen:

```bash
cp dev.env .env
cp dev.config.yml config.yml
```

### 5) Konfigurationsdateien bearbeiten
- Öffne `.env` mit einem Editor (z.B. `nano .env` oder sogar im Texteditor):
  - Ersetze `DEIN_DISCORD_BOT_TOKEN` durch deinen Bot-Token.
  - Setze `CONTROL_CHANNEL_ID` auf die ID deines Discord-Kanals (Rechtsklick > **ID kopieren** vorab muss der Developer Mode im Discord aktivieren sein).
  - Setze `ADMIN_ROLE_IDS` auf die IDs deiner Admin-Rollen (kommagetrennt).
  - Ersetze `https://crcon.example.com` und `DEIN_CRCON_API_TOKEN` durch deine Werte.
- Öffne `config.yml` (z.B. `nano config.yml` oder sogar mit einem Texteditor) und passe an:

<details>
<summary>Config.yml anzeigen</summary>

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

### 6) Abhängigkeiten installieren
Installiere die Python-Pakete global (ohne venv):

```bash
pip3 install -r requirements.txt
```

Falls pip fehlt: `sudo apt install python3-pip -y`. Stelle sicher, dass `discord.py >= 2.2` installiert ist.

### 7) Bot starten
Starte den Bot:

```bash
python3 bot.py
```

Der Bot löscht nicht-gepinnte Nachrichten im Kontrollkanal und postet das Panel. Bei Fehlern setze `LOG_LEVEL=DEBUG` in `.env` für mehr Infos.

### (Optional) Als SystemD-Service laufen lassen
Für Dauerbetrieb erstelle `/etc/systemd/system/mini-crcon-bot.service`:

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

Führe aus: `sudo systemctl daemon-reload && sudo systemctl start mini-crcon-bot`.

---

## 🔁 Virtuelle Umgebungen (Optional)
> [!IMPORTANT]
> Virtuelle Umgebungen (venv) verhindern Konflikte zwischen Python-Paketen und sind für fortgeschrittene Nutzer empfohlen. Hier ist eine detaillierte Anleitung zur Installation und Nutzung von Python 3.10, 3.11 oder 3.12 mit venv.

1. Installiere venv: `sudo apt install python3-venv -y`.
2. Erstelle und aktiviere:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Installiere Abhängigkeiten: `pip install -r requirements.txt`.
4. Starte: `python bot.py`.
5. Deaktiviere: `deactivate`.

Für andere Python-Versionen (z.B. 3.12):

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-distutils \
                   python3.11 python3.11-venv python3.11-distutils \
                   python3.12 python3.12-venv python3.12-distutils
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 💡 Nutzung
Der Bot läuft in Discord und wird über Buttons/Menus gesteuert (Kick, Punish, Map-Switch, Switch Player und Nachrichten).

---

## 🗺 Roadmap
- [x] Spieler-Nachrichtensystem  
- [x] Optional: Panel mit Moderationsaktionen erweitern (Kick, Punish, Map Switch, Switch Player)
- [ ] Mehrsprachige Unterstützung (`translations.json`)  

---

## License
Dieses Projekt ist unter der **MIT License** lizenziert.

---

## Contact
Erstellt von **Fw.Schultz**. Bei Fragen oder Vorschlägen, bitte ein Issue auf GitHub erstellen.

📧 **Kontakt:** [Discord](https://discord.com/users/275297833970565121)
