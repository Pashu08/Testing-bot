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
        data = load_db()
        if category not in data["words"]: data["words"][category] = []
        if word in data["words"][category]:
            return await ctx.send(f"⚠️ `{word}` is already in `{category}`!")
        data["words"][category].append(word)
        save_db(data)
        await ctx.send(f"✅ Added `{word}` to `{category}`!")

    @commands.command()
    async def delword(self, ctx, category: str, *, word: str):
        if not ctx.author.guild_permissions.administrator: 
            return await ctx.send("❌ Only admins can delete words.")
        category, word = category.lower(), word.lower()
        data = load_db()
        if category in data["words"] and word in data["words"][category]:
            data["words"][category].remove(word)
            if len(data["words"][category]) == 0: del data["words"][category]
            save_db(data)
            await ctx.send(f"🗑️ Deleted `{word}` from `{category}`.")
        else:
            await ctx.send(f"❌ Could not find `{word}` in `{category}`.")

    @commands.command()
    async def categories(self, ctx):
        data = load_db()
        cats = data["words"]
        if not cats: return await ctx.send("No categories found! Use `.addword`")
        msg = "📚 **Hangman Categories:**\n"
        for cat, words in cats.items(): msg += f"- **{cat.capitalize()}**: {len(words)} words\n"
        await ctx.send(msg)

    @commands.command()
    async def wordlist(self, ctx, category: str):
        if not ctx.author.guild_permissions.administrator: return await ctx.send("❌ Admin only.")
        category = category.lower()
        data = load_db()
        if category not in data["words"]: return await ctx.send("❌ Category not found.")
        await ctx.send(f"📂 **Admin Word List - {category.capitalize()}**:\n`{', '.join(data['words'][category])}`")

async def setup(bot):
    await bot.add_cog(Words(bot))
