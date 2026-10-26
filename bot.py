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

@bot.event
async def on_ready():
    print(f'✅ Online and running as {bot.user}')
    
    # This tells the bot to look inside the "cogs" folder and load "hangman.py"
    try:
        await bot.load_extension('cogs.hangman')
        print("✅ Hangman module loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load Hangman module: {e}")

# The Error Catcher
@bot.event
async def on_command_error(ctx, error):
    # Ignore errors if someone just types a command that doesn't exist
    if isinstance(error, commands.CommandNotFound):
        return 
    
    # If something actually breaks, print the full error to Termux and tell the chat
    print(f"\n⚠️ ERROR IN COMMAND [{ctx.command}]:")
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send("⚠️ An error occurred in the code! Check the Termux console to see what broke.")

bot.run(TOKEN)
