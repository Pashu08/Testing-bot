import discord
from discord.ext import commands
from utils.imposter_db import load_imposter_db
import random
import asyncio

class ImposterLobby(discord.ui.View):
    def __init__(self, host):
        super().__init__(timeout=120)
        self.host = host
        self.players = []
        self.started = False

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.green, custom_id="join_btn")
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            return await interaction.response.send_message("You already joined!", ephemeral=True)
        self.players.append(interaction.user)
        await interaction.response.send_message("Joined!", ephemeral=True)
        embed = interaction.message.embeds[0]
        embed.description = f"**Players ({len(self.players)}):**\n" + "\n".join([p.name for p in self.players])
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.blurple, custom_id="start_btn")
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            return await interaction.response.send_message("Only the host can start!", ephemeral=True)
        if len(self.players) < 3:
            return await interaction.response.send_message("Need at least 3 players!", ephemeral=True)
        self.started = True
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)
        self.stop()
        await interaction.response.defer()

class ImposterVote(discord.ui.View):
    def __init__(self, players):
        super().__init__(timeout=60)
        self.players = players
        self.votes = {} 
        options = [discord.SelectOption(label=p.name, value=str(p.id)) for p in players]
        self.select = discord.ui.Select(placeholder="Vote for the Imposter...", options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user not in self.players:
            return await interaction.response.send_message("You aren't playing!", ephemeral=True)
        self.votes[interaction.user.id] = int(self.select.values[0])
        await interaction.response.send_message("Vote locked!", ephemeral=True)
        if len(self.votes) == len(self.players): self.stop()

class ImposterGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def imposter(self, ctx):
        data = load_imposter_db()
        guild_pairs = data.get(str(ctx.guild.id), {}).get("pairs", [])
        if not guild_pairs:
            return await ctx.send("❌ No word pairs set! Use `,addpair` first.")
        
        embed = discord.Embed(title="🕵️ Imposter Game", description="Waiting for players... (Min 3)", color=discord.Color.red())
        view = ImposterLobby(host=ctx.author)
        lobby_msg = await ctx.send(embed=embed, view=view)
        
        await view.wait()
        if not view.started: return await ctx.send("Lobby cancelled or timed out.")

        players = view.players
        
        # Shuffle the chosen pair so the Imposter word is completely random
        chosen_pair = list(random.choice(guild_pairs))
        random.shuffle(chosen_pair)
        innocent_word, imposter_word = chosen_pair[0], chosen_pair[1]
        
        imposter_player = random.choice(players)
        
        for p in players:
            try:
                if p == imposter_player:
                    await p.send(f"🕵️ **YOU ARE THE IMPOSTER!**\nWord: **{imposter_word}**")
                else:
                    await p.send(f"👥 **YOU ARE INNOCENT!**\nWord: **{innocent_word}**")
            except discord.Forbidden:
                return await ctx.send(f"⚠️ Could not DM {p.mention}! Game cancelled.")

        await ctx.send("🕵️ **Roles sent!** You have **2 minutes** to drop hints in chat.\n*Timer starting...*")
        await asyncio.sleep(120) 
        
        await ctx.send("⏰ **Time is up!** Select the Imposter from the dropdown. You have 60 seconds!")
        vote_view = ImposterVote(players)
        vote_msg = await ctx.send(view=vote_view)
        await vote_view.wait()
        
        for child in vote_view.children: child.disabled = True
        await vote_msg.edit(view=vote_view)

        if not vote_view.votes: return await ctx.send("Nobody voted! **Imposter wins!**")

        vote_counts = {}
        for voted_id in vote_view.votes.values():
            vote_counts[voted_id] = vote_counts.get(voted_id, 0) + 1
        
        max_votes = max(vote_counts.values())
        max_candidates = [uid for uid, count in vote_counts.items() if count == max_votes]
        
        embed = discord.Embed(title="🗳️ Results", color=discord.Color.gold())
        embed.add_field(name="Real Imposter:", value=imposter_player.mention, inline=False)
        
        if len(max_candidates) > 1:
            embed.description = "It was a tie!"
            embed.add_field(name="Result", value="🏆 **Imposter wins!**", inline=False)
        elif max_candidates[0] == imposter_player.id:
            embed.description = "The town voted out the Imposter!"
            embed.add_field(name="Result", value="🏆 **Innocents win!**", inline=False)
        else:
            embed.description = "The town voted out an innocent!"
            embed.add_field(name="Result", value="🏆 **Imposter wins!**", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ImposterGame(bot))
