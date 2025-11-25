import discord
from discord import app_commands
from discord.ext import commands

class SecuritySlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anti-raid", description="Configure anti-raid settings")
    @app_commands.default_permissions(administrator=True)
    async def anti_raid(self, interaction: discord.Interaction, enabled: bool, threshold: int = 5, window: int = 10):
        """Configure anti-raid protection"""
        self.bot.db.guilds.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {
                "anti_raid_enabled": enabled,
                "anti_raid_threshold": threshold,
                "anti_raid_window": window
            }},
            upsert=True
        )
        
        embed = discord.Embed(
            title="Anti-Raid Settings Updated",
            color=discord.Color.green()
        )
        embed.add_field(name="Enabled", value=enabled, inline=True)
        embed.add_field(name="Threshold", value=threshold, inline=True)
        embed.add_field(name="Window (seconds)", value=window, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="verification", description="Configure verification system")
    @app_commands.default_permissions(administrator=True)
    async def verification(self, interaction: discord.Interaction, enabled: bool, role: discord.Role = None, timeout: int = 300):
        """Configure verification system"""
        self.bot.db.guilds.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {
                "verification_enabled": enabled,
                "verification_role": role.id if role else None,
                "verification_timeout": timeout
            }},
            upsert=True
        )
        
        embed = discord.Embed(
            title="Verification Settings Updated",
            color=discord.Color.green()
        )
        embed.add_field(name="Enabled", value=enabled, inline=True)
        if role:
            embed.add_field(name="Role", value=role.mention, inline=True)
        embed.add_field(name="Timeout", value=f"{timeout}s", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="logs", description="Set log channels")
    @app_commands.default_permissions(administrator=True)
    async def logs(self, interaction: discord.Interaction, mod_log: discord.TextChannel = None, security_log: discord.TextChannel = None):
        """Set log channels"""
        update_data = {}
        if mod_log:
            update_data["mod_log_channel"] = mod_log.id
        if security_log:
            update_data["security_log_channel"] = security_log.id
            
        self.bot.db.guilds.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": update_data},
            upsert=True
        )
        
        embed = discord.Embed(
            title="Log Channels Updated",
            color=discord.Color.green()
        )
        if mod_log:
            embed.add_field(name="Mod Log", value=mod_log.mention, inline=True)
        if security_log:
            embed.add_field(name="Security Log", value=security_log.mention, inline=True)
            
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SecuritySlash(bot))
