import asyncio
import itertools
from functools import partial
from async_timeout import timeout

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio


async def setup(bot):
    await bot.add_cog(Main(bot))


class Source:
    def __init__(self, source, data, requester):
        super().__init__(source)
        self.title = data.get("title")
        self.requester = requester

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    def regather_stream(cls, data):
        return FFmpegPCMAudio(data["source"], executable="ffmpeg")

    @classmethod
    async def create_source(cls, ctx, data):
        title = data["name"]

        await ctx.send(f"Added `{title}` to the queue.")
        return {"title": title, "source": data["files"][0], "requester": ctx.author}


class MusicPlayer:
    def __init__(self, ctx):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                async with timeout(300):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self.guild)

            title = source["title"]
            requester = source["requester"]

            source = Source.regather_stream(source)
            self.current = source

            self.guild.voice_client.play(
                source,
                after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set),
            )
            self.np = await self.channel.send(
                f"Now Playing: `{title}` requested by `{requester}`"
            )

            await self.next.wait()
            source.cleanup()
            self.current = None

    def destroy(self, guild):
        return self.bot.loop.create_task(self.cog.cleanup(guild))


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session

        self.players = {}
        self.vgm_api_base_url = "https://vgm.berkealp.net"

    def get_player(self, ctx):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    # ===========================================================================

    @commands.command(aliases=["j"])
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """ """

        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                return await ctx.send(
                    "Please either specify a valid channel or join one."
                )

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                return await ctx.send(f"Moving to channel: `{channel}` timed out.")
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                return await ctx.send(f"Connecting to channel: `{channel}` timed out.")

        await ctx.send(f"I'm connect to `{channel}`.")

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        """ """

        vc = ctx.voice_client

        await ctx.send("I'm leaving, bye...")
        await vc.disconnect()

    @commands.command(aliases=["v"])
    async def volume(self, ctx, volume: float):
        """ """

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I am not currently connected to voice!")

        if not 0 < volume < 101:
            return await ctx.send("Please enter a value between 1 and 100.")

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = volume / 100

        player.volume = volume / 100
        await ctx.send(f"`{ctx.author}`: Set the volume to `{vol}%`")

    @commands.command()
    async def stop(self, ctx):
        """ """

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently playing anything!")

        await self.cleanup(ctx.guild)

    @commands.command(aliases=["p"])
    async def pause(self, ctx):
        """ """

        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send("I'm not currently playing anything!")
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f"`{ctx.author}`: Paused the song!")

    @commands.command(aliases=["r"])
    async def resume(self, ctx):
        """ """

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I am not currently playing anything!")
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send(f"`{ctx.author}`: Resumed the song!")

    @commands.command(aliases=["s"])
    async def skip(self, ctx):
        """ """

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I am not currently playing anything!")

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send(f"`{ctx.author}`: Skipped the song!")

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        """ """

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice!")

        player = self.get_player(ctx)

        if player.queue.empty():
            return await ctx.send("There are currently no more queued songs.")

        upcoming = list(itertools.islice(player.queue._queue, 0, 10))
        titles = "\n".join(f"- `{_['title']}`" for _ in upcoming)

        await ctx.send(f"Upcoming - Next {len(upcoming)}\n\n{titles}")

    @commands.command(aliases=["c", "np"])
    async def current(self, ctx):
        """ """

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice!")

        player = self.get_player(ctx)

        if not player.current:
            return await ctx.send("I'm not currently playing anything!")

        try:
            await player.np.delete()
        except discord.HTTPException:
            pass

        player.np = await ctx.send(
            f"Now Playing: `annen` requested by `Rubenis RBA-06#3572`"
        )

    # ===========================================================================

    @commands.group(invoke_without_command=True)
    async def vgm(self, ctx):
        """ """

        pass

    @vgm.command(name="search", aliases=["s"])
    async def vgm_search(self, ctx, *, query):
        """ """

        await ctx.trigger_typing()
        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.join)

        async with self.session.get(
            f"{self.vgm_api_base_url}/search",
            params={"q": query},
            ssl=True,
        ) as r:

            if r.status != 200:
                return await ctx.send("Uwu we made a fuck wucky!")

            data = await r.json()

        songs = data["songs"][0:9]
        titles = "\n".join(f"{i+1}. `{_['name']}`" for i, _ in enumerate(songs))

        await ctx.send(
            f"Search Results\n\n{titles.title()}\n\nYour choice (or enter skip):"
        )

        try:
            message = await self.bot.wait_for("message", timeout=30.0)

            if message.content in ["s", "skip"]:
                return await ctx.send("Skiping...")

            player = self.get_player(ctx)
            source = await Source.create_source(ctx, songs[int(message.content) - 1])
            await player.queue.put(source)
        except asyncio.TimeoutError:
            return await ctx.send("Response time has expired.")

    @vgm.group(name="random", aliases=["r"])
    async def vgm_random(self, ctx):
        """ """

        pass

    @vgm_random.command(name="song", aliases=["s"])
    async def vgm_random_song(self, ctx):
        """ """

        await ctx.trigger_typing()
        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.join)

        async with self.session.get(
            f"{self.vgm_api_base_url}/random/song",
            ssl=True,
        ) as r:

            if r.status != 200:
                return await ctx.send("Uwu we made a fuck wucky!")

            data = await r.json()

        player = self.get_player(ctx)
        source = await Source.create_source(ctx, data)
        await player.queue.put(source)

    @vgm_random.command(name="album", aliases=["a"])
    async def vgm_random_album(self, ctx):
        """ """

        pass

    # ===========================================================================

    @vgm_search.before_invoke
    @vgm_random_song.before_invoke
    @vgm_random_album.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
