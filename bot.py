import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load the hidden token from .env
load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Online and running as {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

bot.run(TOKEN)
