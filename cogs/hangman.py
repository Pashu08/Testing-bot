import discord
from discord.ext import commands
import json
import os
import random
import asyncio

DB_FILE = 'database.json'

HANGMAN_PICS = [
"""```
  +---+
  |   |
      |
      |
      |
      |
=========
```""",
"""```
  +---+
  |   |
  O   |
      |
      |
      |
=========
```""",
"""```
  +---+
  |   |
  O   |
  |   |
      |
      |
=========
```""",
"""```
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========
```""",
"""```
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
=========
```""",
"""```
  +---+
  |   |
  O   |
 /|\\  |
 /    |
      |
=========
```""",
"""```
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
=========
```"""
]

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

    @commands.command(name="guide")
    async def game_guide(self, ctx, game_name: str = None):
        if game_name is None or game_name.lower() != "hangman":
            await ctx.send("📚 **Available Guides:**\n- `hangman`\n\nUsage: `.guide hangman` (More games coming soon!)")
            return

        embed = discord.Embed(title="🎮 THE OFFICIAL HANGMAN SURVIVAL GUIDE", color=discord.Color.dark_red())
        embed.add_field(name="1. The Word Bank (Prep Phase)", value="You CANNOT make up words during the game! You draft from the database, so you MUST add words *before* playing.\n- Type `.addword [category] [word]` to expand the lists.\n- Type `.categories` to see what is already available.", inline=False)
        embed.add_field(name="2. Solo Training", value="Type `.hangman [category]`. The bot pulls a random word from that saved category. You have 90 seconds per guess.", inline=False)
        embed.add_field(name="3. THE DUEL: Hot Seat Mode", value="**Lobby**: Type `.hangman duel`. React with ✋ to join, Host clicks ✅ to start.\n**Draft**: The bot DMs you to pick a category, then gives you 5 words *that were already saved in that category*. Pick the hardest one.\n**Hot Seat**: Words are secretly shuffled. Players take turns in the Hot Seat guessing their assigned word.", inline=False)
        embed.set_footer(text="Good luck. You're going to need it.")
        await ctx.send(embed=embed)

    @commands.command(name="hangman")
    async def play_hangman(self, ctx, category: str = None):
        if not category:
            await ctx.send("⚠️ You must specify a category! Example: `.hangman general` or `.hangman duel`.")
            return
            
        category = category.lower()
        
        # This catches the Duel command and holds it for Phase 3
        if category == "duel":
            await ctx.send("⚔️ Multiplayer Duel mode is coming in Phase 3! Try a solo category for now.")
            return

        data = load_db()
        if category not in data["words"] or not data["words"][category]:
            await ctx.send(f"❌ Category `{category}` is empty or doesn't exist. Type `.categories` to check.")
            return

        word = random.choice(data["words"][category])
        guessed_letters = []
        wrong_guesses = 0

        # Function to generate the board string with hidden/revealed letters and spaces
        def get_display_word():
            display = ""
            for char in word:
                if char == " ":
                    display += "   " # Triple space for visual clarity of separate words
                elif char in guessed_letters:
                    display += f"{char} "
                else:
                    display += "_ "
            return display

        # Initial message
        board_msg = await ctx.send(f"🎮 **Solo Hangman** | Category: **{category.capitalize()}**\n{HANGMAN_PICS[wrong_guesses]}\n`{get_display_word()}`\n\n*Type a single letter in the chat to guess! (90s limit)*")

        # This filter ensures the bot only listens to YOUR letters in THAT channel
        def check_guess(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()

        # The Game Loop
        while wrong_guesses < 6:
            try:
                # Wait 90 seconds for a guess
                user_msg = await self.bot.wait_for('message', check=check_guess, timeout=90.0)
                guess = user_msg.content.lower()

                if guess in guessed_letters:
                    await ctx.send(f"⚠️ You already guessed `{guess}`!", delete_after=3)
                    continue

                guessed_letters.append(guess)

                if guess not in word:
                    wrong_guesses += 1

                # Update the board
                display = get_display_word()
                guessed_str = ", ".join(guessed_letters) if guessed_letters else "None"
                
                await board_msg.edit(content=f"🎮 **Solo Hangman** | Category: **{category.capitalize()}**\n{HANGMAN_PICS[wrong_guesses]}\n`{display}`\n\n**Guessed:** {guessed_str}")

                # Check if won
                if "_" not in display:
                    await ctx.send(f"🎉 **YOU SURVIVED!** The word was **{word.title()}**.")
                    return

            except asyncio.TimeoutError:
                await ctx.send(f"⏰ **TIME'S UP!** You took longer than 90 seconds to guess. You hang.\nThe word was **{word.title()}**.")
                return

        # Check if lost (Hit 6 wrong guesses)
        await ctx.send(f"💀 **GAME OVER!** You have been hanged.\nThe word was **{word.title()}**.")

async def setup(bot):
    await bot.add_cog(Hangman(bot))
