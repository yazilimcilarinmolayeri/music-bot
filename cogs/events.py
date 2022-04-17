import sys
import traceback
from io import StringIO
from datetime import datetime

import discord
from discord.ext import commands, menus


async def setup(bot):
    await bot.add_cog(Events(bot))


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.launch_time = datetime.utcnow()

        print(
            f"Bot name: {self.bot.user}\n"
            f"ID: {self.bot.user.id}\n"
            f"Library version: {discord.__version__}"
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(
            error,
            (
                discord.Forbidden,
                commands.CommandNotFound,
                commands.DisabledCommand,
                menus.MenuError,
                discord.errors.HTTPException,
            ),
        ):
            return

        if isinstance(error, commands.errors.CommandOnCooldown):
            return await ctx.send(
                f"Please wait `{round(error.retry_after)}` second to use this command again."
            )

        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.send(error.capitalize())

        if isinstance(error, commands.errors.BadArgument):
            return await ctx.send(str(error).replace('"', "`").capitalize())

        if isinstance(error, commands.CheckFailure):
            return await ctx.message.add_reaction("\N{FLUSHED FACE}")

        error = error.original
        exc = "".join(
            traceback.format_exception(
                type(error), error, error.__traceback__, chain=False
            )
        )

        channel = self.bot.get_channel(self.bot.config["log"]["error_channel_id"])

        await ctx.message.add_reaction("\N{WARNING SIGN}")
        await channel.send(
            content=(
                f"In `{ctx.command.qualified_name}`: "
                f"`{error.__class__.__name__}`: `{error}`"
            ),
            file=discord.File(
                StringIO(exc),
                filename="traceback.txt",
            ),
        )
