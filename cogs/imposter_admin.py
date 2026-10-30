import discord
from discord.ext import commands
from utils.imposter_db import load_imposter_db, save_imposter_db

OWNER_ID = 756012403291848804

def is_admin(ctx):
    if ctx.author.id == OWNER_ID: return True
    if ctx.author.guild_permissions.administrator: return True
    return False

def init_guild(data, guild_id):
    if guild_id not in data:
        data[guild_id] = {"pairs": []}
    return data

class ImposterAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addpair(self, ctx, *, words: str):
        if not is_admin(ctx):
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Only Admins can add word pairs.", color=discord.Color.red()))

        # Split the input by comma
        if "," not in words:
            return await ctx.send(embed=discord.Embed(title="⚠️ Invalid Format", description="Use a comma to separate words!\nExample: `,addpair hospital, school`", color=discord.Color.orange()))

        parts = words.split(",")
        if len(parts) != 2:
            return await ctx.send(embed=discord.Embed(title="⚠️ Invalid Format", description="Please provide exactly two words separated by one comma.", color=discord.Color.orange()))

        innocent_word = parts[0].strip().lower()
        imposter_word = parts[1].strip().lower()
        guild_id = str(ctx.guild.id)

        data = load_imposter_db()
        data = init_guild(data, guild_id)

        # Check for duplicates
        new_pair = [innocent_word, imposter_word]
        if new_pair in data[guild_id]["pairs"] or [imposter_word, innocent_word] in data[guild_id]["pairs"]:
            return await ctx.send(embed=discord.Embed(title="⚠️ Duplicate", description=f"The pair `{innocent_word}` & `{imposter_word}` already exists!", color=discord.Color.orange()))

        # Add and save
        data[guild_id]["pairs"].append(new_pair)
        save_imposter_db(data)

        embed = discord.Embed(title="✅ Pair Added", description=f"**Innocents:** `{innocent_word}`\n**Imposter:** `{imposter_word}`", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def delpair(self, ctx, *, innocent_word: str):
        if not is_admin(ctx):
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", color=discord.Color.red()))

        innocent_word = innocent_word.strip().lower()
        guild_id = str(ctx.guild.id)
        data = load_imposter_db()
        data = init_guild(data, guild_id)

        # Search and remove the pair
        for pair in data[guild_id]["pairs"]:
            if pair[0] == innocent_word or pair[1] == innocent_word:
                data[guild_id]["pairs"].remove(pair)
                save_imposter_db(data)
                return await ctx.send(embed=discord.Embed(title="🗑️ Pair Deleted", description=f"Deleted the pair containing `{innocent_word}`.", color=discord.Color.green()))

        await ctx.send(embed=discord.Embed(title="❌ Error", description=f"Could not find a pair containing `{innocent_word}`.", color=discord.Color.red()))

    @commands.command()
    async def pairs(self, ctx):
        if not is_admin(ctx):
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", color=discord.Color.red()))

        guild_id = str(ctx.guild.id)
        data = load_imposter_db()
        data = init_guild(data, guild_id)

        total_pairs = len(data[guild_id]["pairs"])
        if total_pairs == 0:
            return await ctx.send(embed=discord.Embed(title="📂 Imposter Word Pairs", description="No word pairs loaded yet! Use `,addpair`", color=discord.Color.blue()))

        embed = discord.Embed(title="📂 Imposter Word Pairs", description=f"There are currently **{total_pairs}** word pairs ready to play in this server.", color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ImposterAdmin(bot))
