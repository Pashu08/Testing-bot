import discord
from discord.ext import commands

class Guide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def guide(self, ctx, game: str = None):
        if not game:
            return await ctx.send(embed=discord.Embed(title="⚠️ Error", description="Please specify a guide! Options: `,guide hangman`, `,guide imposter`, or `,guide admin`", color=discord.Color.orange()))

        game = game.lower()

        if game == "hangman":
            embed = discord.Embed(title="📖 How to Play: Hangman", description="Guess the hidden word before you run out of lives!", color=discord.Color.green())
            embed.add_field(name="The Rules", value="**1.** Type `,hangman <category>` to start.\n**2.** Type a single letter in chat to guess.\n**3.** Type the full word to guess it instantly.\n**4.** If you guess wrong too many times, you lose.")
            await ctx.send(embed=embed)
            
        elif game == "imposter":
            embed = discord.Embed(title="📖 How to Play: Imposter", description="Find the player who has the wrong word!", color=discord.Color.red())
            embed.add_field(name="The Rules", value="**1.** Type `,imposter` to open the lobby.\n**2.** Players click **Join**. The host clicks **Start** (minimum 3 players).\n**3.** Everyone is DM'd a secret word, but the Imposter gets a *different* word.\n**4.** You have 2 minutes in chat to drop subtle hints proving you know the word.\n**5.** A voting dropdown appears. Vote for the Imposter. If the Imposter survives, they win!")
            await ctx.send(embed=embed)

        elif game == "admin":
            embed = discord.Embed(title="⚙️ Admin Setup Guide", description="How to manage the game databases.", color=discord.Color.dark_theme())
            
            hangman_guide = (
                "`,addword <category> <word>` - Adds a single word.\n"
                "`,addwords <category> <word1, word2, ...>` - Mass adds words using commas.\n"
                "`,delword <category> <word>` - Removes a word.\n"
                "`,rencat <old> <new>` - Renames a category.\n"
                "`,wordlist <category>` - Privately view all words in a category."
            )
            embed.add_field(name="Hangman Database", value=hangman_guide, inline=False)

            imposter_guide = (
                "`,addpair <innocent_word>, <imposter_word>` - Adds a new pair. **You must use a comma between the two words!**\n"
                "`,delpair <word>` - Deletes the pair containing that word.\n"
                "`,pairs` - Checks how many pairs are currently loaded."
            )
            embed.add_field(name="Imposter Database", value=imposter_guide, inline=False)
            
            await ctx.send(embed=embed)
            
        else:
            await ctx.send(embed=discord.Embed(title="⚠️ Error", description="I don't have a guide for that! Try `,guide imposter`, `,guide hangman`, or `,guide admin`.", color=discord.Color.orange()))

async def setup(bot):
    await bot.add_cog(Guide(bot))
