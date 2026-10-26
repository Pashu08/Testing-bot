# cogs/hangman.py
import discord
from discord.ext import commands
import random
import asyncio
from utils.db import load_db
from utils.art import HANGMAN_PICS

class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.duel_players = {}
        self.duel_hosts = {}

    @commands.command(name="help")
    async def custom_help(self, ctx):
        embed = discord.Embed(title="🎮 Hangman Bot Commands", color=discord.Color.blue())
        embed.add_field(name="🗡️ Play", value="`.hangman [category]` - Solo\n`.hangman duel` - Multiplayer Hot Seat\n`.hangman team` - Team vs. Team", inline=False)
        embed.add_field(name="📚 Word Bank", value="`.categories`, `.addword [cat] [word]`", inline=False)
        embed.add_field(name="🛡️ Admin/Host", value="`.delword`, `.wordlist`, `.hkick @user`", inline=False)
        embed.set_footer(text="Created by Pashu")
        await ctx.send(embed=embed)

    @commands.command(name="guide")
    async def game_guide(self, ctx, game_name: str = None):
        if game_name is None or game_name.lower() != "hangman":
            return await ctx.send("📚 **Available Guides:**\n- `hangman`\nUsage: `.guide hangman`")
        embed = discord.Embed(title="🎮 THE OFFICIAL HANGMAN SURVIVAL GUIDE", color=discord.Color.dark_red())
        embed.add_field(name="1. The Word Bank", value="Type `.addword [cat] [word]` to add words to your server's database.", inline=False)
        embed.add_field(name="2. Solo & Duel", value="`.hangman [category]` to play alone.\n`.hangman duel` for Hot Seat free-for-all mode.", inline=False)
        embed.add_field(name="3. TEAM VS TEAM", value="Type `.hangman team`.\nThe bot splits you into **Red 🍎** and **Blue 🫐** and makes secret Strategy Threads for you to talk in.", inline=False)
        embed.add_field(name="4. Team Rules", value="**Designated Guesser**: You have 90s to talk in your thread, but ONLY the pinged player can type the guess in the main channel.\n**Hero Guess**: Type the FULL word to instantly win. But if you misspell it, your team takes 2 penalty strikes!", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def hkick(self, ctx, member: discord.Member):
        host = self.duel_hosts.get(ctx.channel.id)
        if not ctx.author.guild_permissions.administrator and ctx.author != host:
            return await ctx.send("❌ Only the Host or an Admin can kick players.")
        if ctx.channel.id in self.duel_players and member in self.duel_players[ctx.channel.id]:
            self.duel_players[ctx.channel.id].remove(member)
            await ctx.send(f"👢 **{member.display_name}** was kicked from the lobby!")
        else:
            await ctx.send("⚠️ That player is not in an active lobby here.")

    @commands.command(name="hangman")
    async def play_hangman(self, ctx, category: str = None):
        if not category: return await ctx.send("⚠️ Specify a category! (`.hangman general`, `.hangman duel`, `.hangman team`)")
        category = category.lower()
        
        guild_id = str(ctx.guild.id)
        data = load_db()
        if guild_id not in data or "words" not in data[guild_id] or not data[guild_id]["words"]:
            return await ctx.send("❌ No words have been added in this server yet! Use `.addword`.")
            
        server_words = data[guild_id]["words"]

        def get_display(w, gl):
            d = ""
            for char in w:
                if char == " ": d += "   "
                elif char in gl: d += f"{char} "
                else: d += "_ "
            return d

        async def draft_for_player(p, drafting_for="someone else"):
            try:
                dm = await p.create_dm()
                await dm.send(f"⚔️ **THE DRAFT** ⚔️\nYou are picking a word for **{drafting_for}**!\nReply with a category name from the database.")
                def check_msg(m): return m.author == p and m.channel == dm
                try:
                    cat_msg = await self.bot.wait_for('message', check=check_msg, timeout=60.0)
                    cat = cat_msg.content.lower()
                except asyncio.TimeoutError:
                    cat = random.choice(list(server_words.keys()))
                    await dm.send(f"⏳ Time's up! Auto-picked category: `{cat}`")
                    
                if cat not in server_words or not server_words[cat]:
                    cat = random.choice(list(server_words.keys()))
                    await dm.send(f"⚠️ Invalid category! Auto-picked: `{cat}`")
                    
                cat_words = server_words[cat]
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
                await ctx.send(f"⚠️ {p.mention}, your DMs are locked! Auto-picking a word.")
                return random.choice(server_words[random.choice(list(server_words.keys()))])

        # ==========================================
        # TEAM VS TEAM MODE
        # ==========================================
        if category == "team":
            if ctx.channel.id in self.duel_players: return await ctx.send("⚠️ A game is already happening here!")
            
            self.duel_hosts[ctx.channel.id] = ctx.author
            lobby_msg = await ctx.send(f"🚩 **TEAM HANGMAN LOBBY** 🚩\n\nReact ✋ to join!\nHost (`{ctx.author.display_name}`) react ✅ to start the draft.")
            await lobby_msg.add_reaction("✋")
            await lobby_msg.add_reaction("✅")
            
            def check_start(reaction, user):
                return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == lobby_msg.id
                
            try: await self.bot.wait_for('reaction_add', timeout=300.0, check=check_start)
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
                return await ctx.send("⚠️ Need at least 2 players to form teams!")
                
            self.duel_players[ctx.channel.id] = players
            random.shuffle(players)
            mid = max(1, len(players) // 2)
            team_red = players[:mid]
            team_blue = players[mid:]
            
            await ctx.send(f"🚀 **TEAMS LOCKED!**\n🍎 **Team Red**: {', '.join([p.display_name for p in team_red])}\n🫐 **Team Blue**: {', '.join([p.display_name for p in team_blue])}\n\nSetting up War Rooms...")
            
            try:
                thread_red = await ctx.channel.create_thread(name="🍎 Team Red Strategy", type=discord.ChannelType.private_thread)
                for p in team_red: await thread_red.add_user(p)
                
                thread_blue = await ctx.channel.create_thread(name="🫐 Team Blue Strategy", type=discord.ChannelType.private_thread)
                for p in team_blue: await thread_blue.add_user(p)
            except Exception:
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send("❌ **CRASH:** The bot lacks the 'Create Private Threads' permission in this server!")

            red_cap, blue_cap = team_red[0], team_blue[0]
            await ctx.send(f"📱 {red_cap.mention} and {blue_cap.mention}, check your DMs! You have 60s to draft words for the enemy team.")
            
            tasks = [draft_for_player(red_cap, "Team Blue"), draft_for_player(blue_cap, "Team Red")]
            results = await asyncio.gather(*tasks)
            word_for_blue, word_for_red = results[0], results[1]
            
            state = {
                "red": {"word": word_for_red, "guessed": [], "wrong": 0, "players": team_red, "idx": 0, "name": "🍎 Team Red", "emoji": "🍎"},
                "blue": {"word": word_for_blue, "guessed": [], "wrong": 0, "players": team_blue, "idx": 0, "name": "🫐 Team Blue", "emoji": "🫐"}
            }
            
            current_turn = "red"
            board_msg = await ctx.send("⚔️ **LET THE WAR BEGIN!** ⚔️")
            game_over = False
            
            while not game_over:
                ts = state[current_turn]
                guesser = ts["players"][ts["idx"]]
                
                display = get_display(ts["word"], ts["guessed"])
                g_str = ", ".join(ts["guessed"]) if ts["guessed"] else "None"
                
                content = f"{ts['emoji']} **{ts['name']}'s Turn!**\n{HANGMAN_PICS[ts['wrong']]}\n`{display}`\n\n**Guessed:** {g_str}\n\n👉 {guesser.mention}, you are the **Designated Guesser**! Type a letter OR guess the full word (Hero Guess)!"
                await board_msg.edit(content=content)
                
                def check_team(m):
                    return m.author == guesser and m.channel == ctx.channel and (m.content.isalpha() or " " in m.content)
                
                try:
                    user_msg = await self.bot.wait_for('message', check=check_team, timeout=90.0)
                    guess = user_msg.content.lower()
                    try: await user_msg.delete()
                    except: pass
                    
                    if len(guess) > 1:
                        if guess == ts["word"]:
                            await ctx.send(f"🏆 **HERO GUESS SUCCESS!** {guesser.display_name} correctly guessed **{ts['word'].title()}**!\n**{ts['name']} WINS THE GAME!**")
                            game_over = True
                        else:
                            ts["wrong"] += 2
                            await ctx.send(f"🚨 **HERO GUESS FAILED!** `{guess}` was wrong. {ts['name']} takes **2 strikes**!", delete_after=5)
                    else:
                        if guess in ts["guessed"]:
                            await ctx.send(f"⚠️ Your team already guessed `{guess}`!", delete_after=3)
                            continue 
                        ts["guessed"].append(guess)
                        if guess not in ts["word"]:
                            ts["wrong"] += 1
                            await ctx.send(f"❌ **Wrong Letter!**", delete_after=3)
                            
                    if not game_over:
                        if "_" not in get_display(ts["word"], ts["guessed"]):
                            await ctx.send(f"🎉 **{ts['name']} SOLVED IT!** The word was **{ts['word'].title()}**.\n**{ts['name']} WINS!**")
                            game_over = True
                        elif ts["wrong"] >= 6:
                            enemy = "blue" if current_turn == "red" else "red"
                            await ctx.send(f"💀 **{ts['name']} HANGED!** Their word was **{ts['word'].title()}**.\n**{state[enemy]['name']} WINS BY SURVIVAL!**")
                            game_over = True
                            
                except asyncio.TimeoutError:
                    ts["wrong"] += 1
                    await ctx.send(f"⏰ **TIME'S UP!** {guesser.display_name} went AFK. {ts['name']} takes 1 strike!", delete_after=5)
                    if ts["wrong"] >= 6:
                        enemy = "blue" if current_turn == "red" else "red"
                        await ctx.send(f"💀 **{ts['name']} HANGED FROM AFK!**\n**{state[enemy]['name']} WINS!**")
                        game_over = True
                
                if not game_over:
                    ts["idx"] = (ts["idx"] + 1) % len(ts["players"])
                    current_turn = "blue" if current_turn == "red" else "red"
                    await board_msg.delete()
                    board_msg = await ctx.send("Swapping sides...")
                    await asyncio.sleep(1)
            
            self.duel_players.pop(ctx.channel.id, None)
            self.duel_hosts.pop(ctx.channel.id, None)
            try: await board_msg.delete()
            except: pass
            try: await thread_red.delete()
            except: pass
            try: await thread_blue.delete()
            except: pass
            return

        # ==========================================
        # DUEL MODE
        # ==========================================
        if category == "duel":
            if ctx.channel.id in self.duel_players: return await ctx.send("⚠️ A duel is already happening here!")
            
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
            
            tasks = [draft_for_player(p, "someone else") for p in players]
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
                    
            assigned_words = [None] * len(final_players)
            for i in range(len(final_players)):
                assigned_words[i] = active_results[(i + 1) % len(final_players)]
                
            await ctx.send("🎲 **THE DRAFT IS COMPLETE.** Words are secretly shuffled.\n\n🔥 **LET THE HOT SEATS BEGIN!** 🔥")
            
            player_states = [{"player": p, "word": assigned_words[i], "guessed": [], "wrong": 0, "status": "playing"} for i, p in enumerate(final_players)]
            turn_idx = 0
            
            board_msg = await ctx.send("Setting up boards...")
            
            while any(s["status"] == "playing" for s in player_states):
                while player_states[turn_idx]["status"] != "playing":
                    turn_idx = (turn_idx + 1) % len(player_states)
                    
                state = player_states[turn_idx]
                p = state["player"]
                
                if p not in self.duel_players.get(ctx.channel.id, []):
                    await ctx.send(f"⏭️ **{p.display_name}** was kicked! Skipping their board.")
                    state["status"] = "kicked"
                    turn_idx = (turn_idx + 1) % len(player_states)
                    continue

                display = get_display(state["word"], state["guessed"])
                g_str = ", ".join(state["guessed"]) if state["guessed"] else "None"
                
                await board_msg.edit(content=f"🔥 **HOT SEAT: {p.mention}'s Turn!**\n{HANGMAN_PICS[state['wrong']]}\n`{display}`\n\n**Guessed:** {g_str}\n*Type a letter to guess!*")
                
                def check_guess_duel(m):
                    return m.author == p and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()
                
                try:
                    user_msg = await self.bot.wait_for('message', check=check_guess_duel, timeout=90.0)
                    guess = user_msg.content.lower()
                    
                    try: await user_msg.delete()
                    except: pass 
                    
                    if guess in state["guessed"]:
                        await ctx.send(f"⚠️ {p.mention}, you already guessed `{guess}`!", delete_after=3)
                        continue 
                        
                    state["guessed"].append(guess)
                    turn_pass = False
                    
                    if guess not in state["word"]:
                        state["wrong"] += 1
                        turn_pass = True 
                        await ctx.send(f"❌ **Wrong!** {p.display_name} passes the controller!", delete_after=3)
                        
                    display = get_display(state["word"], state["guessed"])
                    if "_" not in display:
                        state["status"] = "won"
                        await ctx.send(f"🎉 **{p.display_name} SURVIVED THEIR BOARD!** The word was **{state['word'].title()}**.")
                        turn_pass = True 
                        
                    elif state["wrong"] >= 6:
                        state["status"] = "lost"
                        await ctx.send(f"💀 **{p.display_name} HANGED!** Their word was **{state['word'].title()}**.")
                        turn_pass = True 

                    if turn_pass:
                        turn_idx = (turn_idx + 1) % len(player_states)
                        if any(s["status"] == "playing" for s in player_states):
                            await board_msg.delete()
                            board_msg = await ctx.send("Swapping boards...")
                            await asyncio.sleep(1)
                            
                except asyncio.TimeoutError:
                    state["status"] = "lost"
                    await ctx.send(f"⏰ **TIME'S UP!** {p.display_name} AFK'd and died! Word: **{state['word'].title()}**.")
                    turn_idx = (turn_idx + 1) % len(player_states)
                    if any(s["status"] == "playing" for s in player_states):
                        await board_msg.delete()
                        board_msg = await ctx.send("Swapping boards...")
                        await asyncio.sleep(1)

            if board_msg:
                try: await board_msg.delete()
                except: pass

            self.duel_players.pop(ctx.channel.id, None)
            self.duel_hosts.pop(ctx.channel.id, None)
            return await ctx.send("🏁 **THE DUEL HAS ENDED!** Great game everyone.")

        # ==========================================
        # SOLO MODE
        # ==========================================
        if category not in server_words or not server_words[category]:
            return await ctx.send(f"❌ Category `{category}` is empty or doesn't exist in this server.")

        word = random.choice(server_words[category])
        guessed_letters, wrong_guesses = [], 0

        board_msg = await ctx.send(f"🎮 **Solo Hangman** | **{category.capitalize()}**\n{HANGMAN_PICS[wrong_guesses]}\n`{get_display(word, guessed_letters)}`\n\n*Type a letter! (90s limit)*")
        def check_solo(m): return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()

        while wrong_guesses < 6:
            try:
                user_msg = await self.bot.wait_for('message', check=check_solo, timeout=90.0)
                guess = user_msg.content.lower()
                
                try: await user_msg.delete()
                except: pass

                if guess in guessed_letters:
                    await ctx.send(f"⚠️ You already guessed `{guess}`!", delete_after=3)
                    continue
                guessed_letters.append(guess)
                if guess not in word: wrong_guesses += 1
                
                display = get_display(word, guessed_letters)
                g_str = ", ".join(guessed_letters) if guessed_letters else "None"
                await board_msg.edit(content=f"🎮 **Solo Hangman** | **{category.capitalize()}**\n{HANGMAN_PICS[wrong_guesses]}\n`{display}`\n\n**Guessed:** {g_str}")
                
                if "_" not in display: return await ctx.send(f"🎉 **YOU SURVIVED!** The word was **{word.title()}**.")
            except asyncio.TimeoutError:
                return await ctx.send(f"⏰ **TIME'S UP!** You hang.\nThe word was **{word.title()}**.")
        await ctx.send(f"💀 **GAME OVER!** You hang.\nThe word was **{word.title()}**.")

async def setup(bot):
    await bot.add_cog(Hangman(bot))
