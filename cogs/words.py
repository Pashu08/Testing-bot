# cogs/words.py
import discord
from discord.ext import commands
from utils.db import load_db, save_db

OWNER_ID = 756012403291848804

def is_bot_admin(ctx, data, guild_id):
    if ctx.author.id == OWNER_ID: return True
    if ctx.author.guild_permissions.administrator: return True
    if ctx.author.id in data.get(guild_id, {}).get("mods", []): return True
    return False

def init_guild(data, guild_id):
    if guild_id not in data:
        data[guild_id] = {"words": {}, "mods": []}
    if "mods" not in data[guild_id]:
        data[guild_id]["mods"] = []
    if "words" not in data[guild_id]:
        data[guild_id]["words"] = {}
    return data

class Words(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addword(self, ctx, category: str, *, word: str):
        category, word = category.lower(), word.lower()
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
            
        if category not in data[guild_id]["words"]: 
            data[guild_id]["words"][category] = []
            
        if word in data[guild_id]["words"][category]:
            embed = discord.Embed(title="⚠️ Duplicate Word", description=f"`{word}` is already in `{category}`!", color=discord.Color.orange())
            return await ctx.send(embed=embed)
            
        data[guild_id]["words"][category].append(word)
        save_db(data)
        
        embed = discord.Embed(title="✅ Word Added", description=f"Added `{word}` to `{category}`.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def addwords(self, ctx, category: str, *, words_string: str):
        category = category.lower()
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)

        if category not in data[guild_id]["words"]: 
            data[guild_id]["words"][category] = []

        raw_words = [w.strip().lower() for w in words_string.split(",")]
        added, duplicates = [], []

        for w in raw_words:
            if not w: continue
            if w in data[guild_id]["words"][category]:
                duplicates.append(w)
            else:
                data[guild_id]["words"][category].append(w)
                added.append(w)

        save_db(data)

        embed = discord.Embed(title="📚 Mass Add Complete", color=discord.Color.green())
        if added:
            embed.add_field(name="✅ Added Successfully", value=", ".join(added), inline=False)
        if duplicates:
            embed.add_field(name="⚠️ Skipped Duplicates", value=", ".join(duplicates), inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def delword(self, ctx, category: str, *, word: str):
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
        
        if not is_bot_admin(ctx, data, guild_id): 
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Only Bot Admins can delete words.", color=discord.Color.red()))
            
        category, word = category.lower(), word.lower()
        
        if category in data[guild_id]["words"] and word in data[guild_id]["words"][category]:
            data[guild_id]["words"][category].remove(word)
            if len(data[guild_id]["words"][category]) == 0: 
                del data[guild_id]["words"][category]
            save_db(data)
            await ctx.send(embed=discord.Embed(title="🗑️ Word Deleted", description=f"Removed `{word}` from `{category}`.", color=discord.Color.green()))
        else:
            await ctx.send(embed=discord.Embed(title="❌ Error", description=f"Could not find `{word}` in `{category}`.", color=discord.Color.red()))

    @commands.command()
    async def rencat(self, ctx, old_name: str, new_name: str):
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)

        if not is_bot_admin(ctx, data, guild_id): 
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Only Bot Admins can rename categories.", color=discord.Color.red()))
        
        old_name, new_name = old_name.lower(), new_name.lower()
        
        if old_name not in data[guild_id]["words"]:
            return await ctx.send(embed=discord.Embed(title="❌ Error", description=f"Category `{old_name}` does not exist.", color=discord.Color.red()))
            
        if new_name in data[guild_id]["words"]:
            return await ctx.send(embed=discord.Embed(title="⚠️ Error", description=f"Category `{new_name}` already exists! Choose a different name.", color=discord.Color.orange()))
            
        data[guild_id]["words"][new_name] = data[guild_id]["words"].pop(old_name)
        save_db(data)
        
        await ctx.send(embed=discord.Embed(title="🔄 Category Renamed", description=f"Successfully renamed `{old_name}` to `{new_name}`.", color=discord.Color.green()))

    @commands.command()
    async def categories(self, ctx):
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
        
        if not data[guild_id]["words"]:
            return await ctx.send(embed=discord.Embed(title="📚 Categories", description="No categories found! Use `.addword`.", color=discord.Color.blue()))
            
        embed = discord.Embed(title="📚 Hangman Categories", description="Here is the word bank for this server:", color=discord.Color.blue())
        for cat, words in data[guild_id]["words"].items(): 
            embed.add_field(name=cat.capitalize(), value=f"{len(words)} words", inline=True)
            
        await ctx.send(embed=embed)

    @commands.command()
    async def wordlist(self, ctx, category: str):
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)

        if not is_bot_admin(ctx, data, guild_id): 
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Admin only.", color=discord.Color.red()))
        
        category = category.lower()
        
        if category not in data[guild_id]["words"]: 
            return await ctx.send(embed=discord.Embed(title="❌ Error", description="Category not found.", color=discord.Color.red()))
            
        word_string = ', '.join(data[guild_id]["words"][category])
        embed = discord.Embed(title=f"📂 Word List: {category.capitalize()}", description=f"`{word_string}`", color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Words(bot))
