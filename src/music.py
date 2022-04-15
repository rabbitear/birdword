import discord
import asyncio
from discord.ext import commands
import youtube_dl
import birdlog

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
print(f"ytdl is: {ytdl}")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        # could return more stuff via this returning cls, which is player below
        self.error = data.get('error')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = asyncio.Queue()


    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You are not in a voice channel!")
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else: 
            await ctx.voice_client.move_to(voice_channel)

    @commands.command()
    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx, url):
        await self.queue.put(url)
        await ctx.send(f"adding url to queue...")

    @commands.command()
    async def queue(self, ctx):
        queuelist = await self.queue.get()
        await ctx.send(f"queue: {queuelist}")

    @commands.command()
    async def resume(self, ctx):
        """Resume the currently paused song"""
        ctx.voice_client.resume()
        await ctx.send(f"song resumed")

    @commands.command()
    async def pause(self, ctx):
        """Pause the currently paused song"""
        ctx.voice_client.pause()
        await ctx.send(f"song paused")

    @commands.command()
    async def stop(self, ctx):
        """ Stop the currently paused song"""
        ctx.voice_client.stop()
        await ctx.send(f"song stopped")

    @play.before_invoke
    @resume.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel")

    @play.after_invoke
    async def queue_playstream(self, ctx):
        """Streams from a queue of urls"""
        # this while is not correct.
        while True:
            size = self.queue.qsize()
            size_str = f'Entering while, queue size: {size}'
            await ctx.send(size_str)
            print(size_str)
            try:
                url = self.queue.get_nowait()
                async with ctx.typing():
                    player = await YTDLSource.from_url(url, loop=self.client.loop, stream=True)
                    print(f'player error: {player.error}')
                    ctx.voice_client.play(player, after=lambda e: print(
                        f'Player error: {e}' if e else None))
                await ctx.send(f'Now playing: {player.title}')
                print(f"player title: {player.title}")

            except discord.errors.ClientException as e:
                await ctx.send(f'ClientExecption: {e}')
                print(f'ClientExecption: {e}')
                await ctx.send(f'player title: {player.title}')
                size = self.queue.qsize()
                await ctx.send(f'trying queue join, queue size: {size}')
                await self.queue.join()
                await ctx.send(f'join done')
                continue
            except asyncio.queues.QueueEmpty as e:
                await ctx.send(f'The queue is now empty')
                break
            else:
                self.queue.task_done()
                await ctx.send(f'Task done')
                continue
            size = self.queue.qsize()
            await ctx.send(f"While done, queue size: {size}")

def setup(client):
    client.add_cog(music(client))
    print("added music cog to client")

