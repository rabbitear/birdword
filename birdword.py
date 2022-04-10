#!/usr/bin/env python3
import asyncio
import logging
import os

import discord
import youtube_dl
from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

# Logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='birdword.log', encoding='utf-8',
                              mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self._queue = list()
        self.current_song = None
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command()
    async def add(self, ctx, *, url=None):
        """Add a song to a queue"""
        song_info = ytdl.extract_info(url, download=False)
        self._queue.append(song_info)

    @commands.command()
    async def play(self, ctx, *, url=None):
        """
        Add a song to a queue and start playing the queue. If no 
        url is given, then just start playing the queue.
        """
        global ytdl
        if url:
            song_info = ytdl.extract_info(url, download=False)
            self._queue.append(song_info)
        if not ctx.voice_client.is_playing():
            print("we playing")
            # Since there isn't already a play method running, we can
            # start iterating through the queue.
            while True:
                print("processing queue")
                await self.queue(ctx)
                queue = await self.process_queue(ctx)
                if not queue:
                    break
                await asyncio.sleep(1)

    async def process_queue(self, ctx):
        try:
            self.current_song = self._queue.pop(0)
        except IndexError:
            return False
        retry = 0
        while retry < 6:
            try:
                await self.stream(ctx, self.current_song)
                return True
            except commands.errors.CommandInvokeError:
                # Exponential backoff
                await asyncio.sleep(2^retry)
                retry+=1
            except discord.errors.ClientException:
                # Reconnect voice client
                ctx.voice_client.stop()
                await asyncio.sleep(2^retry)
                await self.ensure_voice(ctx)
            await ctx.send(f'Having trouble playing {self.current_song["title"]}')
                
    @commands.command()
    async def skip(self, ctx):
        """Skip the currently playing song in queue"""
        ctx.voice_client.stop()
        await self.play(ctx)

    async def stream(self, ctx, song_info):
        """Streams from a url (same as yt, but doesn't predownload)"""
        ytdl.cache.remove()
        async with ctx.typing():
            player = await YTDLSource.from_url(song_info['url'], loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=await self.process_queue(ctx))
        await ctx.send(f'Now playing: { song_info["title"] }')

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        # Clean up music_queue variables for next play
        if self._queue_playing:
            # Reinsert the currently playing song into the queue
            self._queue.insert(0, self.current_song)
            self._queue_playing = False
        await ctx.voice_client.disconnect()

    @commands.command()
    async def q(self, *args, **kwargs):
        """Alias for queue"""
        await self._queue(*args, **kwargs)

    @commands.command()
    async def queue(self, ctx):
        """Prints the music queue"""
        await ctx.send('\n'.join([f"#{x}: {y['title']}" for x, y in enumerate(self._queue)]))

    @commands.command()
    async def playnext(self, ctx, *, url):
        """Play this song next"""
        song_info = ytdl.extract_info(url, download=False)
        self._queue.insert(0, song_info)

    @commands.command()
    async def pause(self, ctx):
        """Pause the current playing song"""
        ctx.voice_client.pause()
        await ctx.send(f"song paused")

    @commands.command()
    async def resume(self, ctx):
        """Resume the currently paused song"""
        ctx.voice_client.resume()
        await ctx.send(f"song resumed")

    @commands.command()
    async def clear(self, ctx):
        """Clears the music queue"""
        self._queue = list()
        await ctx.send(f"queue has been cleared")

    @play.before_invoke
    @playnext.before_invoke
    @resume.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError(
                    "Author not connected to a voice channel.")


intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('`'),
    description='BirdWord, The premier Discord bot for entertainment and entertainment accessories',
    intents=intents
)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

bot.add_cog(Music(bot))
bot.run(os.getenv('BOT_TOKEN'))
