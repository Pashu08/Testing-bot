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
        # Maps channel ID to the list of active players in a duel
        self.duel_players = {}
        # Maps channel ID to the host user
        self.duel_hosts = {}

    @commands.command()
    async def addword(self, ctx, category: str, *, word: str):
        category = category.lower()
        word = word.lower()
        data = load_db()
        
        if category not in data["words"]:
            data["words"][category] = []
            
        if word in data["words"][category]:
            return await ctx.send(f"⚠️ The word `{word}` is already in `{category}`!")
            
        data["words"][category].append(word)
        save_db(data)
        await ctx.send(f"✅ Added `{word}` to `{category}`!")

    @commands.command()
    async def delword(self, ctx, category: str, *, word: str):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Only admins can delete words.")

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
        if not cats: return await ctx.send("No categories found! Use `.addword`")
        msg = "📚 **Hangman Categories:**\n"
        for cat, words in cats.items(): msg += f"- **{cat.capitalize()}**: {len(words)} words\n"
        await ctx.send(msg)

    @commands.command()
    async def wordlist(self, ctx, category: str):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Admin only. No cheating!")
        category = category.lower()
        data = load_db()
        if category not in data["words"]: return await ctx.send("❌ Category not found.")
        word_string = ", ".join(data["words"][category])
        await ctx.send(f"📂 **Admin Word List - {category.capitalize()}**:\n`{word_string}`")

    @commands.command(name="help")
    async def custom_help(self, ctx):
        embed = discord.Embed(title="🎮 Hangman Bot Commands", color=discord.Color.blue())
        embed.add_field(name="🗡️ Play", value="`.hangman [category]` - Solo\n`.hangman duel` - Multiplayer Hot Seat", inline=False)
        embed.add_field(name="📚 Word Bank", value="`.categories` - View lists\n`.addword [cat] [word]` - Add word", inline=False)
        embed.add_field(name="🛡️ Admin/Host", value="`.delword [cat] [word]` - Delete word\n`.wordlist [cat]` - See words\n`.hkick @user` - Kick player from duel", inline=False)
        embed.set_footer(text="Created by Pashu")
        await ctx.send(embed=embed)

    @commands.command(name="guide")
    async def game_guide(self, ctx, game_name: str = None):
        if game_name is None or game_name.lower() != "hangman":
            return await ctx.send("📚 **Available Guides:**\n- `hangman`\nUsage: `.guide hangman`")
        embed = discord.Embed(title="🎮 THE OFFICIAL HANGMAN SURVIVAL GUIDE", color=discord.Color.dark_red())
        embed.add_field(name="1. The Word Bank (Prep Phase)", value="You CANNOT make up words during the game! You draft from the database. Type `.addword [cat] [word]` before playing.", inline=False)
        embed.add_field(name="2. Solo Training", value="Type `.hangman [category]`. 90 seconds per guess.", inline=False)
        embed.add_field(name="3. THE DUEL: Hot Seat Mode", value="**Lobby**: `.hangman duel`. React ✋ to join, Host clicks ✅ to start.\n**Draft**: The bot DMs you to pick a category and word.\n**Hot Seat**: Words are secretly shuffled. You will never get your own word.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def hkick(self, ctx, member: discord.Member):
        host = self.duel_hosts.get(ctx.channel.id)
        if not ctx.author.guild_permissions.administrator and ctx.author != host:
            return await ctx.send("❌ Only the Host or an Admin can kick players.")
            
        if ctx.channel.id in self.duel_players and member in self.duel_players[ctx.channel.id]:
            self.duel_players[ctx.channel.id].remove(member)
            await ctx.send(f"👢 **{member.display_name}** was kicked from the duel!")
        else:
            await ctx.send("⚠️ That player is not in an active duel here.")

    @commands.command(name="hangman")
    async def play_hangman(self, ctx, category: str = None):
        if not category: return await ctx.send("⚠️ Specify a category! Example: `.hangman general` or `.hangman duel`.")
        category = category.lower()
        data = load_db()

        # ================================
        # PHASE 3: MULTIPLAYER DUEL MODE
        # ================================
        if category == "duel":
            if ctx.channel.id in self.duel_players:
                return await ctx.send("⚠️ A duel is already happening here!")
            
            self.duel_hosts[ctx.channel.id] = ctx.author
            lobby_msg = await ctx.send(f"⚔️ **HANGMAN DUEL LOBBY** ⚔️\n\nReact ✋ to join!\nHost (`{ctx.author.display_name}`) react ✅ to lock the lobby and start.")
            await lobby_msg.add_reaction("✋")
            await lobby_msg.add_reaction("✅")
            
            def check_start(reaction, user):
                return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == lobby_msg.id
                
            try:
                await self.bot.wait_for('reaction_add', timeout=300.0, check=check_start)
            except asyncio.TimeoutError:
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send("⏳ Lobby timed out.")
                
            lobby_msg = await ctx.channel.fetch_message(lobby_msg.id)
            players = []
            for reaction in lobby_msg.reactions:
                if str(reaction.emoji) == "✋":
                    async for user in reaction.users():
                        if not user.bot and user not in players: players.append(user)
                            
            if len(players) < 2:
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send("⚠️ Not enough players joined! Need at least 2.")
                
            self.duel_players[ctx.channel.id] = players
            await ctx.send(f"🚀 **DUEL STARTING!** {len(players)} players locked in.\n\n📱 **CHECK YOUR DMs!** You have 60 seconds to draft a word for someone else...")
            
            # THE DRAFT (Runs for everyone simultaneously)
            async def draft_for_player(p):
                if p not in self.duel_players.get(ctx.channel.id, []): return "kicked"
                try:
                    dm = await p.create_dm()
                    await dm.send("⚔️ **THE DRAFT** ⚔️\nReply with a category name from the database (e.g., `murim`).")
                    
                    def check_msg(m): return m.author == p and m.channel == dm
                    
                    try:
                        cat_msg = await self.bot.wait_for('message', check=check_msg, timeout=60.0)
                        cat = cat_msg.content.lower()
                    except asyncio.TimeoutError:
                        cat = random.choice(list(data["words"].keys()))
                        await dm.send(f"⏳ Time's up! Auto-picked category: `{cat}`")
                        
                    if cat not in data["words"] or not data["words"][cat]:
                        cat = random.choice(list(data["words"].keys()))
                        await dm.send(f"⚠️ Invalid category! Auto-picked: `{cat}`")
                        
                    cat_words = data["words"][cat]
                    sample_size = min(5, len(cat_words))
                    choices = random.sample(cat_words, sample_size)
                    
                    choices_text = "\n".join([f"**{i+1}**. {w}" for i, w in enumerate(choices)])
                    await dm.send(f"Now, reply with the **number** of the hardest word (1-{sample_size}):\n\n{choices_text}")
                    
                    def check_num(m): return m.author == p and m.channel == dm and m.content.isdigit()
                    try:
                        num_msg = await self.bot.wait_for('message', check=check_num, timeout=60.0)
                        idx = int(num_msg.content) - 1
                        if 0 <= idx < sample_size:
                            chosen = choices[idx]
                            await dm.send(f"✅ Locked in: **{chosen}**. Head back to the server!")
                        else:
                            chosen = random.choice(choices)
                            await dm.send(f"⚠️ Invalid number! Auto-picked: **{chosen}**. Head back!")
                    except asyncio.TimeoutError:
                        chosen = random.choice(choices)
                        await dm.send(f"⏳ Time's up! Auto-picked: **{chosen}**. Head back!")
                    return chosen
                    
                except discord.Forbidden:
                    await ctx.send(f"⚠️ {p.mention}, your DMs are locked! Auto-picking a word for you.")
                    cat = random.choice(list(data["words"].keys()))
                    return random.choice(data["words"][cat])

            # Wait for all players to finish drafting at the same time
            tasks = [draft_for_player(p) for p in players]
            results = await asyncio.gather(*tasks)
            
            current_players = self.duel_players.get(ctx.channel.id, [])
            if len(current_players) < 2:
                self.duel_players.pop(ctx.channel.id, None)
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send("⚠️ Too many players left or were kicked. Duel aborted.")
                
            active_results, final_players = [], []
            for i, res in enumerate(results):
                if res != "kicked" and players[i] in current_players:
                    active_results.append(res)
                    final_players.append(players[i])
                    
            # THE SHUFFLE (Shift by 1 guarantees nobody gets their own word)
            assigned_words = [None] * len(final_players)
            for i in range(len(final_players)):
                assigned_words[i] = active_results[(i + 1) % len(final_players)]
                
            await ctx.send("🎲 **THE DRAFT IS COMPLETE.** Words are secretly shuffled.\n\n🔥 **LET THE HOT SEATS BEGIN!** 🔥")
            
            # THE HOT SEAT LOOP
            for i, p in enumerate(final_players):
                if p not in self.duel_players.get(ctx.channel.id, []):
                    await ctx.send(f"⏭️ {p.display_name} was kicked. Skipping their turn...")
                    continue
                    
                word = assigned_words[i]
                guessed_letters = []
                wrong_guesses = 0
                
                def get_display(w, gl):
                    d = ""
                    for char in w:
                        if char == " ": d += "   "
                        elif char in gl: d += f"{char} "
                        else: d += "_ "
                    return d
                
                await ctx.send(f"🔥 **HOT SEAT:** {p.mention}, you are up! (Only your guesses count)")
                board_msg = await ctx.send(f"{HANGMAN_PICS[wrong_guesses]}\n`{get_display(word, guessed_letters)}`\n\n*Type a letter! (90s limit)*")
                
                def check_guess_duel(m):
                    return m.author == p and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()
                
                won = False
                while wrong_guesses < 6:
                    if p not in self.duel_players.get(ctx.channel.id, []):
                        await ctx.send(f"⏭️ {p.display_name} was kicked mid-turn. Moving on!")
                        won = True 
                        break
                        
                    try:
                        user_msg = await self.bot.wait_for('message', check=check_guess_duel, timeout=90.0)
                        guess = user_msg.content.lower()
                        
                        if guess in guessed_letters:
                            await ctx.send(f"⚠️ You already guessed `{guess}`!", delete_after=3)
                            continue
                            
                        guessed_letters.append(guess)
                        if guess not in word: wrong_guesses += 1
                        
                        display = get_display(word, guessed_letters)
                        g_str = ", ".join(guessed_letters) if guessed_letters else "None"
                        await board_msg.edit(content=f"{HANGMAN_PICS[wrong_guesses]}\n`{display}`\n\n**Guessed:** {g_str}")
                        
                        if "_" not in display:
                            await ctx.send(f"🎉 **{p.display_name} SURVIVED!** The word was **{word.title()}**.")
                            won = True
                            break
                    except asyncio.TimeoutError:
                        await ctx.send(f"⏰ **TIME'S UP!** {p.display_name} took too long and hangs!\nThe word was **{word.title()}**.")
                        won = True
                        break
                        
                if not won:
                    await ctx.send(f"💀 **GAME OVER!** {p.display_name} has been hanged.\nThe word was **{word.title()}**.")
                    
                await asyncio.sleep(2) 
                
            self.duel_players.pop(ctx.channel.id, None)
            self.duel_hosts.pop(ctx.channel.id, None)
            return await ctx.send("🏁 **THE DUEL HAS ENDED!** GG everyone.")

        # ================================
        # PHASE 2: SOLO MODE (Fallback)
        # ================================
        if category not in data["words"] or not data["words"][category]:
            return await ctx.send(f"❌ Category `{category}` is empty or doesn't exist.")

        word = random.choice(data["words"][category])
        guessed_letters, wrong_guesses = [], 0

        def get_display_solo():
            d = ""
            for char in word:
                if char == " ": d += "   "
                elif char in guessed_letters: d += f"{char} "
                else: d += "_ "
            return d

        board_msg = await ctx.send(f"🎮 **Solo Hangman** | **{category.capitalize()}**\n{HANGMAN_PICS[wrong_guesses]}\n`{get_display_solo()}`\n\n*Type a letter! (90s limit)*")
        def check_solo(m): return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()

        while wrong_guesses < 6:
            try:
                user_msg = await self.bot.wait_for('message', check=check_solo, timeout=90.0)
                guess = user_msg.content.lower()
                if guess in guessed_letters:
                    await ctx.send(f"⚠️ You already guessed `{guess}`!", delete_after=3)
                    continue
                guessed_letters.append(guess)
                if guess not in word: wrong_guesses += 1
                
                display = get_display_solo()
                g_str = ", ".join(guessed_letters) if guessed_letters else "None"
                await board_msg.edit(content=f"🎮 **Solo Hangman** | **{category.capitalize()}**\n{HANGMAN_PICS[wrong_guesses]}\n`{display}`\n\n**Guessed:** {g_str}")
                
                if "_" not in display: return await ctx.send(f"🎉 **YOU SURVIVED!** The word was **{word.title()}**.")
            except asyncio.TimeoutError:
                return await ctx.send(f"⏰ **TIME'S UP!** You hang.\nThe word was **{word.title()}**.")
        await ctx.send(f"💀 **GAME OVER!** You hang.\nThe word was **{word.title()}**.")

async def setup(bot):
    await bot.add_cog(Hangman(bot))
