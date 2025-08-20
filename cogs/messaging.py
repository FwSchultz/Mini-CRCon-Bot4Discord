import os
import yaml
import discord
from discord.ext import commands
from views.message import MessageMainView
from utils.permissions import user_is_admin

CONTROL_CHANNEL_ID = int(os.getenv("CONTROL_CHANNEL_ID", "0"))

with open("config.yml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f) or {}

class MessagingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Panel beim Start (oder Neustart) neu setzen
        try:
            channel = self.bot.get_channel(CONTROL_CHANNEL_ID)
            if channel and isinstance(channel, discord.TextChannel):
                await channel.purge(limit=5)
                await channel.send(
                    content=f"## {CONFIG.get('ui',{}).get('panel_title','Steuerungs-Panel')}\n{CONFIG.get('ui',{}).get('panel_intro','')}",
                    view=MessageMainView(),
                )
        except Exception:
            pass

    @commands.hybrid_command(name="panel", description="Steuerungs-Panel senden")
    async def panel(self, ctx: commands.Context):
        if not user_is_admin(ctx.author):
            return await ctx.reply("⛔ Dafür fehlen dir die Rechte.")
        await ctx.send(content="## Steuerungs-Panel", view=MessageMainView())

async def setup(bot: commands.Bot):
    await bot.add_cog(MessagingCog(bot))
