import discord
from discord.ext import commands
import asyncio
import os
import sys
from config import Config

class SecurityBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.mongo = None
        self.db = None
        self.anti_raid_cache = {}
        self.suspicious_actions = {}

    async def setup_hook(self):
        # Load handlers
        await self.load_extension('src.handlers.database_handler')
        await self.load_extension('src.handlers.event_handler')
        await self.load_extension('src.handlers.command_handler')
        
        # Load events
        for filename in os.listdir('./src/events'):
            if filename.endswith('.py'):
                await self.load_extension(f'src.events.{filename[:-3]}')
        
        # Load commands
        await self.load_prefix_commands()
        await self.load_slash_commands()

    async def load_prefix_commands(self):
        for filename in os.listdir('./src/commands/prefix'):
            if filename.endswith('.py'):
                await self.load_extension(f'src.commands.prefix.{filename[:-3]}')

    async def load_slash_commands(self):
        for filename in os.listdir('./src/commands/slash'):
            if filename.endswith('.py'):
                await self.load_extension(f'src.commands.slash.{filename[:-3]}')

    async def on_ready(self):
        print(f'{self.user} is online!')
        await self.sync_commands()

    async def sync_commands(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

bot = SecurityBot()

if __name__ == '__main__':
    bot.run(Config.TOKEN)