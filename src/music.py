import discord
import asyncio
from discord.ext import commands
import youtube_dl
import birdlog
import tracemalloc


tracemalloc.start()

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
        self.duration = data.get('duration')
        self.description = data.get('discription')
        self.view_count = data.get('view_count')
        self.filesize = data.get('filesize')
        self.upload_date = data.get('upload_date')
        self.uploader = data.get('uploader')
        self.format = data.get('format')
        self.like_count = data.get('like_count')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        # debug, find what the keys are
        print(f'keys of data: {data.keys()}')
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
        size = 0
        count = 0
        di = f'qsize: {size}, wc: {count}'
        while True:
            count += 1
            size = self.queue.qsize()
            size_str = f'Entering while, {di}'
            await ctx.send(size_str)
            print(size_str)
            try:
                async with ctx.typing():
                    url = self.queue.get_nowait()
                    await ctx.send(f'before ytdlsource, {di}')
                    player = await YTDLSource.from_url(url, loop=self.client.loop, stream=True)
                    print(f'player error: {player.error}, {di}')
                    # play the sound now.
                    ctx.voice_client.play(player, after=lambda e: print(
                        f'Player error: {e}' if e else None))

                await ctx.send(f'Now playing: {player.title} (duration: {player.duration})')
                await ctx.send(f'Uploader: {player.uploader}, Upload_date: {player.upload_date}, Filesize: {player.filesize}, Format: {player.format}, Views: {player.view_count}, Likes: {player.like_count}')
                print(f"player title: {player.title}")

            except discord.errors.ClientException as e:
                await ctx.send(f'ClientExecption: {e}')
                print(f'ClientExecption: {e}')
                await ctx.send(f'CE: player title: {player.title}')
                size = self.queue.qsize()
                await ctx.send(f'di: {di}')
                await self.queue.join()
                continue
            except asyncio.queues.QueueEmpty as e:
                await ctx.send(f'QE: The queue is now empty, {di}')
                break
            else:
                self.queue.task_done()
                await ctx.send(f'else: Task done {di}')
                continue
            size = self.queue.qsize()
            await ctx.send(f"WHILE END, {di}")

def setup(client):
    client.add_cog(music(client))
    print("added music cog to client")

