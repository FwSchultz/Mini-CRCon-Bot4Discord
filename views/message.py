# views/message.py
import asyncio
import discord
from typing import List, Dict, Optional, Callable
import yaml
import os, json
import logging
logger = logging.getLogger("views.message")

from utils.permissions import user_is_admin
from api_client import (
    set_map,
    do_kick_player,
    do_punish_player,
    do_switch_player_now,   # Switch-API
    get_players,
    message_player,
    message_all,
    message_side,
    get_last_error,
)

# -----------------------------------------------------------------------------
# Farben / Embeds (kompatibel zu älterem discord.py)
# -----------------------------------------------------------------------------
ACCENT_COLOR  = 0x2b2d31
SUCCESS_COLOR = 0x43b581
DANGER_COLOR  = 0xed4245

def make_embed(title: str, desc: Optional[str] = None, color: int = ACCENT_COLOR) -> discord.Embed:
    # Kein discord.Embed.Empty nutzen → einfach None verwenden
    e = discord.Embed(title=title, description=(desc or None), color=color)
    return e

def _safe_excerpt(text: str, limit: int = 200) -> str:
    text = text or ""
    return (text[:limit] + "…") if len(text) > limit else text

# -----------------------------------------------------------------------------
# Config laden
# -----------------------------------------------------------------------------
try:
    with open("config.yml", "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f) or {}
except FileNotFoundError:
    _CFG = {}

# App: Log-Channel-ID (aus config oder ENV)
_app_cfg = _CFG.get("app", {}) or {}
_RAW_LOG_CH = _app_cfg.get("log_channel_id") or os.getenv("LOG_CHANNEL_ID") or None
try:
    LOG_CHANNEL_ID: Optional[int] = int(_RAW_LOG_CH) if _RAW_LOG_CH else None
except Exception:
    LOG_CHANNEL_ID = None

# Messaging
_MSG_CFG = _CFG.get("messaging", {}) or {}
EPHEMERAL_TTL_SECONDS = int(_MSG_CFG.get("ephemeral_ttl_seconds", 20))
MESSAGING_ENABLED = bool(_MSG_CFG.get("enabled", True))
_BTN_CFG = _MSG_CFG.get("buttons") or {}
BTN_ENABLE_SINGLE = bool(_BTN_CFG.get("single", True))
BTN_ENABLE_ALLIES = bool(_BTN_CFG.get("allies", True))
BTN_ENABLE_AXIS   = bool(_BTN_CFG.get("axis", True))
BTN_ENABLE_ALL    = bool(_BTN_CFG.get("all", True))
PAGE_SIZE = int(_MSG_CFG.get("page_size", 25))

# Map switch
_MAP_SWITCH_CFG = _CFG.get("map_switch", {}) or {}
MAP_SWITCH_ENABLED = bool(_MAP_SWITCH_CFG.get("enabled", False))
MAP_SWITCH_LABEL = str(_MAP_SWITCH_CFG.get("button_label", "Map wechseln"))
MAP_SWITCH_EPHEMERAL = bool(_MAP_SWITCH_CFG.get("ephemeral", False))
MAP_SWITCH_TTL_SECONDS = int(_MAP_SWITCH_CFG.get("ttl_seconds", 45))

# Kick/Punish + Switch Player
_KICK_CFG = _CFG.get("kick_player") or {}
_PUNISH_CFG = _CFG.get("punish_player") or {}
_SWITCH_CFG = _CFG.get("switch_player") or {}
KICK_ENABLED   = bool(_KICK_CFG.get("enable", False))
PUNISH_ENABLED = bool(_PUNISH_CFG.get("enable", False))
SWITCH_ENABLED = bool(_SWITCH_CFG.get("enable", False))

# --- Icons / Emoji -----------------------------------------------------------
_ICONS_CFG = (_CFG.get("ui", {}) or {}).get("icons", {}) or {}

def _icon(key: str, default: str) -> str:
    """Icon aus config.yml lesen, sonst Default."""
    try:
        val = _ICONS_CFG.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    except Exception:
        pass
    return default

# -----------------------------------------------------------------------------
# Logging in Discord-Log-Channel
# -----------------------------------------------------------------------------
async def _log(interaction: discord.Interaction, *, title: str, desc: str = "", color: int = ACCENT_COLOR,
               fields: Optional[List[tuple[str, str, bool]]] = None):
    """Sendet ein Embed in den konfigurierten Log-Channel (falls gesetzt)."""
    if not LOG_CHANNEL_ID:
        return
    try:
        ch = interaction.client.get_channel(LOG_CHANNEL_ID)
        if ch is None:
            ch = await interaction.client.fetch_channel(LOG_CHANNEL_ID)  # type: ignore
        if isinstance(ch, (discord.TextChannel, discord.Thread)):
            e = make_embed(title, desc, color)
            try:
                e.set_footer(text=f"by {interaction.user} • ID {interaction.user.id}")
            except Exception:
                pass
            if fields:
                for name, value, inline in fields:
                    e.add_field(name=name, value=value, inline=inline)
            await ch.send(embed=e)
    except Exception:
        # Logging darf UI nicht brechen
        pass

# -----------------------------------------------------------------------------
# Hilfsfunktionen: ephemer & auto-delete
# -----------------------------------------------------------------------------
async def _send_ephemeral_and_auto_delete(
    interaction: discord.Interaction, content: str, delay: int = EPHEMERAL_TTL_SECONDS
):
    await interaction.response.send_message(content, ephemeral=True)
    try:
        await asyncio.sleep(delay)
        await interaction.delete_original_response()
    except Exception:
        pass

async def _edit_ephemeral_and_auto_delete(
    interaction: discord.Interaction, content: str, delay: int = EPHEMERAL_TTL_SECONDS
):
    try:
        await interaction.edit_original_response(content=content, view=None)
        await asyncio.sleep(delay)
        await interaction.delete_original_response()
    except Exception:
        pass

async def _try_delete_message_later(msg: discord.Message, delay: int):
    try:
        await asyncio.sleep(delay)
        await msg.delete()
    except Exception:
        pass

# -----------------------------------------------------------------------------
# MAP SWITCH – Helpers & Views
# -----------------------------------------------------------------------------
_MAPS_CACHE = {"data": None, "mtime": 0.0}

def load_enabled_maps():
    path = "maps.json"
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}

    if _MAPS_CACHE["data"] is not None and _MAPS_CACHE["mtime"] == mtime:
        return _MAPS_CACHE["data"]

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f) or {}

    filtered = {k: v for k, v in data.items() if v.get("enabled")}
    groups = {}
    for key, meta in filtered.items():
        mode = meta.get("mode", "Other")
        label = meta.get("label", key)
        groups.setdefault(mode, []).append({"key": key, "label": label})
    for mode in groups:
        groups[mode].sort(key=lambda x: x["label"].lower())

    _MAPS_CACHE.update(data=groups, mtime=mtime)
    return groups

class AdminOnlyView(discord.ui.View):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        is_admin = user_is_admin(interaction.user)
        if not is_admin:
            try:
                await interaction.response.send_message("⛔ Dafür fehlen dir die Rechte.", ephemeral=True)
            except Exception:
                pass
        return is_admin

class MapModeButton(discord.ui.Button):
    def __init__(self, mode: str, count: int):
        super().__init__(label=f"{mode} ({count})", style=discord.ButtonStyle.primary)
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        view = MapSelectView(self.mode)
        await interaction.response.edit_message(
            content=f"**Map wählen:** {self.mode}",
            view=view
        )

class MapModeView(AdminOnlyView):
    def __init__(self):
        super().__init__(timeout=120)
        self.groups = load_enabled_maps()

        desired = ["Warfare", "Warfare Night", "Offensive", "Skirmish"]
        ordered = [m for m in desired if m in self.groups] + [m for m in self.groups if m not in desired]

        for mode in ordered:
            count = len(self.groups.get(mode, []))
            if count > 0:
                self.add_item(MapModeButton(mode, count))

        if not self.children:
            self.add_item(discord.ui.Button(
                label="Keine Karten gefunden (maps.json prüfen)",
                style=discord.ButtonStyle.secondary,
                disabled=True
            ))

class MapSelect(discord.ui.Select):
    def __init__(self, parent_view: "MapSelectView", options: List[discord.SelectOption]):
        super().__init__(placeholder="Map auswählen …", min_values=1, max_values=1, options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        label = self.parent_view.get_label(key)
        await interaction.response.edit_message(
            content=f"**Ausgewählt:** {self.parent_view.mode} → `{label}`\nBestätigen?",
            view=MapConfirmView(key, label)
        )

class MapSelectView(AdminOnlyView):
    def __init__(self, mode: str):
        super().__init__(timeout=180)
        self.mode = mode
        self.groups = load_enabled_maps()
        self.maps = self.groups.get(mode, [])
        self.page = 0
        self.page_size = 25
        self._rebuild()

    def get_label(self, key: str) -> str:
        for m in self.maps:
            if m["key"] == key:
                return m["label"]
        return key

    def _make_options(self, chunk: List[Dict[str, str]]) -> List[discord.SelectOption]:
        return [discord.SelectOption(label=m["label"], value=m["key"]) for m in chunk]

    def _rebuild(self):
        for child in list(self.children):
            if isinstance(child, (MapSelect, MapPagePrev, MapPageNext)):
                self.remove_item(child)
        start = self.page * self.page_size
        end = start + self.page_size
        chunk = self.maps[start:end]
        if not chunk:
            self.add_item(discord.ui.Button(
                label="Keine Maps in dieser Kategorie",
                style=discord.ButtonStyle.secondary,
                disabled=True
            ))
            return
        self.add_item(MapSelect(self, self._make_options(chunk)))
        if len(self.maps) > self.page_size:
            self.add_item(MapPagePrev(self))
            self.add_item(MapPageNext(self))

class MapPagePrev(discord.ui.Button):
    def __init__(self, owner: MapSelectView):
        super().__init__(style=discord.ButtonStyle.secondary, label="◀")
        self.owner = owner

    async def callback(self, interaction: discord.Interaction):
        if self.owner.page > 0:
            self.owner.page -= 1
            self.owner._rebuild()
            await interaction.response.edit_message(view=self.owner)
        else:
            await interaction.response.defer()

class MapPageNext(discord.ui.Button):
    def __init__(self, owner: MapSelectView):
        super().__init__(style=discord.ButtonStyle.secondary, label="▶")
        self.owner = owner

    async def callback(self, interaction: discord.Interaction):
        if (self.owner.page + 1) * self.owner.page_size < len(self.owner.maps):
            self.owner.page += 1
            self.owner._rebuild()
            await interaction.response.edit_message(view=self.owner)
        else:
            await interaction.response.defer()

class MapConfirmYes(discord.ui.Button):
    def __init__(self, owner: "MapConfirmView"):
        super().__init__(label="✅ Map jetzt setzen", style=discord.ButtonStyle.success)
        self.owner = owner  # <— eigener Verweis statt 'parent'

    async def callback(self, interaction: discord.Interaction):
        label = self.owner.label
        key = self.owner.map_key

        logger.debug("set_map requested by user=%s: key=%s label=%s",
                     getattr(interaction.user, "id", "?"), key, label)

        # 1) Sofort Status zeigen
        await interaction.response.edit_message(
            content=f"⏳ Setze Map: `{label}` (`{key}`) …",
            view=None
        )

        # 2) EINMAL Map setzen
        res = await asyncio.to_thread(set_map, key)
        ok = bool(res.get("ok")) if isinstance(res, dict) else ("ok" in str(res).lower())
        logger.debug("set_map result ok=%s res=%r", ok, res)

        # 3) Ergebnis
        if ok:
            final_text = f"🗺️ **Map gesetzt:** `{label}` (`{key}`)"
        else:
            err = res.get("error") if isinstance(res, dict) else str(res)[:900]
            final_text = f"❌ **Fehler beim Setzen der Map** `{label}`\n```{err}```"

        try:
            await interaction.message.edit(content=final_text, view=None)
        except Exception:
            pass

        if not MAP_SWITCH_EPHEMERAL and interaction.message:
            asyncio.create_task(_try_delete_message_later(interaction.message, MAP_SWITCH_TTL_SECONDS))

class MapConfirmNo(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Abbrechen", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Abgebrochen.", view=None)
        if not MAP_SWITCH_EPHEMERAL and interaction.message:
            asyncio.create_task(_try_delete_message_later(interaction.message, 10))

class MapConfirmView(AdminOnlyView):
    def __init__(self, map_key: str, label: str):
        super().__init__(timeout=60)
        self.map_key = map_key
        self.label = label
        self.add_item(MapConfirmYes(self))
        self.add_item(MapConfirmNo())

class MapSwitchButton(discord.ui.Button):
    def __init__(self, label: str = "Map wechseln"):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            row=1,
            custom_id="map_switch_open",
            emoji=_icon("panel_map", "🗺️"),
        )

    async def callback(self, interaction: discord.Interaction):
        logger.debug("map_switch_open by user=%s", getattr(interaction.user, "id", "?"))
        if not user_is_admin(interaction.user):
            return await interaction.response.send_message("⛔ Dafür fehlen dir die Rechte.", ephemeral=True)

        groups = load_enabled_maps()
        if not groups:
            return await interaction.response.send_message(
                "❌ Keine Karten gefunden. Prüfe `maps.json` oder die `enabled`-Flags.", ephemeral=True
            )

        await interaction.response.send_message(
            content="**Map wechseln** → wähle zuerst einen Modus:",
            view=MapModeView(),
            ephemeral=MAP_SWITCH_EPHEMERAL
        )

        if not MAP_SWITCH_EPHEMERAL:
            try:
                msg = await interaction.original_response()
                asyncio.create_task(_try_delete_message_later(msg, MAP_SWITCH_TTL_SECONDS))
            except Exception:
                pass

# -----------------------------------------------------------------------------
# Player Picker (generisch)
# -----------------------------------------------------------------------------
class PlayerSelect(discord.ui.Select):
    def __init__(self, parent_view: "PlayerPickerView", options: List[discord.SelectOption]):
        self.parent_view = parent_view
        super().__init__(min_values=1, max_values=1, placeholder="Spieler auswählen…", options=options)

    async def callback(self, interaction: discord.Interaction):
        values = self.values or []
        if not values:
            return await interaction.response.defer()
        steam_id, name = values[0].split("|", 1)
        player = next((p for p in self.parent_view.players if str(p.get("steam_id_64")) == steam_id), None)
        if player is None:
            player = {"steam_id_64": steam_id, "name": name}

        if callable(self.parent_view.on_selected):
            # origin_interaction für spätere Löschung (Dropdown) durchreichen
            return await self.parent_view.on_selected(interaction, player, self.parent_view.origin_interaction)

        modal = MessageModalSingle(parent_message=interaction.message, target_name=name, target_id=steam_id)
        await interaction.response.send_modal(modal)

class PlayerPickerView(discord.ui.View):
    def __init__(self, page_size: int = PAGE_SIZE, on_selected: Optional[Callable] = None):
        super().__init__(timeout=120)
        self.page_size = page_size
        self.page = 0
        self.players: List[Dict] = []
        self.select: Optional[PlayerSelect] = None
        self.on_selected = on_selected
        self.origin_interaction: Optional[discord.Interaction] = None  # <- wichtig

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True

    def _make_options(self, chunk: List[Dict]) -> List[discord.SelectOption]:
        opts = []
        for p in chunk:
            label = p.get("name") or "?"
            value = f"{p.get('steam_id_64')}|{p.get('name')}"
            description = "VIP" if p.get("is_vip") else None
            opts.append(discord.SelectOption(label=label, value=value, description=description))
        return opts

    def _refresh_components(self):
        for child in list(self.children):
            if isinstance(child, PlayerSelect):
                self.remove_item(child)
        start = self.page * self.page_size
        end = start + self.page_size
        chunk = self.players[start:end]
        options = self._make_options(chunk)
        self.select = PlayerSelect(self, options)
        self.add_item(self.select)

    async def load_players(self):
        players = await asyncio.to_thread(get_players)
        logger.debug("loaded %d players", len(players))
        self.players = sorted(players, key=lambda p: (-int(p.get("is_vip") or 0), str(p.get("name") or "")))
        if self.players:
            self._refresh_components()

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, _):
        if self.page > 0:
            self.page -= 1
            self._refresh_components()
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, _):
        max_page = (max(len(self.players) - 1, 0)) // self.page_size
        if self.page < max_page:
            self.page += 1
            self._refresh_components()
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.defer()

# -----------------------------------------------------------------------------
# Kick / Punish / Switch Modals & Buttons
# -----------------------------------------------------------------------------
class KickModal(discord.ui.Modal):
    def __init__(self, player_name: str, steam_id: str,
                 parent_message: Optional[discord.Message] = None,
                 origin_interaction: Optional[discord.Interaction] = None):
        super().__init__(title=f"Kick {player_name}")
        self.player_name = player_name
        self.steam_id = steam_id
        self.parent_message = parent_message
        self.origin_interaction = origin_interaction
        self.reason_input = discord.ui.TextInput(label="Grund", style=discord.TextStyle.long, required=True)
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        logger.debug("kick submit by=%s target=%s (%s)", getattr(interaction.user,"id","?"),
                     self.player_name, self.steam_id)
        # Dropdown schließen
        try:
            if self.origin_interaction:
                await self.origin_interaction.delete_original_response()
        except Exception:
            pass

        reason = str(self.reason_input.value).strip()
        await interaction.response.send_message("⏳ Kicke Spieler …", ephemeral=True)
        try:
            await asyncio.to_thread(do_kick_player, self.player_name, self.steam_id, reason)
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"✅ **{self.player_name}** wurde gekickt.\nGrund: {reason}", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="👢 Kick",
                desc=f"**{self.player_name}** wurde gekickt.",
                color=SUCCESS_COLOR,
                fields=[
                    ("SteamID64", f"`{self.steam_id}`", True),
                    ("Grund", _safe_excerpt(reason, 300) or "—", False),
                ],
            )
        except Exception as e:
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"❌ Kick fehlgeschlagen für **{self.player_name}**: {e}", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="❌ Kick fehlgeschlagen",
                desc=f"**{self.player_name}**",
                color=DANGER_COLOR,
                fields=[("Fehler", _safe_excerpt(str(e), 400), False)],
            )

class PunishModal(discord.ui.Modal):
    def __init__(self, player_name: str,
                 parent_message: Optional[discord.Message] = None,
                 origin_interaction: Optional[discord.Interaction] = None):
        super().__init__(title=f"Bestrafen {player_name}")
        self.player_name = player_name
        self.parent_message = parent_message
        self.origin_interaction = origin_interaction
        self.reason_input = discord.ui.TextInput(label="Grund", style=discord.TextStyle.long, required=True)
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        logger.debug("punish submit by=%s target=%s (%s)", getattr(interaction.user,"id","?"), self.player_name)
        try:
            if self.origin_interaction:
                await self.origin_interaction.delete_original_response()
        except Exception:
            pass

        reason = str(self.reason_input.value).strip()
        by_user = interaction.user.display_name if hasattr(interaction.user, "display_name") else str(interaction.user)
        await interaction.response.send_message("⏳ Strafe wird eingetragen …", ephemeral=True)
        try:
            await asyncio.to_thread(do_punish_player, self.player_name, reason, by_user)
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"✅ Strafe für **{self.player_name}** erfasst.\nGrund: {reason}", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="🧾 Punish",
                desc=f"Strafe für **{self.player_name}** erfasst.",
                color=SUCCESS_COLOR,
                fields=[("Grund", _safe_excerpt(reason, 300) or "—", False)],
            )
        except Exception as e:
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"❌ Bestrafung fehlgeschlagen für **{self.player_name}**: {e}", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="❌ Punish fehlgeschlagen",
                desc=f"**{self.player_name}**",
                color=DANGER_COLOR,
                fields=[("Fehler", _safe_excerpt(str(e), 400), False)],
            )

class SwitchPlayerModal(discord.ui.Modal):
    def __init__(self, player_name: str,
                 parent_message: Optional[discord.Message] = None,
                 origin_interaction: Optional[discord.Interaction] = None):
        super().__init__(title=f"Switch {player_name}")
        self.player_name = player_name
        self.parent_message = parent_message
        self.origin_interaction = origin_interaction
        self.info = discord.ui.TextInput(
            label="Bestätigung",
            style=discord.TextStyle.short,
            required=False,
            placeholder="Optionaler Hinweis (z.B. Grund)"
        )
        self.add_item(self.info)

    async def on_submit(self, interaction: discord.Interaction):
        logger.debug("switch submit by=%s target=%s (%s)", getattr(interaction.user,"id","?"), self.player_name)
        try:
            if self.origin_interaction:
                await self.origin_interaction.delete_original_response()
        except Exception:
            pass

        note = str(self.info.value or "").strip()
        await interaction.response.send_message("⏳ Spieler wird geswitcht …", ephemeral=True)
        try:
            ok = await asyncio.to_thread(do_switch_player_now, self.player_name)
            if ok:
                asyncio.create_task(_edit_ephemeral_and_auto_delete(
                    interaction, f"✅ **{self.player_name}** wurde geswitcht.", EPHEMERAL_TTL_SECONDS
                ))
                await _log(
                    interaction,
                    title="🔀 Switch Player",
                    desc=f"**{self.player_name}** wurde geswitcht.",
                    color=SUCCESS_COLOR,
                    fields=[("Hinweis", _safe_excerpt(note, 300) or "—", False)] if note else None,
                )
            else:
                asyncio.create_task(_edit_ephemeral_and_auto_delete(
                    interaction, f"❌ Switch fehlgeschlagen für **{self.player_name}**.", EPHEMERAL_TTL_SECONDS
                ))
                await _log(
                    interaction,
                    title="❌ Switch fehlgeschlagen",
                    desc=f"**{self.player_name}**",
                    color=DANGER_COLOR,
                )
        except Exception as e:
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"❌ Switch fehlgeschlagen für **{self.player_name}**: {e}", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="❌ Switch fehlgeschlagen",
                desc=f"**{self.player_name}**",
                color=DANGER_COLOR,
                fields=[("Fehler", _safe_excerpt(str(e), 400), False)],
            )

# Buttons (Hauptmenü)
class KickButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Kick",
            style=discord.ButtonStyle.danger,
            custom_id="kick_player",
            row=0,
            emoji=_icon("panel_kick", "🔨"),
        )

    async def callback(self, interaction: discord.Interaction):
        logger.debug("kick flow started by user=%s", getattr(interaction.user, "id", "?"))
        if not user_is_admin(interaction.user):
            return await interaction.response.send_message("⛔ Dafür fehlen dir die Rechte.", ephemeral=True)
        await interaction.response.send_message(
            embed=make_embed("⏳ Lade Spielerliste …", "", ACCENT_COLOR), ephemeral=True
        )

        picker = PlayerPickerView(on_selected=self._on_selected)
        picker.origin_interaction = interaction  # <- wichtig für späteres Löschen
        await picker.load_players()

        if not picker.players:
            detail = get_last_error() or "Keine Spieler online."
            return await interaction.edit_original_response(
                content=f"❌ Keine Spieler gefunden. Hinweis: {detail}", view=None
            )

        await interaction.edit_original_response(content="Wähle den Spieler zum Kicken:", view=picker)

    async def _on_selected(self, interaction: discord.Interaction, player: Dict,
                           origin_inter: Optional[discord.Interaction]):
        modal = KickModal(
            player_name=player["name"],
            steam_id=str(player["steam_id_64"]),
            parent_message=interaction.message,
            origin_interaction=origin_inter
        )
        await interaction.response.send_modal(modal)

class PunishButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Punish",
            style=discord.ButtonStyle.secondary,
            custom_id="punish_player",
            row=0,
            emoji=_icon("panel_punish", "⚠️"),
        )

    async def callback(self, interaction: discord.Interaction):
        logger.debug("punish flow started by user=%s", getattr(interaction.user, "id", "?"))
        if not user_is_admin(interaction.user):
            return await interaction.response.send_message("⛔ Dafür fehlen dir die Rechte.", ephemeral=True)
        await interaction.response.send_message(
            embed=make_embed("⏳ Lade Spielerliste …", "", ACCENT_COLOR), ephemeral=True
        )

        picker = PlayerPickerView(on_selected=self._on_selected)
        picker.origin_interaction = interaction
        await picker.load_players()

        if not picker.players:
            detail = get_last_error() or "Keine Spieler online."
            return await interaction.edit_original_response(
                content=f"❌ Keine Spieler gefunden. Hinweis: {detail}", view=None
            )

        await interaction.edit_original_response(content="Wähle den Spieler für Punish:", view=picker)

    async def _on_selected(self, interaction: discord.Interaction, player: Dict,
                           origin_inter: Optional[discord.Interaction]):
        modal = PunishModal(
            player_name=player["name"],
            parent_message=interaction.message,
            origin_interaction=origin_inter
        )
        await interaction.response.send_modal(modal)

class SwitchPlayerButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Switch Player",
            style=discord.ButtonStyle.primary,
            custom_id="switch_player",
            row=0,
            emoji=_icon("panel_switch", "🔁"),
        )

    async def callback(self, interaction: discord.Interaction):
        logger.debug("switch flow started by user=%s", getattr(interaction.user, "id", "?"))
        if not user_is_admin(interaction.user):
            return await interaction.response.send_message("⛔ Dafür fehlen dir die Rechte.", ephemeral=True)
        await interaction.response.send_message(
            embed=make_embed("⏳ Lade Spielerliste …", "", ACCENT_COLOR), ephemeral=True
        )

        picker = PlayerPickerView(on_selected=self._on_selected)
        picker.origin_interaction = interaction
        await picker.load_players()

        if not picker.players:
            detail = get_last_error() or "Keine Spieler online."
            return await interaction.edit_original_response(
                content=f"❌ Keine Spieler gefunden. Hinweis: {detail}", view=None
            )

        await interaction.edit_original_response(content="Wähle den Spieler zum Switchen:", view=picker)

    async def _on_selected(self, interaction: discord.Interaction, player: Dict,
                           origin_inter: Optional[discord.Interaction]):
        modal = SwitchPlayerModal(
            player_name=player["name"],
            parent_message=interaction.message,
            origin_interaction=origin_inter
        )
        await interaction.response.send_modal(modal)

# -----------------------------------------------------------------------------
# Haupt-/Submenu Views
# -----------------------------------------------------------------------------
class MessageMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # persistent

        if MAP_SWITCH_ENABLED:
            self.add_item(MapSwitchButton(MAP_SWITCH_LABEL))
        if KICK_ENABLED:
            self.add_item(KickButton())
        if PUNISH_ENABLED:
            self.add_item(PunishButton())
        if SWITCH_ENABLED:
            self.add_item(SwitchPlayerButton())

    @discord.ui.button(
        label="Nachricht",
        style=discord.ButtonStyle.primary,
        custom_id="msg_main",
        row=1,
        emoji=_icon("panel_message", "💬"),
    )
    async def open_submenu(self, interaction: discord.Interaction, _):
        if not MESSAGING_ENABLED:
            return await _send_ephemeral_and_auto_delete(
                interaction, "❌ Der Bereich **Nachrichten** ist derzeit deaktiviert."
            )
        await interaction.response.edit_message(content="Wähle eine Zielgruppe:", view=MessageSubmenuView())

class MessageSubmenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)

        hidden_ids = set()
        if not BTN_ENABLE_SINGLE: hidden_ids.add("msg_to_one")
        if not BTN_ENABLE_ALLIES: hidden_ids.add("msg_to_allies")
        if not BTN_ENABLE_AXIS:   hidden_ids.add("msg_to_axis")
        if not BTN_ENABLE_ALL:    hidden_ids.add("msg_to_all")

        def _prune_buttons(view: "MessageSubmenuView"):
            for child in list(view.children):
                if isinstance(child, discord.ui.Button):
                    if getattr(child, "custom_id", None) in hidden_ids:
                        view.remove_item(child)
        self._deferred_prune = _prune_buttons

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if hasattr(self, "_deferred_prune") and callable(self._deferred_prune):
            try:
                self._deferred_prune(self)
            finally:
                self._deferred_prune = None
        return True

    @discord.ui.button(
        label="An EINEN Spieler",
        style=discord.ButtonStyle.primary,
        custom_id="msg_to_one",
        emoji=_icon("msg_one", "👤"),
    )
    async def to_one(self, interaction: discord.Interaction, _):
        await interaction.response.send_message(
            embed=make_embed("⏳ Lade Spielerliste …", "", ACCENT_COLOR), ephemeral=True
        )
        picker = PlayerPickerView()  # Default-Action = Nachricht senden
        await picker.load_players()

        if not picker.players:
            detail = get_last_error() or "Keine Spieler online."
            await interaction.edit_original_response(content=f"❌ Keine Spieler gefunden. Hinweis: {detail}", view=None)
            return

        # Anzeige im Panel (nicht ephemer)
        try:
            await interaction.message.edit(content="Wähle den Spieler:", view=picker)
        except Exception:
            await interaction.followup.send("Wähle den Spieler:", view=picker, ephemeral=True)

        try:
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, "✅ Spielerliste geladen.", EPHEMERAL_TTL_SECONDS
            ))
        except Exception:
            pass

    @discord.ui.button(
        label="An ALLIES",
        style=discord.ButtonStyle.success,
        custom_id="msg_to_allies",
        emoji=_icon("msg_allies", "🔵"),
    )
    async def to_allies(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(MessageModalSide(parent_message=interaction.message, side="allies"))

    @discord.ui.button(
        label="An AXIS",
        style=discord.ButtonStyle.danger,
        custom_id="msg_to_axis",
        emoji=_icon("msg_axis", "🔴"),
    )
    async def to_axis(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(MessageModalSide(parent_message=interaction.message, side="axis"))

    @discord.ui.button(
        label="An ALLE",
        style=discord.ButtonStyle.primary,
        custom_id="msg_to_all",
        emoji=_icon("msg_all", "📣"),
    )
    async def to_all(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(MessageModalAll(parent_message=interaction.message))

    @discord.ui.button(
        label="Zurück",
        style=discord.ButtonStyle.danger,
        custom_id="msg_back",
        emoji=_icon("back", "↩️"),
    )
    async def back(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(content="Steuerungs-Panel", view=MessageMainView())

# -----------------------------------------------------------------------------
# Modals: Messaging (mit Logging)
# -----------------------------------------------------------------------------
class MessageModalSingle(discord.ui.Modal, title="Nachricht an Spieler"):
    def __init__(self, target_name: str, target_id: str, parent_message: Optional[discord.Message] = None):
        super().__init__()
        self.target_name = target_name
        self.target_id = target_id
        self.parent_message = parent_message
        self.msg_input = discord.ui.TextInput(
            label=f"Nachricht an {target_name}", style=discord.TextStyle.long, required=True
        )
        self.add_item(self.msg_input)

    async def on_submit(self, interaction: discord.Interaction):
        msg = str(self.msg_input.value).strip()
        await interaction.response.send_message("⏳ Sende Nachricht …", ephemeral=True)
        try:
            await asyncio.to_thread(message_player, self.target_name, self.target_id, msg)
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"✅ Nachricht an **{self.target_name}** gesendet.\n„{msg}“", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="✉️ PM an Spieler",
                desc=f"**{self.target_name}** (`{self.target_id}`)",
                color=SUCCESS_COLOR,
                fields=[("Inhalt", _safe_excerpt(msg, 400) or "—", False)],
            )
        except Exception as e:
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"❌ Nachricht an **{self.target_name}** fehlgeschlagen: {e}", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="❌ PM fehlgeschlagen",
                desc=f"**{self.target_name}** (`{self.target_id}`)",
                color=DANGER_COLOR,
                fields=[("Fehler", _safe_excerpt(str(e), 400), False)],
            )
        try:
            if self.parent_message:
                await self.parent_message.edit(content="Wähle eine Zielgruppe:", view=MessageSubmenuView())
            elif interaction.message:
                await interaction.message.edit(content="Wähle eine Zielgruppe:", view=MessageSubmenuView())
        except Exception:
            pass

class MessageModalSide(discord.ui.Modal):
    def __init__(self, side: str, parent_message: Optional[discord.Message] = None):
        super().__init__(title=f"Nachricht an {side.upper()}")
        self.side = side
        self.parent_message = parent_message
        self.msg_input = discord.ui.TextInput(label="Nachricht", style=discord.TextStyle.long, required=True)
        self.add_item(self.msg_input)

    async def on_submit(self, interaction: discord.Interaction):
        msg = str(self.msg_input.value).strip()
        await interaction.response.send_message("⏳ Sende Nachricht …", ephemeral=True)
        try:
            res = await asyncio.to_thread(message_side, self.side, msg)
            if isinstance(res, dict) and res.get("ok"):
                count = res.get("count")
                suffix = f" ({count} Spieler)" if count is not None else ""
                asyncio.create_task(_edit_ephemeral_and_auto_delete(
                    interaction, f"✅ Nachricht an **{self.side.upper()}** gesendet{suffix}.\n„{msg}“",
                    EPHEMERAL_TTL_SECONDS
                ))
                await _log(
                    interaction,
                    title="📣 Nachricht an Seite",
                    desc=f"**{self.side.upper()}**",
                    color=SUCCESS_COLOR,
                    fields=[("Inhalt", _safe_excerpt(msg, 400) or "—", False),
                            ("Anzahl", str(count) if count is not None else "—", True)],
                )
            else:
                err = res.get('error','Unbekannter Fehler') if isinstance(res, dict) else str(res)
                asyncio.create_task(_edit_ephemeral_and_auto_delete(
                    interaction, f"❌ Nachricht an **{self.side.upper()}** fehlgeschlagen: {err}",
                    EPHEMERAL_TTL_SECONDS
                ))
                await _log(
                    interaction,
                    title="❌ Nachricht an Seite fehlgeschlagen",
                    desc=f"**{self.side.upper()}**",
                    color=DANGER_COLOR,
                    fields=[("Fehler", _safe_excerpt(str(err), 400), False)],
                )
        except Exception as e:
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"❌ Nachricht an **{self.side.upper()}** fehlgeschlagen: {e}", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="❌ Nachricht an Seite fehlgeschlagen",
                desc=f"**{self.side.upper()}**",
                color=DANGER_COLOR,
                fields=[("Fehler", _safe_excerpt(str(e), 400), False)],
            )
        try:
            if self.parent_message:
                await self.parent_message.edit(content="Wähle eine Zielgruppe:", view=MessageSubmenuView())
            elif interaction.message:
                await interaction.message.edit(content="Wähle eine Zielgruppe:", view=MessageSubmenuView())
        except Exception:
            pass

class MessageModalAll(discord.ui.Modal, title="Nachricht an ALLE"):
    def __init__(self, parent_message: Optional[discord.Message] = None):
        super().__init__()
        self.parent_message = parent_message
        self.msg_input = discord.ui.TextInput(label="Nachricht", style=discord.TextStyle.long, required=True)
        self.add_item(self.msg_input)

    async def on_submit(self, interaction: discord.Interaction):
        msg = str(self.msg_input.value).strip()
        await interaction.response.send_message("⏳ Sende Nachricht …", ephemeral=True)
        try:
            res = await asyncio.to_thread(message_all, msg)
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"✅ Nachricht an **ALLE** gesendet.\n„{msg}“", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="📢 Nachricht an ALLE",
                desc=f"Erfolgreich gesendet.",
                color=SUCCESS_COLOR,
                fields=[("Inhalt", _safe_excerpt(msg, 400) or "—", False),
                        ("Versendet", str(res.get('count')) if isinstance(res, dict) else "—", True)],
            )
        except Exception as e:
            asyncio.create_task(_edit_ephemeral_and_auto_delete(
                interaction, f"❌ Nachricht an **ALLE** fehlgeschlagen: {e}", EPHEMERAL_TTL_SECONDS
            ))
            await _log(
                interaction,
                title="❌ Nachricht an ALLE fehlgeschlagen",
                desc="—",
                color=DANGER_COLOR,
                fields=[("Fehler", _safe_excerpt(str(e), 400), False)],
            )
        try:
            if self.parent_message:
                await self.parent_message.edit(content="Wähle eine Zielgruppe:", view=MessageSubmenuView())
            elif interaction.message:
                await interaction.message.edit(content="Wähle eine Zielgruppe:", view=MessageSubmenuView())
        except Exception:
            pass
