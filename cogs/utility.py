import os
import time
import inspect
from datetime import datetime

import discord
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(Utility(bot))


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Shows help about the bot, a command, or a category."
            }
        )

        self.owner_cogs = [""]
        self.ignore_cogs = ["Events", "Jishaku"]


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self._original_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @commands.command()
    async def uptime(self, ctx):
        """Tells you how long the bot has been up for."""

        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        await ctx.send(f"Uptime: `{days}d, {hours}h, {minutes}m, {seconds}s`")

    @commands.command()
    async def ping(self, ctx, member: discord.Member = None):
        """Used to test bot's response time."""

        before = time.monotonic()
        message = await ctx.send("Pinging...")
        ping = (time.monotonic() - before) * 1000

        await message.edit(content="Pong: `{} ms`".format(round(ping, 2)))

    @commands.command()
    async def source(self, ctx, *, command=None):
        """Displays my full source code or for a specific command."""

        branch = "main"
        source_url = "https://github.com/yazilimcilarinmolayeri/music-bot"

        if command is None:
            return await ctx.send(source_url)

        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace(".", " "))

            if obj is None:
                return await ctx.send("Command not found!")

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        location = os.path.relpath(filename).replace("\\", "/")
        final_url = "<{}/blob/{}/{}#L{}-L{}>".format(
            source_url,
            branch,
            location,
            firstlineno,
            firstlineno + len(lines) - 1,
        )

        await ctx.send(final_url)

    @commands.command(aliases=["info"])
    async def about(self, ctx):
        """Tells you information about the bot itself."""

        pass
