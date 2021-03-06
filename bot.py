#!/usr/bin/python3.9

#
# Copyright (C) 2022 yazilimcilarinmolayeri
#

import os
import json
import logging
import warnings

import discord
import aiohttp
from discord.ext import commands


os.environ["JISHAKU_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


class MusicBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_extensions = [
            "jishaku",
            "cogs.events",
            "cogs.main",
            "cogs.utility",
        ]
        self.config = config
        self.color = 0x2F3136

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()

        for ext in self.initial_extensions:
            await self.load_extension(ext)

    @property
    def owners(self):
        return [self.get_user(id) for id in self.owner_ids]

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def close(self):
        await super().close()
        await self.session.close()

    def run(self):
        super().run(self.config["bot"]["token"], reconnect=True)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename="music-bot.log", mode="w", encoding="utf-8")
    formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    with open("config.json") as file:
        config = json.loads(file.read())

    intents = discord.Intents.default()
    intents.message_content = True

    bot = MusicBot(
        config=config,
        intents=intents,
        command_prefix=config["bot"]["command_prefix"],
        owner_ids=set(config["bot"]["owner_ids"]),
    )
    bot.run()
