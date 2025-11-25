import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server"""
        try:
            await member.ban(reason=reason)
            
            # Log the action
            await self.log_mod_action(
                ctx.guild, 
                "ban", 
                ctx.author, 
                member, 
                reason
            )
            
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error banning member: {e}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        try:
            await member.kick(reason=reason)
            
            await self.log_mod_action(
                ctx.guild, 
                "kick", 
                ctx.author, 
                member, 
                reason
            )
            
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error kicking member: {e}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, duration: str = "1h", *, reason="No reason provided"):
        """Mute a member for specified duration"""
        try:
            # Convert duration to seconds
            seconds = self.parse_duration(duration)
            if not seconds:
                await ctx.send("Invalid duration format. Use: 1h, 30m, 1d, etc.")
                return
            
            # Get or create muted role
            muted_role = await self.get_muted_role(ctx.guild)
            
            await member.add_roles(muted_role, reason=reason)
            
            # Schedule unmute
            await asyncio.sleep(seconds)
            await member.remove_roles(muted_role)
            
            await self.log_mod_action(
                ctx.guild, 
                "mute", 
                ctx.author, 
                member, 
                f"{reason} (Duration: {duration})"
            )
            
            embed = discord.Embed(
                title="Member Muted",
                description=f"{member.mention} has been muted for {duration}.",
                color=discord.Color.dark_gray()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error muting member: {e}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason):
        """Warn a member"""
        warning_data = {
            "guild_id": ctx.guild.id,
            "user_id": member.id,
            "moderator_id": ctx.author.id,
            "reason": reason,
            "timestamp": datetime.utcnow()
        }
        
        self.bot.db.warnings.insert_one(warning_data)
        
        await self.log_mod_action(
            ctx.guild, 
            "warn", 
            ctx.author, 
            member, 
            reason
        )
        
        embed = discord.Embed(
            title="Member Warned",
            description=f"{member.mention} has been warned.",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def warnings(self, ctx, member: discord.Member):
        """Check warnings for a member"""
        warnings = list(self.bot.db.warnings.find({
            "guild_id": ctx.guild.id,
            "user_id": member.id
        }))
        
        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            color=discord.Color.orange()
        )
        
        if warnings:
            for i, warning in enumerate(warnings, 1):
                mod = ctx.guild.get_member(warning['moderator_id'])
                mod_name = mod.display_name if mod else "Unknown"
                embed.add_field(
                    name=f"Warning #{i}",
                    value=f"Reason: {warning['reason']}\nBy: {mod_name}\nDate: {warning['timestamp'].strftime('%Y-%m-%d %H:%M')}",
                    inline=False
                )
        else:
            embed.description = "No warnings found."
            
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Clear specified number of messages"""
        if amount > 100:
            await ctx.send("You can only clear up to 100 messages at once.")
            return
            
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        embed = discord.Embed(
            title="Messages Cleared",
            description=f"Deleted {len(deleted) - 1} messages.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, delete_after=5)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Lock the current channel"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        
        embed = discord.Embed(
            title="Channel Locked",
            description="This channel has been locked.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Unlock the current channel"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        
        embed = discord.Embed(
            title="Channel Unlocked",
            description="This channel has been unlocked.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Set slowmode for the channel"""
        await ctx.channel.edit(slowmode_delay=seconds)
        
        embed = discord.Embed(
            title="Slowmode Set",
            description=f"Slowmode set to {seconds} seconds.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    async def get_muted_role(self, guild):
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            
            # Set permissions for all channels
            for channel in guild.channels:
                await channel.set_permissions(muted_role, send_messages=False)
                
        return muted_role

    def parse_duration(self, duration):
        units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        
        try:
            number = int(duration[:-1])
            unit = duration[-1].lower()
            return number * units.get(unit, 1)
        except:
            return None

    async def log_mod_action(self, guild, action, moderator, target, reason):
        config = self.bot.db.guilds.find_one({"guild_id": guild.id}) or {}
        log_channel = config.get('mod_log_channel')
        
        if log_channel:
            channel = guild.get_channel(log_channel)
            if channel:
                embed = discord.Embed(
                    title=f"Moderation Action: {action.upper()}",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Moderator", value=moderator.mention, inline=True)
                embed.add_field(name="Target", value=target.mention, inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
