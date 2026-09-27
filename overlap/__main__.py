"""
Entry point for `python -m overlap` — runs the Discord bot.

Importing overlap.bot already does all the setup (config validation, plugin
loading, building the Discord client); this just starts it. A package can't
be executed directly (`python -m overlap` alone, with no submodule) unless it
has this file — without it, Python raises "'overlap' is a package and cannot
be directly executed", which is exactly what the Dockerfile's and
docker-compose's `python -m overlap` command hit before this file existed.
"""
from overlap import config
from overlap.bot import client

client.run(config.DISCORD_TOKEN)
