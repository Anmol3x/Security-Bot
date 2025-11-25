import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    TOKEN = os.getenv('DISCORD_TOKEN')
    PREFIX = '.'
    OWNER_IDS = [int(x) for x in os.getenv('OWNER_IDS', '').split(',') if x]
    
    # Database
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/discord_bot')
    
    # Dashboard
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 5000))
    DASHBOARD_SECRET = os.getenv('DASHBOARD_SECRET', 'your-secret-key')
    
    # Security Settings
    ANTI_RAID_THRESHOLD = int(os.getenv('ANTI_RAID_THRESHOLD', 5))
    ANTI_RAID_WINDOW = int(os.getenv('ANTI_RAID_WINDOW', 10))
    
    # Default Cooldowns
    COMMAND_COOLDOWN = 3
    ANTI_SPAM_COOLDOWN = 2