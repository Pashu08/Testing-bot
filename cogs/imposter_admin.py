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

        if "," not in words:
            return await ctx.send(embed=discord.Embed(title="⚠️ Invalid Format", description="Use a comma to separate words!\nExample: `,addpair hospital, school`", color=discord.Color.orange()))

        parts = words.split(",")
        if len(parts) != 2:
            return await ctx.send(embed=discord.Embed(title="⚠️ Invalid Format", description="Please provide exactly two words separated by one comma.", color=discord.Color.orange()))

        word1 = parts[0].strip().lower()
        word2 = parts[1].strip().lower()
        guild_id = str(ctx.guild.id)

        data = load_imposter_db()
        data = init_guild(data, guild_id)

        new_pair = [word1, word2]
        if new_pair in data[guild_id]["pairs"] or [word2, word1] in data[guild_id]["pairs"]:
            return await ctx.send(embed=discord.Embed(title="⚠️ Duplicate", description=f"The pair `{word1}` & `{word2}` already exists!", color=discord.Color.orange()))

        data[guild_id]["pairs"].append(new_pair)
        save_imposter_db(data)

        embed = discord.Embed(title="✅ Secret Pair Added", description=f"**Linked Words:** `{word1}` ↔️ `{word2}`", color=discord.Color.green())
        embed.set_footer(text="Roles are hidden to prevent cheating.")
        await ctx.send(embed=embed)

    @commands.command()
    async def delpair(self, ctx, *, word: str):
        if not is_admin(ctx):
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", color=discord.Color.red()))

        word = word.strip().lower()
        guild_id = str(ctx.guild.id)
        data = load_imposter_db()
        data = init_guild(data, guild_id)

        for pair in data[guild_id]["pairs"]:
            if pair[0] == word or pair[1] == word:
                data[guild_id]["pairs"].remove(pair)
                save_imposter_db(data)
                return await ctx.send(embed=discord.Embed(title="🗑️ Pair Deleted", description=f"Deleted the pair containing `{word}`.", color=discord.Color.green()))

        await ctx.send(embed=discord.Embed(title="❌ Error", description=f"Could not find a pair containing `{word}`.", color=discord.Color.red()))

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
