import discord
from discord.ext import commands
from api_client import diagnose

class DiagnosticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="diag", description="API-Diagnose (Erreichbarkeit, Version, get_players)")
    async def diag(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        info = diagnose()
        emb = discord.Embed(title="CRCON API Diagnose", color=0x2b90d9)
        emb.add_field(name="API Base URL", value=info.get("api_base_url"), inline=False)

        net = info.get("network", {})
        if net.get("ok"):
            emb.add_field(name="Netzwerk", value=f"ok={net.get('ok')} host={net.get('host')} port={net.get('port')} rtt_ms={net.get('rtt_ms')}", inline=False)
        else:
            emb.add_field(name="Netzwerk", value=f"ok={net.get('ok')} error={net.get('error')}", inline=False)

        emb.add_field(name="Version/Health", value=str(info.get("version", {})), inline=False)
        emb.add_field(name="get_players", value=str(info.get("get_players", {})), inline=False)

        if info.get("last_error"):
            emb.add_field(name="Last Error", value=f"```{str(info['last_error'])[:900]}```", inline=False)

        await ctx.reply(embed=emb, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(DiagnosticsCog(bot))
