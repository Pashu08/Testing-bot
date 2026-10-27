# cogs/general.py
import discord
from discord.ext import commands
from utils.db import load_db, save_db

OWNER_ID = 756012403291848804

def init_guild(data, guild_id):
    if guild_id not in data:
        data[guild_id] = {"words": {}, "mods": []}
    if "mods" not in data[guild_id]:
        data[guild_id]["mods"] = []
    if "words" not in data[guild_id]:
        data[guild_id]["words"] = {}
    return data

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
            embed.add_field(name="`.hangman [category]`", value="Play a standard **Solo** game. You have 90 seconds per guess.", inline=False)
            embed.add_field(name="`.hangman duel`", value="**Hot Seat Multiplayer**. The bot DMs everyone to draft words for each other. Miss a letter, and your turn passes!", inline=False)
            embed.add_field(name="`.hangman team`", value="**Team vs Team**. Chaos in the main channel! Talk openly and bluff, but only the *Designated Guesser* can actually type the answer!", inline=False)
            embed.add_field(name="💡 Hints & Hero Guesses", value="Type `?guess [word]` to instantly solve it (Fails cost 2 Lives!).\nType `?hint` or `?cat` at the cost of **1 Life** to get a clue.", inline=False)
            
        elif selection == "Word Management":
            embed = discord.Embed(title="📚 Word Management", color=discord.Color.green())
            embed.add_field(name="`.categories`", value="Shows all word categories in this server.", inline=False)
            embed.add_field(name="`.addword [category] [word]`", value="Adds a single word to a category.", inline=False)
            embed.add_field(name="`.addwords [category] [word1], [word2]`", value="Mass add words separated by commas.", inline=False)
            
        elif selection == "Admin & Mods":
            embed = discord.Embed(title="🛡️ Admin & Mods", color=discord.Color.red())
            embed.add_field(name="`.rencat [old_name] [new_name]`", value="Renames an existing category.", inline=False)
            embed.add_field(name="`.delword [category] [word]`", value="Deletes a word.", inline=False)
            embed.add_field(name="`.wordlist [category]`", value="Shows the full list of words in a category.", inline=False)
            embed.add_field(name="`.hkick @user`", value="Kicks a player from an active lobby. (Host/Bot Mod only)", inline=False)
            embed.add_field(name="`.addmod @user` / `.delmod @user`", value="Gives a user permission to delete words, rename categories, and kick players.", inline=False)
            embed.add_field(name="`.modlist`", value="See who the current Bot Admins are.", inline=False)

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

    @commands.command()
    async def addmod(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.administrator and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Only Server Admins or the Bot Owner can add mods.", color=discord.Color.red()))
            
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
        
        if member.id in data[guild_id]["mods"]:
            return await ctx.send(embed=discord.Embed(title="⚠️ Already Mod", description=f"{member.mention} is already a Bot Admin.", color=discord.Color.orange()))
            
        data[guild_id]["mods"].append(member.id)
        save_db(data)
        await ctx.send(embed=discord.Embed(title="🛡️ Mod Added", description=f"{member.mention} is now a Bot Admin!", color=discord.Color.green()))

    @commands.command()
    async def delmod(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.administrator and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Only Server Admins or the Bot Owner can remove mods.", color=discord.Color.red()))
            
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
        
        if member.id not in data[guild_id]["mods"]:
            return await ctx.send(embed=discord.Embed(title="⚠️ Not Found", description=f"{member.mention} is not in the Bot Admin list.", color=discord.Color.orange()))
            
        data[guild_id]["mods"].remove(member.id)
        save_db(data)
        await ctx.send(embed=discord.Embed(title="🗑️ Mod Removed", description=f"{member.mention} is no longer a Bot Admin.", color=discord.Color.red()))

    @commands.command()
    async def modlist(self, ctx):
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
        
        mod_ids = data.get(guild_id, {}).get("mods", [])
        if not mod_ids:
            return await ctx.send(embed=discord.Embed(title="🛡️ Bot Admins", description="There are no custom Bot Admins in this server yet.", color=discord.Color.blue()))
            
        mod_mentions = [f"<@{m_id}>" for m_id in mod_ids]
        embed = discord.Embed(title="🛡️ Current Bot Admins", description="\n".join(mod_mentions), color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
