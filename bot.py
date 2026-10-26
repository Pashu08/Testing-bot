import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import traceback

# Load the hidden token
load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='.', intents=intents)

# This deletes the ugly default Discord help menu
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'✅ Online and running as {bot.user}')
    
    try:
        await bot.load_extension('cogs.hangman')
        print("✅ Hangman module loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load Hangman module: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return 
    
    print(f"\n⚠️ ERROR IN COMMAND [{ctx.command}]:")
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send("⚠️ An error occurred in the code! Check the Termux console to see what broke.")

bot.run(TOKEN)
