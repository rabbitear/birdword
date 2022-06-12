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

@bot.listen()
async def on_message(message):
    if message.content == 'ping':
        await message.channel.send('pong')

@bot.listen()
async def on_message(message):
    if message.author.name == 'rabbitbird':
        await message.channel.send('bla bla bla bla')
        print(message)

@bot.listen()
async def on_message(message):
    if message.author.name == 'rabbitbird' or message.author.name =='StormBeatz':
        await message.channel.send('blah blah bla bla')
        print(f"---- {message.author.name} ----")
        print(f"message: {message}")
        print("---")
        print(f"content: {message.content}")
        print(f"embeds:  {message.embeds}")
        print(f"len(embeds): {len(message.embeds)}")
        [print(i) for i in message.embeds]
        print(f"type: {type(message.embeds)}")
        print("---")

for i in range(len(cogs)):
    cogs[i].setup(bot)

bot.run(os.getenv("BOT_TOKEN"))

