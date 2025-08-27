# bot.py
from __future__ import annotations
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple

import discord
from discord.ext import commands
import yaml
from dotenv import load_dotenv

from logging_setup import setup_logging  # <-- neu

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Logging (Datei + Konsole)
setup_logging()  # liest LOG_LEVEL aus .env
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

    path = str(banner_cfg.get("path") or "").strip()
    if path:
        abs_path = (BASE_DIR / path) if not os.path.isabs(path) else Path(path)
        if abs_path.is_file():
            filename = abs_path.name
            file = discord.File(str(abs_path), filename=filename)
            embed.set_image(url=f"attachment://{filename}")
            logger.debug("Panel-Banner (lokal) eingebunden: %s", abs_path)
            return embed, file
        else:
            logger.warning("Banner-Datei nicht gefunden: %s", abs_path)

    url = str(banner_cfg.get("url") or "").strip()
    if url:
        embed.set_image(url=url)
        logger.debug("Panel-Banner (URL) eingebunden: %s", url)
        return embed, None

    return embed, None

# -----------------------------------------------------------------------------
# Cog-Loader (lädt cogs/diagnostics.py & cogs/messaging.py, wenn vorhanden)
# -----------------------------------------------------------------------------
async def load_extensions():
    cogs_dir = BASE_DIR / "cogs"
    if not cogs_dir.exists():
        logger.debug("Kein cogs/ Verzeichnis gefunden – überspringe Cog-Load.")
        return

    for py in cogs_dir.glob("*.py"):
        stem = py.stem
        if stem == "__init__" or stem.startswith("_"):
            continue  # __init__ und Hidden-Dateien ignorieren
        name = f"cogs.{stem}"
        try:
            await bot.load_extension(name)
            logger.info("Cog geladen: %s", name)
        except Exception as e:
            logger.error("Cog %s konnte nicht geladen werden: %s", name, e)
# -----------------------------------------------------------------------------
# Log-Channel Helper (optional)
# -----------------------------------------------------------------------------
def _get_log_channel_id() -> Optional[int]:
    return int(_CFG.get("app", {}).get("log_channel_id") or os.getenv("LOG_CHANNEL_ID") or 0) or None

async def log_to_channel(guild: discord.Guild, *, title: str, desc: str = "", color: int = 0x2b2d31):
    log_chan_id = _get_log_channel_id()
    if not log_chan_id:
        return
    try:
        channel = guild.get_channel(log_chan_id) or await bot.fetch_channel(log_chan_id)
        if isinstance(channel, discord.TextChannel):
            e = make_embed(title, desc, color)
            await channel.send(embed=e)
    except Exception as e:
        logger.debug("Konnte nicht in Log-Channel schreiben: %s", e)

# -----------------------------------------------------------------------------
# Purge-Helper
# -----------------------------------------------------------------------------
async def purge_control_channel(channel: discord.TextChannel) -> int:
    """Löscht alle nicht gepinnten Nachrichten im Channel."""
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
# Fehler-Hooks → loggen & optional in Log-Channel spiegeln
# -----------------------------------------------------------------------------
@bot.event
async def on_error(event_method: str, *args, **kwargs):
    logger.exception("Ungefangene Exception in %s", event_method)
    # Optional in Log-Channel spiegeln (falls Guild ermittelbar)
    try:
        for g in bot.guilds:
            await log_to_channel(g, title="⚠️ Unbehandelter Fehler", desc=f"In `{event_method}` – siehe Logdatei.", color=0xED4245)
    except Exception:
        pass

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    logger.warning("Command-Fehler bei %s: %s", getattr(ctx, "command", None), error)
    try:
        await ctx.reply(f"⚠️ Fehler: `{error}`")
    except Exception:
        pass
    try:
        if ctx.guild:
            await log_to_channel(ctx.guild, title="⚠️ Command-Fehler", desc=str(error), color=0xED4245)
    except Exception:
        pass

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    logger.warning("Slash-Fehler: %s", error)
    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"⚠️ Fehler: `{error}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ Fehler: `{error}`", ephemeral=True)
    except Exception:
        pass
    try:
        if interaction.guild:
            await log_to_channel(interaction.guild, title="⚠️ Slash-Fehler", desc=str(error), color=0xED4245)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# on_ready
# -----------------------------------------------------------------------------
@bot.event
async def on_ready():
    logger.info("Eingeloggt als %s (ID: %s)", bot.user, bot.user.id)

    # Persistente Views registrieren (falls gewünscht)
    from views.message import MessageMainView  # nach Logging-Setup importieren
    if _CFG.get("app", {}).get("use_persistent_views", True):
        try:
            bot.add_view(MessageMainView())
        except Exception:
            pass

    # Cogs laden (damit /diag & /panel funktionieren)
    await load_extensions()
    try:
        # Optional: nur für diese/n Guild(s) syncen → schneller
        guild_ids = [g.id for g in bot.guilds]
        if guild_ids:
            for gid in guild_ids:
                await bot.tree.sync(guild=discord.Object(id=gid))
                logger.info("Slash-Commands mit Guild %s synchronisiert.", gid)
        else:
            await bot.tree.sync()
            logger.info("Slash-Commands global synchronisiert.")
    except Exception as e:
        logger.warning("Slash-Command Sync fehlgeschlagen: %s", e)

    # Control-Channel ermitteln
    control_channel_id = _CFG.get("app", {}).get("control_channel_id") or os.getenv("CONTROL_CHANNEL_ID")
    if not control_channel_id:
        logger.warning("Kein control_channel_id konfiguriert – überspringe Panel.")
        return

    control_channel_id = int(control_channel_id)
    channel = bot.get_channel(control_channel_id) or await bot.fetch_channel(control_channel_id)  # type: ignore
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
        if channel.guild:
            await log_to_channel(channel.guild, title="🤖 Bot gestartet", desc=f"Guild: **{channel.guild.name}**\nUser: **{bot.user}**", color=0x57F287)
    except Exception as e:
        logger.debug("Startup-Log übersprungen: %s", e)

# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    bot.run(TOKEN)
