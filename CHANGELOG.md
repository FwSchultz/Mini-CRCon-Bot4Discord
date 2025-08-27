# Changelog

## [v1.3.0] - 2025-08-26
### Added
- **!diag**: Neues, kompaktes Status‑Embed
  - **API Status** mit Ampel‑Icon (🟢/🔴) je nach HTTP‑Erreichbarkeit.
  - **API Version** aus `/api/get_version` (z. B. `v11.5.2`).
  - **Aktuelle Spielerzahl** als klare Anzeige (🔴 „Spieler online 0“ / 🟢 „Spieler online N“).
- **Control‑Panel**: Embed‑Banner (lokale Datei *oder* URL) kann angezeigt werden.
- **Persistente Views**: `MessageMainView` wird beim Start registriert, damit Buttons nach einem Neustart weiterhin funktionieren.
- **Logging‑Verbesserungen**:
  - Zentrales `logging_setup` mit Level aus `.env`.
  - Fehler‑Hooks spiegeln Ausnahmen optional in den Log‑Channel.

### Changed
- **Versions‑Erkennung**: Diagnose benutzt nun zuerst `/api/get_version` (Fallbacks vorhanden).
- **Diag‑Embed**: Felder umbenannt/vereinfacht („API Status“, „API Version“, „Aktuelle Spielerzahl“).

### Fixed
- **Robustere API‑Erkennung** in der Diagnose (TCP‑Check + intelligente Endpoint‑Suche).
- **Control‑Channel purge**: Löscht zuverlässig alle ungepinnten Nachrichten vor dem Panel‑Post.
- **Views/Message**: Diverse Guard‑Checks & kleinere Stabilitätsfixes in Selects/Buttons/Modals.

### Config
- `.env`: `API_BASE_URL`, `API_TOKEN`, `LOG_LEVEL` u. a.
- `config.yml`:
  - `app.control_channel_id`, optional `app.log_channel_id`
  - `messaging.*` (Buttons, `page_size`, ephemere TTL)
  - `map_switch.*` (aktivierbar, Label, TTL)
  - `ui.icons.*` für Emojis/Icons

### Developer
- **`api_client`**:
  - Gemeinsame `requests.Session` mit Retry‑Strategie.
  - Einheitliche Fehlerprotokollierung (`_LAST_ERROR`) und `diagnose()`‑Summary.
  - Neue Helfer: `try_endpoints()`, `get_detailed_players()`, `message_side()`.
- **`bot.py`**:
  - Cogs‑Loader, Guild‑scoped Slash‑Sync, Panel‑Banner‑Support.
  - Persistente Views & sauberer Startup‑Log.

---

