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
    if message.author.name == 'rabbitear' or message.author.name =='StormBeatz':
        await message.channel.send('blah blah bla bla')
        print(f"---- {message.author.name} ----")
        print(f"MESSAGE: {message}")
        print("---")
        print(f"CONTENT: {message.content}")
        print(f"EMBEDS:  {message.embeds}")
        print(f"len(embeds): {len(message.embeds)}")
        #if len(message.embeds):
        #for i in message.embeds:
        for i, embed in enumerate(message.embeds):
            desc = message.embeds[i].description
            titl = message.embeds[i].title
            print(f"DESC{i}: {desc}")
            print(f"TITL{i}: {titl}")
            await message.channel.send(f'from {message.author} the BLA BLA title{i}: {message.embeds[0].title}')
            await message.channel.send(f'from {message.author} the BLA BLA description{i}: {message.embeds[0].description}')

        [print(i) for i in message.embeds]
        print(f"type: {type(message.embeds)}")
        print(f"webhook_id: {message.webhook_id}")
        print("---")

for i in range(len(cogs)):
    cogs[i].setup(bot)

bot.run(os.getenv("BOT_TOKEN"))

