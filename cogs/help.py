import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="🤖 Bot Commands", color=discord.Color.blurple())
        
        embed.add_field(name="🎮 Games", value="`,hangman [category]` - Start Hangman\n`,imposter` - Start Imposter", inline=False)
        embed.add_field(name="📖 Guides", value="`,guide hangman` - How to play Hangman\n`,guide imposter` - How to play Imposter", inline=False)
        embed.add_field(name="⚙️ Admin Setup", value="**Hangman:** `,categories`, `,addword`, `,addwords`, `,delword`, `,rencat`\n**Imposter:** `,pairs`, `,addpair`, `,delpair`", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
