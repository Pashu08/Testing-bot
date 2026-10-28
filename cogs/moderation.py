# cogs/moderation.py
import discord
from discord.ext import commands
from collections import deque

OWNER_ID = 756012403291848804

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cache up to 15 deleted messages per channel using a memory-safe deque
        self.snipes = {}

    # ==========================
    # SNIPE SYSTEM
    # ==========================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Ignore bot messages AND ignore commands so it doesn't snipe your own ',snipe'
        if message.author.bot or message.content.startswith(','):
            return
            
        if message.channel.id not in self.snipes:
            self.snipes[message.channel.id] = deque(maxlen=15)
            
        # Strip out raw image links instead of saving physical attachments
        attachment_urls = [attachment.url for attachment in message.attachments]
        
        # Save only the raw text data to prevent Termux memory bloat
        snipe_data = {
            "author_name": message.author.display_name,
            "author_avatar": message.author.display_avatar.url,
            "content": message.content,
            "attachments": attachment_urls,
            "created_at": message.created_at
        }
        
        self.snipes[message.channel.id].append(snipe_data)

    @commands.command()
    async def snipe(self, ctx, arg: str = "1"):
        # Permission Lock: Mods and Owner Only
        if not ctx.author.guild_permissions.manage_messages and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="You need the `Manage Messages` permission to use this.", color=discord.Color.red()), delete_after=5)

        # 1. Instantly delete the user's snipe command to hide the evidence
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
            
        channel_snipes = self.snipes.get(ctx.channel.id)
        
        if not channel_snipes:
            return await ctx.send(embed=discord.Embed(title="🔫 Nothing to Snipe!", description="No recently deleted messages found here.", color=discord.Color.red()), delete_after=5)
            
        total_snipes = len(channel_snipes)

        # Show a summary log of all cached messages at once
        if arg.lower() in ["list", "all"]:
            description = ""
            for i, snipe in enumerate(reversed(channel_snipes), 1):
                content = snipe["content"][:45] + "..." if len(snipe["content"]) > 45 else snipe["content"]
                if not content.strip() and snipe["attachments"]:
                    content = "[Image/Attachment]"
                    
                # Calculate the exact timestamp for Discord to format as "X minutes ago"
                unix_time = int(snipe["created_at"].timestamp())
                description += f"**{i}. {snipe['author_name']}** (<t:{unix_time}:R>): {content}\n"
                
            embed = discord.Embed(title=f"📝 Last {total_snipes} Deleted Messages", description=description, color=discord.Color.blue())
            embed.set_footer(text=f"Requested by {ctx.author.display_name} • Self-destructing in 20s")
            return await ctx.send(embed=embed, delete_after=20)
            
        # Error handling if they type something weird
        if not arg.isdigit():
            return await ctx.send(embed=discord.Embed(title="⚠️ Error", description="Use `,snipe` for the newest, `,snipe 3` for a specific one, or `,snipe list` for the full log.", color=discord.Color.orange()), delete_after=5)
            
        index = int(arg)
        if index < 1 or index > total_snipes:
            return await ctx.send(embed=discord.Embed(title="⚠️ Error", description=f"I only have **{total_snipes}** deleted message(s). Pick a number between 1 and {total_snipes}.", color=discord.Color.orange()), delete_after=5)
            
        # Index 1 is the most recent (last in list), Index 2 is second most recent, etc.
        snipe = channel_snipes[-index]
        unix_time = int(snipe["created_at"].timestamp())
        
        content = snipe["content"]
        if snipe["attachments"]:
            links = "\n".join(snipe["attachments"])
            content += f"\n\n🔗 **Attachments:**\n{links}"
            
        if not content.strip():
            content = "*[No text content]*"
            
        # Add explicit time tag to the bottom of the main message
        content += f"\n\n*Sent <t:{unix_time}:R>*"

        embed = discord.Embed(description=content, color=discord.Color.purple())
        embed.set_author(name=snipe["author_name"], icon_url=snipe["author_avatar"])
        embed.set_footer(text=f"Sniped by {ctx.author.display_name} • [Msg {index}/{total_snipes}] • Self-destructing in 15s")
        embed.timestamp = snipe["created_at"]
        
        # 2. Send the snipe and auto-delete it after 15 seconds
        await ctx.send(embed=embed, delete_after=15)

    # ==========================
    # PURGE SYSTEM
    # ==========================
    @commands.command()
    async def purge(self, ctx, amount: int = 0, member: discord.Member = None):
        if not ctx.author.guild_permissions.manage_messages and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="You need the `Manage Messages` permission to use this.", color=discord.Color.red()))
            
        if amount < 1 or amount > 100:
            return await ctx.send(embed=discord.Embed(title="⚠️ Error", description="Specify a number between 1 and 100. (e.g. `,purge 10` or `,purge 10 @user`)", color=discord.Color.orange()), delete_after=5)
            
        def check(m):
            return m.author == member if member else True
            
        try:
            search_limit = 100 if member else amount + 1
            deleted = await ctx.channel.purge(limit=search_limit, check=check)
            
            if member:
                try: await ctx.message.delete()
                except: pass
                
            actual_deleted = len(deleted) if member else len(deleted) - 1
            target_text = f" from **{member.display_name}**" if member else ""
            
            await ctx.send(embed=discord.Embed(title="🧹 Cleaned Up!", description=f"Successfully purged **{actual_deleted}** messages{target_text}.", color=discord.Color.green()), delete_after=4)
            
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(title="❌ Missing Permissions", description="I need the `Manage Messages` permission in my Server Settings to do this!", color=discord.Color.red()), delete_after=5)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
