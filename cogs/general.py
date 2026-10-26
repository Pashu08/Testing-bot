# cogs/general.py
import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def custom_help(self, ctx):
        embed = discord.Embed(title="🎮 Hangman Bot Commands", color=discord.Color.blue())
        embed.add_field(name="🗡️ Play", value="`.hangman [category]` - Solo\n`.hangman duel` - Multiplayer Hot Seat\n`.hangman team` - Team vs. Team", inline=False)
        embed.add_field(name="📚 Word Bank", value="`.categories`, `.addword [cat] [word]`", inline=False)
        embed.add_field(name="🛡️ Admin/Host", value="`.delword`, `.wordlist`, `.hkick @user`", inline=False)
        embed.set_footer(text="Created by Pashu")
        await ctx.send(embed=embed)

    @commands.command(name="guide")
    async def game_guide(self, ctx, game_name: str = None):
        if game_name is None or game_name.lower() != "hangman":
            return await ctx.send("📚 **Available Guides:**\n- `hangman`\nUsage: `.guide hangman`")
        embed = discord.Embed(title="🎮 THE OFFICIAL HANGMAN SURVIVAL GUIDE", color=discord.Color.dark_red())
        embed.add_field(name="1. The Word Bank", value="Type `.addword [cat] [word]` to add words to your server's database.", inline=False)
        embed.add_field(name="2. Solo & Duel", value="`.hangman [category]` to play alone.\n`.hangman duel` for Hot Seat free-for-all mode.", inline=False)
        embed.add_field(name="3. TEAM VS TEAM", value="Type `.hangman team`.\nThe bot splits you into **Red 🍎** and **Blue 🫐** and makes secret Strategy Threads for you to talk in.", inline=False)
        embed.add_field(name="4. Team Rules", value="**Designated Guesser**: You have 90s to talk in your thread, but ONLY the pinged player can type the guess in the main channel.\n**Hero Guess**: Type the FULL word to instantly win. But if you misspell it, your team takes 2 penalty strikes!", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
