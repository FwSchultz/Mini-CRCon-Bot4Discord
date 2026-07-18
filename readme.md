<div align="center">

  <img src="https://github.com/FwSchultz/assets/blob/main/bots/FwS-Bots/Bot.png" alt="Mini CRCON Bot Logo" width="200" height="auto" />
  <h1>Mini CRCON Bot for Discord</h1>

  <p>Discord-Steuerungsoberfläche für Hell-Let-Loose-Server über die CRCON-API.</p>

<p>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/graphs/contributors"><img src="https://img.shields.io/github/contributors/FwSchultz/Mini-CRCon-Bot4Discord" alt="contributors" /></a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/commits/main"><img src="https://img.shields.io/github/last-commit/FwSchultz/Mini-CRCon-Bot4Discord" alt="last update" /></a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/network/members"><img src="https://img.shields.io/github/forks/FwSchultz/Mini-CRCon-Bot4Discord" alt="forks" /></a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/stargazers"><img src="https://img.shields.io/github/stars/FwSchultz/Mini-CRCon-Bot4Discord" alt="stars" /></a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/issues"><img src="https://img.shields.io/github/issues/FwSchultz/Mini-CRCon-Bot4Discord" alt="issues" /></a>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/blob/main/LICENSE"><img src="https://img.shields.io/github/license/FwSchultz/Mini-CRCon-Bot4Discord.svg" alt="license" /></a>
</p>

<h4>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord">Documentation</a>
  <span> · </span>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/issues">Report Bug</a>
  <span> · </span>
  <a href="https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/issues">Request Feature</a>
</h4>
</div>

<br />

# Inhaltsverzeichnis

- [Über das Projekt](#über-das-projekt)
- [Funktionen](#funktionen)
- [Technik](#technik)
- [Projektstruktur](#projektstruktur)
- [Voraussetzungen](#voraussetzungen)
- [Konfiguration](#konfiguration)
- [Installation mit Docker Compose](#installation-mit-docker-compose)
- [Lokale Installation](#lokale-installation)
- [Discord-Befehle](#discord-befehle)
- [Berechtigungen](#berechtigungen)
- [CRCON-Berechtigungen](#crcon-berechtigungen)
- [Sicherheit](#sicherheit)
- [Roadmap](#roadmap)
- [Lizenz](#lizenz)
- [Kontakt](#kontakt)

---

## Über das Projekt

Der **Mini CRCON Bot for Discord** stellt ein dauerhaftes Steuerungs-Panel in Discord bereit. Berechtigte Administratoren können darüber Spieler benachrichtigen, Karten wechseln, Spieler kicken, bestrafen oder unmittelbar das Team wechseln lassen.

Die Kommunikation erfolgt über die HTTP-API einer bestehenden CRCON-Installation. Der Bot ersetzt CRCON nicht, sondern bietet eine kompakte Discord-Oberfläche für häufig benötigte Administrationsaufgaben.

---

## Funktionen

- Persistentes Discord-Steuerungs-Panel
- Nachricht an einzelne Spieler
- Nachricht an Allies, Axis oder alle Spieler
- Spielerauswahl mit Pagination
- Kartenwechsel anhand einer konfigurierbaren `maps.json`
- Spieler kicken, bestrafen und sofort ins andere Team verschieben
- API-Diagnose mit Erreichbarkeit, Version und Spielerzahl
- Rollen-, Benutzer-, Owner- und Administrator-Prüfung
- Wiederholungsversuche und Timeouts bei API-Aufrufen
- Rotierende Logdateien
- Optionales Panel-Banner
- Docker- und Docker-Compose-Unterstützung

---

## Technik

- **Python:** 3.12
- **Discord:** discord.py 2.4+
- **HTTP:** requests mit Retry-Strategie
- **Konfiguration:** YAML und Umgebungsvariablen
- **Deployment:** Docker und Docker Compose
- **Zielsystem:** Hell Let Loose CRCON API

---

## Projektstruktur

```text
Mini-CRCon-Bot4Discord/
├── assets/
├── cogs/
│   ├── diagnostics.py
│   └── messaging.py
├── utils/
│   └── permissions.py
├── views/
│   └── message.py
├── api_client.py
├── bot.py
├── logging_setup.py
├── maps.json
├── .env.example
├── config.example.yml
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Voraussetzungen

- Discord-Bot-Anwendung
- erreichbare CRCON-Installation mit API-Zugang
- Docker und Docker Compose, alternativ Python 3.12

Der Discord-Bot benötigt typischerweise:

- Kanäle ansehen
- Nachrichten senden
- Links einbetten
- Dateien anhängen
- Nachrichtenverlauf lesen
- Nachrichten verwalten, falls der Steuerungskanal beim Start bereinigt werden soll

---

## Konfiguration

Repository klonen:

```bash
git clone https://github.com/FwSchultz/Mini-CRCon-Bot4Discord.git
cd Mini-CRCon-Bot4Discord
```

Vorlagen kopieren:

```bash
cp .env.example .env
cp config.example.yml config.yml
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item config.example.yml config.yml
```

`.env` anpassen:

```env
DISCORD_TOKEN=DEIN_DISCORD_BOT_TOKEN
API_BASE_URL=https://crcon.example.com
API_TOKEN=DEIN_CRCON_API_TOKEN
CONFIG_PATH=config.yml
LOG_LEVEL=INFO
```

In `config.yml` mindestens Steuerungskanal und berechtigte Rollen eintragen:

```yaml
app:
  control_channel_id: 123456789012345678
  log_channel_id: 0
  purge_control_channel_on_start: true

permissions:
  allow_admin_perm: false
  allow_guild_owner: true
  role_ids:
    - 123456789012345678
  user_ids: []
```

Alle IDs in der Vorlage sind absichtlich leer oder `0`.

---

## Installation mit Docker Compose

```bash
docker compose up -d --build
```

Status und Logs:

```bash
docker compose ps
docker compose logs -f mini-crcon-bot
```

Stoppen:

```bash
docker compose down
```

Die Logdateien bleiben im lokalen Ordner `logs/` erhalten.

---

## Lokale Installation

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements.txt
python bot.py
```

---

## Discord-Befehle

| Befehl | Funktion |
|---|---|
| `/panel` | Steuerungs-Panel erneut senden |
| `/diag` | geschützte CRCON-API-Diagnose anzeigen |

Die eigentlichen Serveraktionen werden über Buttons, Auswahllisten und Dialoge im Panel ausgeführt.

---

## Berechtigungen

Zugriff erhält ein Benutzer, wenn mindestens eine aktivierte Regel zutrifft:

- explizite Benutzer-ID
- Discord-Serverbesitzer
- Discord-Berechtigung `Administrator`
- eine konfigurierte Rollen-ID

Für eine kontrollierte Einrichtung empfiehlt sich `allow_admin_perm: false` und die Freigabe über konkrete Rollen.

---

## CRCON-Berechtigungen

Der API-Token benötigt abhängig von den aktivierten Funktionen Zugriff auf:

- `get_players`
- `get_detailed_players`
- `message_player`
- `set_map`
- `kick`
- `punish`
- `switch_player_now`

Vergib nur die tatsächlich benötigten Rechte.

---

## Sicherheit

- `.env` und `config.yml` werden nicht versioniert.
- Tokens niemals in Screenshots, ZIP-Dateien oder Issues veröffentlichen.
- Das Diagnosekommando ist auf berechtigte Benutzer beschränkt.
- Der Steuerungskanal wird nur bereinigt, wenn `purge_control_channel_on_start` aktiviert ist.
- Bei Discord-Reconnects wird die Initialisierung nicht mehrfach ausgeführt.
- Administratorrechte nur vergeben, wenn einzelne Discord-Rechte nicht ausreichen.

---

## Roadmap

- [x] Persistentes Bedienpanel
- [x] Spieler- und Seitennachrichten
- [x] Kartenwechsel
- [x] Kick, Punish und Teamwechsel
- [x] Docker-Unterstützung
- [ ] Audit-Log für ausgeführte Adminaktionen
- [ ] Tests für API-Client und Rechteprüfung
- [ ] optionale Bestätigungsdialoge für kritische Aktionen

---

## Lizenz

Veröffentlicht unter der MIT-Lizenz. Weitere Informationen stehen in [LICENSE](LICENSE).

---

## Kontakt

**Fw.Schultz**

- GitHub: [@FwSchultz](https://github.com/FwSchultz)
- Website: [fwschultz.de](https://fwschultz.de)
- LinkedIn: [Oliver Blume](https://www.linkedin.com/in/oliver-blume)
- Fehler und Vorschläge: [GitHub Issues](https://github.com/FwSchultz/Mini-CRCon-Bot4Discord/issues)
