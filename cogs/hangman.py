import discord
from discord.ext import commands
import json
import os

# This file will automatically be created in your main folder
DB_FILE = 'database.json'

# Helper function to load the database safely
def load_db():
    if not os.path.exists(DB_FILE):
        # Create a default database structure if it doesn't exist
        with open(DB_FILE, 'w') as f:
            json.dump({"words": {"general": ["discord", "python", "termux"]}, "stats": {}}, f, indent=4)
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Database Read Error: {e}")
        return {"words": {}, "stats": {}}

# Helper function to save changes to the database
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
        
        # Create the category if it doesn't exist yet
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
        # Prevent regular users from deleting words
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Only server admins can delete words.")
            return

        category = category.lower()
        word = word.lower()
        data = load_db()
        
        if category in data["words"] and word in data["words"][category]:
            data["words"][category].remove(word)
            
            # Clean up: If category is now empty, delete the category entirely
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

# This setup function is required at the bottom of every Cog file
async def setup(bot):
    await bot.add_cog(Hangman(bot))
