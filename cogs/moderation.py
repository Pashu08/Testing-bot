# cogs/moderation.py
import discord
from discord.ext import commands

OWNER_ID = 756012403291848804

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # This dictionary caches the last deleted message per channel
        self.snipes = {}

    # ==========================
    # SNIPE SYSTEM
    # ==========================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # We ignore bot deletions so it only snipes real humans
        if message.author.bot:
            return
        
        # Save the deleted message to the channel's ID cache
        self.snipes[message.channel.id] = message

    @commands.command()
    async def snipe(self, ctx):
        message = self.snipes.get(ctx.channel.id)
        
        if not message:
            return await ctx.send(embed=discord.Embed(title="🔫 Nothing to Snipe!", description="No recently deleted messages found in this channel.", color=discord.Color.red()))
            
        embed = discord.Embed(description=message.content, color=discord.Color.purple())
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.set_footer(text="Sniped by " + ctx.author.display_name)
        embed.timestamp = message.created_at
        
        await ctx.send(embed=embed)

    # ==========================
    # PURGE SYSTEM
    # ==========================
    @commands.command()
    async def purge(self, ctx, amount: int = 0, member: discord.Member = None):
        if not ctx.author.guild_permissions.manage_messages and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="You need the `Manage Messages` permission to use this.", color=discord.Color.red()))
            
        if amount < 1 or amount > 100:
            return await ctx.send(embed=discord.Embed(title="⚠️ Error", description="Specify a number between 1 and 100. (e.g. `,purge 10` or `,purge 10 @user`)", color=discord.Color.orange()), delete_after=5)
            
        # This function checks if a message belongs to the pinged user (if one was provided)
        def check(m):
            return m.author == member if member else True
            
        try:
            # If targeting a specific user, we search up to 100 messages back to find their specific messages
            search_limit = 100 if member else amount + 1
            deleted = await ctx.channel.purge(limit=search_limit, check=check)
            
            # Clean up the command message itself if we used a targeted filter
            if member:
                try: await ctx.message.delete()
                except: pass
                
            actual_deleted = len(deleted) if member else len(deleted) - 1
            target_text = f" from **{member.display_name}**" if member else ""
            
            await ctx.send(embed=discord.Embed(title="🧹 Cleaned Up!", description=f"Successfully purged **{actual_deleted}** messages{target_text}.", color=discord.Color.green()), delete_after=4)
            
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(title="❌ Missing Permissions", description="I need the `Manage Messages` permission in my Server Settings to do this!", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(Moderation(bot))
