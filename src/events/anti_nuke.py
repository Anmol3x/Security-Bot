import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.action_timestamps = {}
        self.trusted_users = {}

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.check_mass_deletion(channel.guild, 'channel')

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.check_mass_deletion(role.guild, 'role')

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.check_mass_action(guild, 'ban')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if await self.is_kick(member):
            await self.check_mass_action(member.guild, 'kick')

    async def check_mass_deletion(self, guild, action_type):
        guild_id = guild.id
        current_time = datetime.utcnow()
        
        key = f"{guild_id}_{action_type}"
        
        if key not in self.action_timestamps:
            self.action_timestamps[key] = []
        
        self.action_timestamps[key].append(current_time)
        
        # Keep only actions from last 10 seconds
        window = timedelta(seconds=10)
        self.action_timestamps[key] = [
            ts for ts in self.action_timestamps[key] 
            if current_time - ts < window
        ]
        
        # Check if threshold exceeded
        if len(self.action_timestamps[key]) >= 3:  # 3 actions in 10 seconds
            await self.handle_mass_deletion(guild, action_type)

    async def handle_mass_deletion(self, guild, action_type):
        config = self.bot.db.guilds.find_one({"guild_id": guild.id}) or {}
        
        if not config.get('anti_nuke_enabled', True):
            return
            
        # Get recent audit log entry to find responsible user
        async for entry in guild.audit_logs(limit=5, action=getattr(discord.AuditLogAction, f'{action_type}_delete')):
            user = entry.user
            
            # Skip if user is trusted
            if await self.is_trusted(guild, user):
                break
                
            # Take action
            await self.punish_nuker(guild, user, f"Mass {action_type} deletion")
            break

    async def punish_nuker(self, guild, user, reason):
        try:
            # Remove administrator permissions
            for role in user.roles[1:]:  # Skip @everyone
                if role.permissions.administrator:
                    await user.remove_roles(role)
                    
            # Kick the user
            await user.kick(reason=reason)
            
        except Exception as e:
            print(f"Error punishing nuker: {e}")

    async def is_trusted(self, guild, user):
        config = self.bot.db.guilds.find_one({"guild_id": guild.id}) or {}
        trusted_roles = config.get('trusted_roles', [])
        trusted_users = config.get('trusted_users', [])
        
        if user.id in trusted_users:
            return True
            
        for role in user.roles:
            if role.id in trusted_roles:
                return True
                
        return False

    async def is_kick(self, member):
        try:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    return True
        except:
            pass
        return False

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
