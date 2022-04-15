# main birdword file 

import discord
import asyncio
import os
from discord.ext import commands
import music
import birdlog

cogs = [music]

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="`", 
        description='BirdWord, The Discord bot for entertaining the users',
        intents=intents)

@bot.event
async def on_ready():
    start_str = f"Logging in as {bot.user} (ID: {bot.user.id})"
    print(start_str)

for i in range(len(cogs)):
    cogs[i].setup(bot)

bot.run(os.getenv("BOT_TOKEN"))

