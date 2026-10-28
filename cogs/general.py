# cogs/general.py
import discord
from discord.ext import commands

class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Playing the Game", description="Learn how to play Solo, Duel, and Team.", emoji="🎮"),
            discord.SelectOption(label="Word Management", description="Commands for adding and checking words.", emoji="📚"),
            discord.SelectOption(label="Admin & Mods", description="How to manage games and bot admins.", emoji="🛡️")
        ]
        super().__init__(placeholder="Select a category to explore...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        
        if selection == "Playing the Game":
            embed = discord.Embed(title="🎮 Playing the Game", color=discord.Color.blue())
            embed.add_field(name="`,hangman [category]`", value="Play a standard **Solo** game.", inline=False)
            embed.add_field(name="`,hangman duel`", value="**Hot Seat Multiplayer**. Draft words for each other!", inline=False)
            embed.add_field(name="`,hangman team`", value="**Team vs Team**. Chaos in the main channel!", inline=False)
            embed.add_field(name="`,guide`", value="Read the full rulebook on how to play and use hints.", inline=False)
            
        elif selection == "Word Management":
            embed = discord.Embed(title="📚 Word Management", color=discord.Color.green())
            embed.add_field(name="`,categories`", value="Shows all word categories in this server.", inline=False)
            embed.add_field(name="`,addword [category] [word]`", value="Adds a single word to a category.", inline=False)
            embed.add_field(name="`,addwords [category] [word1], [word2]`", value="Mass add words separated by commas.", inline=False)
            
        elif selection == "Admin & Mods":
            embed = discord.Embed(title="🛡️ Admin & Mods", color=discord.Color.red())
            embed.add_field(name="`,purge [number] [@user]`", value="Deletes messages. Target a user to only wipe their chat.", inline=False)
            embed.add_field(name="`,snipe`", value="Catch the last deleted message in the channel.", inline=False)
            embed.add_field(name="`,hkick @user`", value="Kicks a player from an active lobby.", inline=False)
            embed.add_field(name="`,addmod` / `,delmod`", value="Manage custom Bot Admins.", inline=False)

        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120.0)
        self.add_item(HelpDropdown())

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def custom_help(self, ctx):
        embed = discord.Embed(
            title="✨ Hangman Bot Help Menu",
            description="Welcome to the ultimate Hangman experience.\nSelect a category from the dropdown menu below to see the commands!",
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text="Created by Pashu")
        await ctx.send(embed=embed, view=HelpView())

    @commands.command(name="guide")
    async def game_guide(self, ctx):
        embed = discord.Embed(title="📖 The Official Hangman Guide", color=discord.Color.gold())
        embed.add_field(name="⏱️ The Rules", value="You have **90 seconds** per turn. If you go AFK, you take a strike!", inline=False)
        embed.add_field(name="⚔️ Multiplayer Drafts", value="In Duel and Team modes, check your DMs when the game starts! You have 60s to secretly draft the hardest word for your opponents.", inline=False)
        embed.add_field(name="💡 The Sacrifice Economy", value="• Type `?hint` to sacrifice **1 Life** and reveal a random letter.\n• Type `?cat` to sacrifice **1 Life** and reveal the category.", inline=False)
        embed.add_field(name="🦸 Hero Guesses", value="Think you know the answer? Type `?guess [your word]`.\n✅ **If right:** Instant win.\n❌ **If wrong:** You take a **2 Strike** penalty!", inline=False)
        embed.set_footer(text="Good luck out there!")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
