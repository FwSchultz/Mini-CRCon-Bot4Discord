import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple

import discord
from discord.ext import commands
import yaml
from dotenv import load_dotenv

from views.message import MessageMainView

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("bot")

# Config laden
CFG_PATH = Path(os.getenv("CONFIG_PATH") or (BASE_DIR / "config.yml"))
try:
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f) or {}
except FileNotFoundError:
    _CFG = {}

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN fehlt in .env")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------------------------------------------------------
# (Optional) schlichtes Embed für das Panel
# -----------------------------------------------------------------------------
def make_embed(title: str, desc: Optional[str] = None, color: int = 0x2b2d31) -> discord.Embed:
    # Beschreibung = None (nicht discord.Embed.Empty), ist kompatibel mit allen lib-Versionen
    return discord.Embed(title=title, description=desc or None, color=color)

def build_panel_embed_and_banner(ui_cfg: dict) -> Tuple[discord.Embed, Optional[discord.File]]:
    """Erzeugt Embed + optionales Banner (lokal als Attachment *oder* per URL)."""
    title = ui_cfg.get("panel_title", "Steuerungs-Panel")
    intro = ui_cfg.get("panel_intro", "Wähle eine Aktion. Missbrauch führt zum Entzug von Rechten.")
    color = int(ui_cfg.get("panel_color", 0x2b2d31))
    embed = make_embed(title, intro, color)

    banner_cfg = ui_cfg.get("banner", {}) or {}
    if not banner_cfg.get("enabled", True):
        return embed, None

    # 1) Lokaler Pfad hat Vorrang
    path = str(banner_cfg.get("path") or "").strip()
    if path:
        abs_path = (BASE_DIR / path) if not os.path.isabs(path) else Path(path)
        if abs_path.is_file():
            filename = abs_path.name
            file = discord.File(str(abs_path), filename=filename)
            embed.set_image(url=f"attachment://{filename}")
            return embed, file
        else:
            logger.warning("Banner-Datei nicht gefunden: %s", abs_path)

    # 2) URL-Fallback
    url = str(banner_cfg.get("url") or "").strip()
    if url:
        embed.set_image(url=url)
        return embed, None

    return embed, None

# -----------------------------------------------------------------------------
# Purge-Helper
# -----------------------------------------------------------------------------
async def purge_control_channel(channel: discord.TextChannel) -> int:
    """Löscht alle nicht gepinnten Nachrichten im Channel.
    Nutzt bulk purge wenn erlaubt, sonst löscht nur eigene Nachrichten.
    """
    deleted_total = 0

    try:
        perms = channel.permissions_for(channel.guild.me)
    except Exception:
        me = channel.guild.get_member(channel._state.user.id)  # type: ignore
        perms = channel.permissions_for(me)

    if perms.manage_messages:
        def _check(m: discord.Message) -> bool:
            return not m.pinned
        while True:
            deleted = await channel.purge(limit=100, check=_check, bulk=True)
            deleted_total += len(deleted)
            if len(deleted) < 100:
                break
            await asyncio.sleep(0.3)
    else:
        me = channel.guild.me
        async for m in channel.history(limit=None):
            if not m.pinned and (m.author == me):
                try:
                    await m.delete()
                    deleted_total += 1
                except Exception:
                    pass

    logger.info("Control-Channel purged: %d Nachricht(en) gelöscht.", deleted_total)
    return deleted_total

# -----------------------------------------------------------------------------
# Log-Channel Helper (optional)
# -----------------------------------------------------------------------------
async def send_startup_log(guild: discord.Guild) -> None:
    """Schickt eine kleine Startmeldung in den optionalen Log-Channel."""
    log_chan_id = _CFG.get("app", {}).get("log_channel_id") or os.getenv("LOG_CHANNEL_ID")
    if not log_chan_id:
        return
    try:
        log_chan_id = int(log_chan_id)
    except Exception:
        logger.warning("LOG_CHANNEL_ID ungültig, überspringe Log-Ausgabe.")
        return

    channel = guild.get_channel(log_chan_id) or await bot.fetch_channel(log_chan_id)
    if not isinstance(channel, discord.TextChannel):
        logger.warning("Log-Channel ist kein TextChannel.")
        return

    e = make_embed("🤖 Bot gestartet", f"Guild: **{guild.name}**\nUser: **{bot.user}**")
    try:
        await channel.send(embed=e)
    except Exception as e:
        logger.warning("Konnte Log-Meldung nicht senden: %s", e)

# -----------------------------------------------------------------------------
# on_ready
# -----------------------------------------------------------------------------
@bot.event
async def on_ready():
    logger.info("Eingeloggt als %s (ID: %s)", bot.user, bot.user.id)

    # Persistente Views registrieren (falls gewünscht)
    if _CFG.get("app", {}).get("use_persistent_views", True):
        try:
            bot.add_view(MessageMainView())
        except Exception:
            # falls schon registriert
            pass

    # Control-Channel ermitteln
    control_channel_id = _CFG.get("app", {}).get("control_channel_id") or os.getenv("CONTROL_CHANNEL_ID")
    if not control_channel_id:
        logger.warning("Kein control_channel_id in config.yml/app.control_channel_id oder ENV CONTROL_CHANNEL_ID gesetzt. "
                       "Überspringe Panel-Bereitstellung.")
        return

    control_channel_id = int(control_channel_id)

    channel = bot.get_channel(control_channel_id)
    if channel is None:
        channel = await bot.fetch_channel(control_channel_id)  # type: ignore

    if not isinstance(channel, discord.TextChannel):
        logger.error("Channel %s ist kein TextChannel.", control_channel_id)
        return

    # Kanalinhalt löschen und Panel neu posten
    await purge_control_channel(channel)

    ui_cfg = _CFG.get("ui", {}) or {}
    embed, banner_file = build_panel_embed_and_banner(ui_cfg)

    if banner_file:
        await channel.send(embed=embed, file=banner_file, view=MessageMainView())
    else:
        await channel.send(embed=embed, view=MessageMainView())

    logger.info("Panel im Control-Channel bereitgestellt.")

    # Optional: Log-Channel benachrichtigen
    try:
        await send_startup_log(channel.guild)
    except Exception as e:
        logger.debug("Startup-Log übersprungen: %s", e)

# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    bot.run(TOKEN)
