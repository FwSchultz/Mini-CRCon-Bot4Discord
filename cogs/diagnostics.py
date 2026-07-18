# cogs/diagnostics.py
from __future__ import annotations
import logging
import discord
from discord.ext import commands
from api_client import diagnose
from utils.permissions import user_is_admin

logger = logging.getLogger("cog.diagnostics")


def _green_red_icon(ok: bool) -> str:
    return "🟢" if ok else "🔴"


def _extract_version_string(version_info: dict) -> str:
    """
    Erwartet diagnose()['version']-Struktur:
      { 'url': ..., 'status': 200, 'data': {...} }
    Typische Payload bei /api/get_version:
      data = { 'result': 'v11.5.2\\n', ... }
    """
    data = (version_info or {}).get("data")
    if isinstance(data, dict):
        val = data.get("result") or data.get("version") or ""
        if isinstance(val, str):
            s = val.strip()
            if s:
                return s
    return "—"


class DiagnosticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="diag",
        description="API-Diagnose (Erreichbarkeit, Version, Status, Spielerzahl)"
    )
    async def diag(self, ctx: commands.Context):
        if not user_is_admin(ctx.author):
            return await ctx.reply("⛔ Dafür fehlen dir die Rechte.", ephemeral=True if ctx.interaction else False)
        # Defer (bei Slash ephemer, bei Prefix normal)
        try:
            if ctx.interaction:
                await ctx.interaction.response.defer(ephemeral=True)
            else:
                await ctx.defer()
        except Exception:
            pass

        # Diagnose aus api_client
        try:
            info = diagnose()
        except Exception as e:
            logger.exception("Diagnose fehlgeschlagen: %s", e)
            if ctx.interaction:
                try:
                    await ctx.interaction.followup.send(
                        f"❌ Diagnose fehlgeschlagen: `{e}`", ephemeral=True
                    )
                except Exception:
                    pass
            else:
                try:
                    await ctx.reply(f"❌ Diagnose fehlgeschlagen: `{e}`")
                except Exception:
                    pass
            return

        emb = discord.Embed(title="CRCON API Diagnose", color=0x2b90d9)

        # Base URL
        emb.add_field(
            name="API Base URL",
            value=str(info.get("api_base_url") or "—"),
            inline=False
        )

        # Netzwerk
        net = info.get("network", {}) or {}
        if net.get("ok"):
            emb.add_field(
                name="Netzwerk",
                value=f"ok={net.get('ok')} • {net.get('host')}:{net.get('port')} • rtt={net.get('rtt_ms')}ms",
                inline=False
            )
        else:
            emb.add_field(
                name="Netzwerk",
                value=f"ok={net.get('ok')} • error={net.get('error')}",
                inline=False
            )

        # Version (nur die reine Versionsnummer)
        ver = info.get("version", {}) or {}
        version_str = _extract_version_string(ver)
        emb.add_field(name="Version", value=version_str, inline=True)

        # API Status → nur Icon
        api_ok = (ver.get("status") == 200)
        emb.add_field(name="API Status", value=_green_red_icon(api_ok), inline=True)

        # Aktuelle Spielerzahl → Icon nach Anzahl (0 = rot, >0 = grün)
        gp = info.get("get_players", {}) or {}
        count = 0
        try:
            count = int(gp.get("count") or 0)
        except Exception:
            count = 0
        players_ok = count > 0
        emb.add_field(
            name="Aktuelle Spielerzahl",
            value=f"{_green_red_icon(players_ok)} Spieler online {count}",
            inline=False
        )

        # Letzter Fehler aus dem HTTP-Client (falls vorhanden)
        if info.get("last_error"):
            le = str(info["last_error"])[:900]
            emb.add_field(name="Last Error", value=f"```{le}```", inline=False)

        # Antwort senden
        try:
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=emb, ephemeral=True)
            else:
                await ctx.reply(embed=emb)
        except Exception as e:
            logger.warning("Antwort fehlgeschlagen: %s", e)


async def setup(bot: commands.Bot):
    await bot.add_cog(DiagnosticsCog(bot))
