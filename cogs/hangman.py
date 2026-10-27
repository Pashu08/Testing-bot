# cogs/hangman.py
import discord
from discord.ext import commands
import random
import asyncio
from utils.db import load_db
from utils.art import HANGMAN_PICS

OWNER_ID = 756012403291848804

class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.duel_players = {}
        self.duel_hosts = {}

    @commands.command()
    async def hkick(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        data = load_db()
        mods = data.get(guild_id, {}).get("mods", [])
        
        host = self.duel_hosts.get(ctx.channel.id)
        is_admin = ctx.author.guild_permissions.administrator
        is_owner = ctx.author.id == OWNER_ID
        is_mod = ctx.author.id in mods
        is_host = ctx.author == host
        
        if not (is_admin or is_owner or is_mod or is_host):
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Only the Host or a Bot Admin can kick players.", color=discord.Color.red()))
            
        if ctx.channel.id in self.duel_players and member in self.duel_players[ctx.channel.id]:
            self.duel_players[ctx.channel.id].remove(member)
            await ctx.send(embed=discord.Embed(title="👢 Player Kicked", description=f"**{member.display_name}** was kicked from the lobby!", color=discord.Color.orange()))
        else:
            await ctx.send(embed=discord.Embed(title="⚠️ Not Found", description="That player is not in an active lobby here.", color=discord.Color.red()))

    @commands.command(name="hangman")
    async def play_hangman(self, ctx, category: str = None):
        if not category: 
            return await ctx.send(embed=discord.Embed(title="⚠️ Missing Category", description="Specify a category! (`.hangman general`, `.hangman duel`, `.hangman team`)", color=discord.Color.red()))
        category = category.lower()
        
        guild_id = str(ctx.guild.id)
        data = load_db()
        if guild_id not in data or "words" not in data[guild_id] or not data[guild_id]["words"]:
            return await ctx.send(embed=discord.Embed(title="❌ Word Bank Empty", description="No words have been added in this server yet! Use `.addword`.", color=discord.Color.red()))
            
        server_words = data[guild_id]["words"]

        def get_display(w, gl):
            d = ""
            for char in w:
                if char == " ": d += "   "
                elif char in gl: d += f"{char} "
                else: d += "_ "
            return d

        # ==========================================
        # MULTIPLAYER DRAFT WITH DROPDOWNS
        # ==========================================
        async def draft_for_player(p, drafting_for="someone else"):
            try:
                dm = await p.create_dm()
                
                class CategorySelect(discord.ui.Select):
                    def __init__(self, cats):
                        options = [discord.SelectOption(label=c.capitalize(), value=c) for c in cats[:25]]
                        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)
                    async def callback(self, interaction: discord.Interaction):
                        self.view.cat_choice = self.values[0]
                        self.disabled = True
                        await interaction.response.edit_message(content=f"✅ Selected Category: **{self.values[0].capitalize()}**", view=self.view)
                        self.view.stop()

                class CategoryView(discord.ui.View):
                    def __init__(self, cats):
                        super().__init__(timeout=60.0)
                        self.cat_choice = None
                        self.add_item(CategorySelect(cats))
                
                cats = list(server_words.keys())
                cat_view = CategoryView(cats)
                
                embed = discord.Embed(title="⚔️ THE DRAFT", description=f"You are picking a word for **{drafting_for}**!", color=discord.Color.gold())
                cat_msg = await dm.send(embed=embed, view=cat_view)
                await cat_view.wait()
                
                if cat_view.cat_choice is None:
                    chosen_cat = random.choice(cats)
                    await cat_msg.edit(content=f"⏳ Time's up! Auto-picked category: `{chosen_cat}`", embed=None, view=None)
                else:
                    chosen_cat = cat_view.cat_choice

                cat_words = server_words[chosen_cat]
                sample_size = min(25, len(cat_words))
                choices = random.sample(cat_words, sample_size)

                class WordSelect(discord.ui.Select):
                    def __init__(self, words):
                        options = [discord.SelectOption(label=w, value=w) for w in words]
                        super().__init__(placeholder="Choose the hardest word...", min_values=1, max_values=1, options=options)
                    async def callback(self, interaction: discord.Interaction):
                        self.view.word_choice = self.values[0]
                        self.disabled = True
                        await interaction.response.edit_message(content=f"✅ Locked in: **{self.values[0]}**. Head back to the server!", view=self.view)
                        self.view.stop()

                class WordView(discord.ui.View):
                    def __init__(self, words):
                        super().__init__(timeout=60.0)
                        self.word_choice = None
                        self.add_item(WordSelect(words))

                word_view = WordView(choices)
                word_msg = await dm.send("Now, select the exact word they have to guess:", view=word_view)
                await word_view.wait()

                if word_view.word_choice is None:
                    chosen_word = random.choice(choices)
                    await word_msg.edit(content=f"⏳ Time's up! Auto-picked: **{chosen_word}**. Head back to the server!", view=None)
                else:
                    chosen_word = word_view.word_choice
                    
                return chosen_word

            except discord.Forbidden:
                await ctx.send(embed=discord.Embed(title="⚠️ DMs Locked", description=f"{p.mention}, your DMs are locked! Auto-picking a word.", color=discord.Color.orange()))
                return random.choice(server_words[random.choice(list(server_words.keys()))])

        # ==========================================
        # TEAM VS TEAM MODE
        # ==========================================
        if category == "team":
            if ctx.channel.id in self.duel_players: 
                return await ctx.send(embed=discord.Embed(title="⚠️ Lobby Active", description="A game is already happening here!", color=discord.Color.red()))
            
            self.duel_hosts[ctx.channel.id] = ctx.author
            embed = discord.Embed(title="🚩 TEAM HANGMAN LOBBY", description="React ✋ to join!\nHost react ✅ to lock teams and start the draft.", color=discord.Color.gold())
            embed.set_footer(text=f"Host: {ctx.author.display_name}")
            lobby_msg = await ctx.send(embed=embed)
            await lobby_msg.add_reaction("✋")
            await lobby_msg.add_reaction("✅")
            
            def check_start(reaction, user):
                return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == lobby_msg.id
                
            try: await self.bot.wait_for('reaction_add', timeout=300.0, check=check_start)
            except asyncio.TimeoutError:
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send(embed=discord.Embed(title="⏳ Timeout", description="Lobby timed out.", color=discord.Color.dark_gray()))
                
            lobby_msg = await ctx.channel.fetch_message(lobby_msg.id)
            players = []
            for reaction in lobby_msg.reactions:
                if str(reaction.emoji) == "✋":
                    async for user in reaction.users():
                        if not user.bot and user not in players: players.append(user)
                            
            if len(players) < 2:
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send(embed=discord.Embed(title="⚠️ Error", description="Need at least 2 players to form teams!", color=discord.Color.red()))
                
            self.duel_players[ctx.channel.id] = players
            random.shuffle(players)
            mid = max(1, len(players) // 2)
            team_red, team_blue = players[:mid], players[mid:]
            
            team_embed = discord.Embed(title="🚀 TEAMS LOCKED!", description="Setting up War Rooms...", color=discord.Color.green())
            team_embed.add_field(name="🍎 Team Red", value=", ".join([p.display_name for p in team_red]), inline=False)
            team_embed.add_field(name="🫐 Team Blue", value=", ".join([p.display_name for p in team_blue]), inline=False)
            await ctx.send(embed=team_embed)
            
            try:
                thread_red = await ctx.channel.create_thread(name="🍎 Team Red Strategy", type=discord.ChannelType.private_thread)
                for p in team_red: await thread_red.add_user(p)
                thread_blue = await ctx.channel.create_thread(name="🫐 Team Blue Strategy", type=discord.ChannelType.private_thread)
                for p in team_blue: await thread_blue.add_user(p)
            except Exception:
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send(embed=discord.Embed(title="❌ CRASH", description="The bot lacks the 'Create Private Threads' permission!", color=discord.Color.red()))

            red_cap, blue_cap = team_red[0], team_blue[0]
            await ctx.send(embed=discord.Embed(title="📱 Draft Phase", description=f"{red_cap.mention} and {blue_cap.mention}, check your DMs! You have 60s to draft words.", color=discord.Color.gold()))
            
            tasks = [draft_for_player(red_cap, "Team Blue"), draft_for_player(blue_cap, "Team Red")]
            results = await asyncio.gather(*tasks)
            word_for_blue, word_for_red = results[0], results[1]
            
            state = {
                "red": {"word": word_for_red, "guessed": [], "wrong": 0, "players": team_red, "idx": 0, "name": "Team Red", "emoji": "🍎", "color": discord.Color.red()},
                "blue": {"word": word_for_blue, "guessed": [], "wrong": 0, "players": team_blue, "idx": 0, "name": "Team Blue", "emoji": "🫐", "color": discord.Color.blue()}
            }
            
            current_turn = "red"
            board_msg = await ctx.send(embed=discord.Embed(title="⚔️ LET THE WAR BEGIN! ⚔️", color=discord.Color.dark_gray()))
            game_over = False
            
            while not game_over:
                ts = state[current_turn]
                guesser = ts["players"][ts["idx"]]
                display = get_display(ts["word"], ts["guessed"])
                g_str = ", ".join(ts["guessed"]) if ts["guessed"] else "None"
                
                board_embed = discord.Embed(title=f"{ts['emoji']} {ts['name']}'s Turn!", color=ts["color"])
                board_embed.description = f"```text\n{HANGMAN_PICS[ts['wrong']]}\n```\n`{display}`\n\n**Guessed:** {g_str}\n\n👉 {guesser.mention}, you are the **Designated Guesser**! Type a letter OR guess the full word (Hero Guess)!"
                await board_msg.edit(embed=board_embed)
                
                def check_team(m): return m.author == guesser and m.channel == ctx.channel and (m.content.isalpha() or " " in m.content)
                
                try:
                    user_msg = await self.bot.wait_for('message', check=check_team, timeout=90.0)
                    guess = user_msg.content.lower()
                    try: await user_msg.delete()
                    except: pass
                    
                    if len(guess) > 1: # HERO GUESS
                        if guess == ts["word"]:
                            await ctx.send(embed=discord.Embed(title="🏆 HERO GUESS SUCCESS!", description=f"{guesser.display_name} correctly guessed **{ts['word'].title()}**!\n**{ts['name']} WINS THE GAME!**", color=discord.Color.green()))
                            game_over = True
                        else:
                            ts["wrong"] += 2
                            await ctx.send(embed=discord.Embed(title="🚨 HERO GUESS FAILED!", description=f"`{guess}` was wrong. {ts['name']} takes **2 strikes**!", color=discord.Color.red()), delete_after=5)
                    else: # SINGLE LETTER
                        if guess in ts["guessed"]:
                            await ctx.send(embed=discord.Embed(description=f"⚠️ Your team already guessed `{guess}`!", color=discord.Color.orange()), delete_after=3)
                            continue 
                        ts["guessed"].append(guess)
                        if guess not in ts["word"]:
                            ts["wrong"] += 1
                            await ctx.send(embed=discord.Embed(description="❌ **Wrong Letter!**", color=discord.Color.red()), delete_after=3)
                            
                    if not game_over:
                        if "_" not in get_display(ts["word"], ts["guessed"]):
                            await ctx.send(embed=discord.Embed(title=f"🎉 {ts['name']} SOLVED IT!", description=f"The word was **{ts['word'].title()}**.\n**{ts['name']} WINS!**", color=discord.Color.green()))
                            game_over = True
                        elif ts["wrong"] >= 6:
                            enemy = "blue" if current_turn == "red" else "red"
                            await ctx.send(embed=discord.Embed(title=f"💀 {ts['name']} HANGED!", description=f"Their word was **{ts['word'].title()}**.\n**{state[enemy]['name']} WINS BY SURVIVAL!**", color=discord.Color.red()))
                            game_over = True
                            
                except asyncio.TimeoutError:
                    ts["wrong"] += 1
                    await ctx.send(embed=discord.Embed(description=f"⏰ **TIME'S UP!** {guesser.display_name} went AFK. {ts['name']} takes 1 strike!", color=discord.Color.red()), delete_after=5)
                    if ts["wrong"] >= 6:
                        enemy = "blue" if current_turn == "red" else "red"
                        await ctx.send(embed=discord.Embed(title=f"💀 {ts['name']} HANGED FROM AFK!", description=f"**{state[enemy]['name']} WINS!**", color=discord.Color.red()))
                        game_over = True
                
                if not game_over:
                    ts["idx"] = (ts["idx"] + 1) % len(ts["players"])
                    current_turn = "blue" if current_turn == "red" else "red"
                    await board_msg.delete()
                    board_msg = await ctx.send(embed=discord.Embed(description="🔄 Swapping sides...", color=discord.Color.dark_gray()))
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
            if ctx.channel.id in self.duel_players: 
                return await ctx.send(embed=discord.Embed(title="⚠️ Lobby Active", description="A duel is already happening here!", color=discord.Color.red()))
            
            self.duel_hosts[ctx.channel.id] = ctx.author
            embed = discord.Embed(title="⚔️ HANGMAN DUEL LOBBY", description="React ✋ to join!\nHost react ✅ to lock the lobby and start.", color=discord.Color.gold())
            embed.set_footer(text=f"Host: {ctx.author.display_name}")
            lobby_msg = await ctx.send(embed=embed)
            await lobby_msg.add_reaction("✋")
            await lobby_msg.add_reaction("✅")
            
            def check_start(reaction, user): return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == lobby_msg.id
                
            try: await self.bot.wait_for('reaction_add', timeout=300.0, check=check_start)
            except asyncio.TimeoutError:
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send(embed=discord.Embed(title="⏳ Timeout", description="Lobby timed out.", color=discord.Color.dark_gray()))
                
            lobby_msg = await ctx.channel.fetch_message(lobby_msg.id)
            players = []
            for reaction in lobby_msg.reactions:
                if str(reaction.emoji) == "✋":
                    async for user in reaction.users():
                        if not user.bot and user not in players: players.append(user)
                            
            if len(players) < 2:
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send(embed=discord.Embed(title="⚠️ Error", description="Need at least 2 players!", color=discord.Color.red()))
                
            self.duel_players[ctx.channel.id] = players
            await ctx.send(embed=discord.Embed(title="🚀 DUEL STARTING!", description=f"{len(players)} players locked in.\n\n📱 **CHECK YOUR DMs!** You have 60s to draft words.", color=discord.Color.green()))
            
            tasks = [draft_for_player(p, "someone else") for p in players]
            results = await asyncio.gather(*tasks)
            
            current_players = self.duel_players.get(ctx.channel.id, [])
            if len(current_players) < 2:
                self.duel_players.pop(ctx.channel.id, None)
                self.duel_hosts.pop(ctx.channel.id, None)
                return await ctx.send(embed=discord.Embed(title="⚠️ Aborted", description="Too many players left. Duel aborted.", color=discord.Color.red()))
                
            active_results, final_players = [], []
            for i, res in enumerate(results):
                if res != "kicked" and players[i] in current_players:
                    active_results.append(res)
                    final_players.append(players[i])
                    
            assigned_words = [None] * len(final_players)
            for i in range(len(final_players)): assigned_words[i] = active_results[(i + 1) % len(final_players)]
                
            await ctx.send(embed=discord.Embed(title="🎲 DRAFT COMPLETE", description="Words are secretly shuffled.\n\n🔥 **LET THE HOT SEATS BEGIN!** 🔥", color=discord.Color.gold()))
            
            player_states = [{"player": p, "word": assigned_words[i], "guessed": [], "wrong": 0, "status": "playing"} for i, p in enumerate(final_players)]
            turn_idx = 0
            
            board_msg = await ctx.send(embed=discord.Embed(description="Setting up boards...", color=discord.Color.dark_gray()))
            
            while any(s["status"] == "playing" for s in player_states):
                while player_states[turn_idx]["status"] != "playing": turn_idx = (turn_idx + 1) % len(player_states)
                    
                state = player_states[turn_idx]
                p = state["player"]
                
                if p not in self.duel_players.get(ctx.channel.id, []):
                    await ctx.send(embed=discord.Embed(description=f"⏭️ **{p.display_name}** was kicked! Skipping their board.", color=discord.Color.orange()))
                    state["status"] = "kicked"
                    turn_idx = (turn_idx + 1) % len(player_states)
                    continue

                display = get_display(state["word"], state["guessed"])
                g_str = ", ".join(state["guessed"]) if state["guessed"] else "None"
                
                b_embed = discord.Embed(title=f"🔥 HOT SEAT: {p.display_name}'s Turn!", color=discord.Color.purple())
                b_embed.description = f"```text\n{HANGMAN_PICS[state['wrong']]}\n```\n`{display}`\n\n**Guessed:** {g_str}\n\n👉 {p.mention}, type a letter to guess!"
                await board_msg.edit(embed=b_embed)
                
                def check_guess_duel(m): return m.author == p and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()
                
                try:
                    user_msg = await self.bot.wait_for('message', check=check_guess_duel, timeout=90.0)
                    guess = user_msg.content.lower()
                    try: await user_msg.delete()
                    except: pass 
                    
                    if guess in state["guessed"]:
                        await ctx.send(embed=discord.Embed(description=f"⚠️ {p.mention}, you already guessed `{guess}`!", color=discord.Color.orange()), delete_after=3)
                        continue 
                        
                    state["guessed"].append(guess)
                    turn_pass = False
                    
                    if guess not in state["word"]:
                        state["wrong"] += 1
                        turn_pass = True 
                        await ctx.send(embed=discord.Embed(description=f"❌ **Wrong!** {p.display_name} passes the controller!", color=discord.Color.red()), delete_after=3)
                        
                    display = get_display(state["word"], state["guessed"])
                    if "_" not in display:
                        state["status"] = "won"
                        await ctx.send(embed=discord.Embed(title="🎉 BOARD SURVIVED!", description=f"**{p.display_name}** completed their word: **{state['word'].title()}**.", color=discord.Color.green()))
                        turn_pass = True 
                    elif state["wrong"] >= 6:
                        state["status"] = "lost"
                        await ctx.send(embed=discord.Embed(title="💀 HANGED!", description=f"**{p.display_name}** died! Their word was **{state['word'].title()}**.", color=discord.Color.red()))
                        turn_pass = True 

                    if turn_pass:
                        turn_idx = (turn_idx + 1) % len(player_states)
                        if any(s["status"] == "playing" for s in player_states):
                            await board_msg.delete()
                            board_msg = await ctx.send(embed=discord.Embed(description="🔄 Swapping boards...", color=discord.Color.dark_gray()))
                            await asyncio.sleep(1)
                            
                except asyncio.TimeoutError:
                    state["status"] = "lost"
                    await ctx.send(embed=discord.Embed(title="⏰ TIME'S UP!", description=f"**{p.display_name}** AFK'd and died! Word: **{state['word'].title()}**.", color=discord.Color.red()))
                    turn_idx = (turn_idx + 1) % len(player_states)
                    if any(s["status"] == "playing" for s in player_states):
                        await board_msg.delete()
                        board_msg = await ctx.send(embed=discord.Embed(description="🔄 Swapping boards...", color=discord.Color.dark_gray()))
                        await asyncio.sleep(1)

            if board_msg:
                try: await board_msg.delete()
                except: pass

            self.duel_players.pop(ctx.channel.id, None)
            self.duel_hosts.pop
