# cogs/bot_admin.py
import discord
from discord.ext import commands
from utils.db import load_db, save_db, init_guild

OWNER_ID = 756012403291848804

class BotAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addmod(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.administrator and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Only Server Admins or the Bot Owner can add mods.", color=discord.Color.red()))
            
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
        
        if member.id in data[guild_id]["mods"]:
            return await ctx.send(embed=discord.Embed(title="⚠️ Already Mod", description=f"{member.mention} is already a Bot Admin.", color=discord.Color.orange()))
            
        data[guild_id]["mods"].append(member.id)
        save_db(data)
        await ctx.send(embed=discord.Embed(title="🛡️ Mod Added", description=f"{member.mention} is now a Bot Admin!", color=discord.Color.green()))

    @commands.command()
    async def delmod(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.administrator and ctx.author.id != OWNER_ID:
            return await ctx.send(embed=discord.Embed(title="❌ Access Denied", description="Only Server Admins or the Bot Owner can remove mods.", color=discord.Color.red()))
            
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
        
        if member.id not in data[guild_id]["mods"]:
            return await ctx.send(embed=discord.Embed(title="⚠️ Not Found", description=f"{member.mention} is not in the Bot Admin list.", color=discord.Color.orange()))
            
        data[guild_id]["mods"].remove(member.id)
        save_db(data)
        await ctx.send(embed=discord.Embed(title="🗑️ Mod Removed", description=f"{member.mention} is no longer a Bot Admin.", color=discord.Color.red()))

    @commands.command()
    async def modlist(self, ctx):
        guild_id = str(ctx.guild.id)
        data = load_db()
        data = init_guild(data, guild_id)
        
        mod_ids = data.get(guild_id, {}).get("mods", [])
        if not mod_ids:
            return await ctx.send(embed=discord.Embed(title="🛡️ Bot Admins", description="There are no custom Bot Admins in this server yet.", color=discord.Color.blue()))
            
        mod_mentions = [f"<@{m_id}>" for m_id in mod_ids]
        embed = discord.Embed(title="🛡️ Current Bot Admins", description="\n".join(mod_mentions), color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotAdmin(bot))
