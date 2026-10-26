import discord
from discord.ext import commands
import json
import os

DB_FILE = 'database.json'

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"words": {"general": ["discord", "python", "termux"]}, "stats": {}}, f, indent=4)
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Database Read Error: {e}")
        return {"words": {}, "stats": {}}

def save_db(data):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ Database Save Error: {e}")

class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addword(self, ctx, category: str, *, word: str):
        category = category.lower()
        word = word.lower()
        data = load_db()
        
        if category not in data["words"]:
            data["words"][category] = []
            
        if word in data["words"][category]:
            await ctx.send(f"⚠️ The word `{word}` is already in the `{category}` category!")
            return
            
        data["words"][category].append(word)
        save_db(data)
        await ctx.send(f"✅ Added `{word}` to the `{category}` category!")

    @commands.command()
    async def delword(self, ctx, category: str, *, word: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Only server admins can delete words.")
            return

        category = category.lower()
        word = word.lower()
        data = load_db()
        
        if category in data["words"] and word in data["words"][category]:
            data["words"][category].remove(word)
            if len(data["words"][category]) == 0:
                del data["words"][category]
                
            save_db(data)
            await ctx.send(f"🗑️ Deleted `{word}` from `{category}`.")
        else:
            await ctx.send(f"❌ Could not find `{word}` in `{category}`.")

    @commands.command()
    async def categories(self, ctx):
        data = load_db()
        cats = data["words"]
        
        if not cats:
            await ctx.send("No categories found. Use `.addword <category> <word>` to make one!")
            return
            
        msg = "📚 **Hangman Categories:**\n"
        for cat, words in cats.items():
            msg += f"- **{cat.capitalize()}**: {len(words)} words\n"
            
        await ctx.send(msg)

    @commands.command()
    async def wordlist(self, ctx, category: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Only server admins can view the word list to prevent cheating!")
            return

        category = category.lower()
        data = load_db()
        
        if category not in data["words"] or not data["words"][category]:
            await ctx.send(f"❌ The category `{category}` is empty or doesn't exist.")
            return
            
        words = data["words"][category]
        word_string = ", ".join(words)
        await ctx.send(f"📂 **Admin Word List - {category.capitalize()}**:\n`{word_string}`")

    @commands.command(name="help")
    async def custom_help(self, ctx):
        embed = discord.Embed(title="🎮 Hangman Bot Commands", color=discord.Color.blue())
        
        embed.add_field(name="🗡️ Play", value="`.hangman [category]` - Play solo\n`.hangman duel` - Start a multiplayer Hot Seat game", inline=False)
        embed.add_field(name="📚 Word Bank", value="`.categories` - View all available categories\n`.addword [category] [word]` - Add a new word", inline=False)
        embed.add_field(name="🛡️ Admin Only", value="`.delword [cat] [word]` - Delete a word\n`.wordlist [cat]` - Reveal all words in a category\n`.hkick @user` - Kick a player from a duel", inline=False)
        
        embed.set_footer(text="Created by Pashu")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Hangman(bot))
