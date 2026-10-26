# cogs/words.py
import discord
from discord.ext import commands
from utils.db import load_db, save_db

class Words(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addword(self, ctx, category: str, *, word: str):
        category, word = category.lower(), word.lower()
        guild_id = str(ctx.guild.id) # Gets the Server's unique ID
        data = load_db()
        
        # If this server doesn't exist in the database yet, create its room
        if guild_id not in data:
            data[guild_id] = {"words": {}}
            
        if category not in data[guild_id]["words"]: 
            data[guild_id]["words"][category] = []
            
        if word in data[guild_id]["words"][category]:
            return await ctx.send(f"⚠️ `{word}` is already in `{category}`!")
            
        data[guild_id]["words"][category].append(word)
        save_db(data)
        await ctx.send(f"✅ Added `{word}` to `{category}` in this server!")

    @commands.command()
    async def delword(self, ctx, category: str, *, word: str):
        if not ctx.author.guild_permissions.administrator: 
            return await ctx.send("❌ Only admins can delete words.")
            
        category, word = category.lower(), word.lower()
        guild_id = str(ctx.guild.id)
        data = load_db()
        
        if guild_id in data and category in data[guild_id]["words"] and word in data[guild_id]["words"][category]:
            data[guild_id]["words"][category].remove(word)
            if len(data[guild_id]["words"][category]) == 0: 
                del data[guild_id]["words"][category]
            save_db(data)
            await ctx.send(f"🗑️ Deleted `{word}` from `{category}`.")
        else:
            await ctx.send(f"❌ Could not find `{word}` in `{category}` in this server.")

    @commands.command()
    async def categories(self, ctx):
        guild_id = str(ctx.guild.id)
        data = load_db()
        
        if guild_id not in data or not data[guild_id]["words"]: 
            return await ctx.send("No categories found for this server! Use `.addword`")
            
        cats = data[guild_id]["words"]
        msg = "📚 **Hangman Categories (This Server):**\n"
        for cat, words in cats.items(): 
            msg += f"- **{cat.capitalize()}**: {len(words)} words\n"
        await ctx.send(msg)

    @commands.command()
    async def wordlist(self, ctx, category: str):
        if not ctx.author.guild_permissions.administrator: return await ctx.send("❌ Admin only.")
        
        category = category.lower()
        guild_id = str(ctx.guild.id)
        data = load_db()
        
        if guild_id not in data or category not in data[guild_id]["words"]: 
            return await ctx.send("❌ Category not found in this server.")
            
        word_string = ', '.join(data[guild_id]["words"][category])
        await ctx.send(f"📂 **Admin Word List - {category.capitalize()}**:\n`{word_string}`")

async def setup(bot):
    await bot.add_cog(Words(bot))
