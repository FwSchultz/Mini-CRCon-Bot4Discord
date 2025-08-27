# cogs/messaging.py
from __future__ import annotations
import logging
import os
import yaml
import discord
from discord.ext import commands
from views.message import MessageMainView
from utils.permissions import user_is_admin

logger = logging.getLogger("cog.messaging")

CONTROL_CHANNEL_ID = int(os.getenv("CONTROL_CHANNEL_ID", "0"))

try:
    with open("config.yml", "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f) or {}
except FileNotFoundError:
    CONFIG = {}

def _make_embed() -> discord.Embed:
    ui = CONFIG.get("ui", {}) or {}
    title = ui.get("panel_title", "Steuerungs-Panel")
    intro = ui.get("panel_intro", "")
    color = int(ui.get("panel_color", 0x2b2d31))
    return discord.Embed(title=title, description=intro or None, color=color)

class MessagingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # KEIN on_ready hier → Panel wird in bot.py bereitgestellt

    @commands.hybrid_command(name="panel", description="Steuerungs-Panel erneut posten")
    async def panel(self, ctx: commands.Context):
        if not user_is_admin(ctx.author):
            return await ctx.reply("⛔ Dafür fehlen dir die Rechte.", ephemeral=True if ctx.interaction else False)

        try:
            await ctx.reply(embed=_make_embed(), view=MessageMainView(), ephemeral=False)
            logger.info("/panel von %s ausgeführt in #%s", ctx.author, getattr(ctx.channel, 'name', '?'))
        except Exception as e:
            logger.exception("/panel fehlgeschlagen: %s", e)
            try:
                await ctx.reply(f"❌ Konnte Panel nicht senden: `{e}`", ephemeral=True if ctx.interaction else False)
            except Exception:
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(MessagingCog(bot))
