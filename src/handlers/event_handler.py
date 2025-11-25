import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

class EventHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_timestamps = {}
        self.message_cache = {}

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        config = self.bot.db.guilds.find_one({"guild_id": guild_id}) or {}
        
        # Anti-raid detection
        await self.check_anti_raid(member)
        
        # Verification system
        if config.get('verification_enabled', False):
            await self.start_verification(member)

    async def check_anti_raid(self, member):
        guild_id = member.guild.id
        current_time = datetime.utcnow()
        
        if guild_id not in self.join_timestamps:
            self.join_timestamps[guild_id] = []
        
        self.join_timestamps[guild_id].append(current_time)
        
        # Remove timestamps outside the window
        window = timedelta(seconds=self.bot.anti_raid_window)
        self.join_timestamps[guild_id] = [
            ts for ts in self.join_timestamps[guild_id] 
            if current_time - ts < window
        ]
        
        # Check threshold
        if len(self.join_timestamps[guild_id]) >= self.bot.anti_raid_threshold:
            await self.handle_raid(member.guild)

    async def handle_raid(self, guild):
        config = self.bot.db.guilds.find_one({"guild_id": guild.id}) or {}
        security_log = config.get('security_log_channel')
        
        if security_log:
            channel = guild.get_channel(security_log)
            if channel:
                await channel.send("🚨 **RAID DETECTED** - Anti-raid measures activated!")
        
        # Take action based on config
        if config.get('anti_raid_auto_lock', False):
            await self.lock_server(guild)
        
        if config.get('anti_raid_auto_kick', False):
            await self.kick_recent_joins(guild)

    async def lock_server(self, guild):
        for channel in guild.channels:
            try:
                await channel.set_permissions(guild.default_role, send_messages=False)
            except:
                pass

    async def kick_recent_joins(self, guild):
        recent_joins = self.join_timestamps.get(guild.id, [])
        for member in guild.members:
            if member.joined_at and member.joined_at in recent_joins:
                try:
                    await member.kick(reason="Anti-raid protection")
                except:
                    pass

    async def start_verification(self, member):
        # CAPTCHA verification implementation
        pass

async def setup(bot):
    await bot.add_cog(EventHandler(bot))
