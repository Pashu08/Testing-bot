import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import traceback

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='.', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'✅ Online and running as {bot.user}')
    
    # Auto-load ALL files in the cogs folder
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"✅ Loaded {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return 
    print(f"\n⚠️ ERROR IN COMMAND [{ctx.command}]:")
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send("⚠️ An error occurred! Check Termux console.")

bot.run(TOKEN)
