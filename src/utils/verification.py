import discord
import asyncio
import random
import string
from PIL import Image, ImageDraw, ImageFont
import io

class VerificationSystem:
    def __init__(self, bot):
        self.bot = bot
        self.pending_verifications = {}

    async def generate_captcha(self):
        """Generate a simple CAPTCHA image"""
        # Create image
        image = Image.new('RGB', (200, 80), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Generate random text
        text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Draw text with some distortion
        for i, char in enumerate(text):
            x = 20 + i * 30
            y = 20 + random.randint(-5, 5)
            draw.text((x, y), char, fill=(0, 0, 0))
        
        # Add some noise
        for _ in range(100):
            x = random.randint(0, 199)
            y = random.randint(0, 79)
            draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # Convert to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return text, discord.File(buffer, filename='captcha.png')

    async def start_verification(self, member):
        """Start verification process for a member"""
        captcha_text, captcha_image = await self.generate_captcha()
        
        # Store CAPTCHA text
        self.pending_verifications[member.id] = captcha_text
        
        # Send CAPTCHA to user
        embed = discord.Embed(
            title="Verification Required",
            description="Please solve the CAPTCHA below to verify yourself.",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://captcha.png")
        
        try:
            await member.send(embed=embed, file=captcha_image)
            
            # Set timeout for verification
            await asyncio.sleep(300)  # 5 minutes
            if member.id in self.pending_verifications:
                await member.kick(reason="Verification timeout")
                del self.pending_verifications[member.id]
                
        except discord.Forbidden:
            # Can't DM user, kick them
            await member.kick(reason="Enable DMs to verify")

    async def verify_member(self, member, code):
        """Verify a member with provided code"""
        if member.id not in self.pending_verifications:
            return False
            
        if self.pending_verifications[member.id].lower() == code.lower():
            # Assign verification role
            config = self.bot.db.guilds.find_one({"guild_id": member.guild.id}) or {}
            role_id = config.get('verification_role')
            
            if role_id:
                role = member.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
            
            del self.pending_verifications[member.id]
            return True
            
        return False
