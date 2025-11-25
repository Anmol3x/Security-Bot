import discord
from discord.ext import commands
from pymongo import MongoClient
from config import Config

class DatabaseHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.setup_database()

    def setup_database(self):
        try:
            self.client = MongoClient(Config.MONGO_URI)
            self.db = self.client.discord_bot
            self.bot.mongo = self.client
            self.bot.db = self.db
            print("Connected to MongoDB")
        except Exception as e:
            print(f"Database connection failed: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        # Create indexes
        self.db.guilds.create_index("guild_id", unique=True)
        self.db.warnings.create_index([("guild_id", 1), ("user_id", 1)])
        self.db.logs.create_index([("guild_id", 1), ("timestamp", -1)])

    def get_guild_config(self, guild_id):
        return self.db.guilds.find_one({"guild_id": guild_id}) or {}

    def update_guild_config(self, guild_id, update_data):
        self.db.guilds.update_one(
            {"guild_id": guild_id},
            {"$set": update_data},
            upsert=True
        )

async def setup(bot):
    await bot.add_cog(DatabaseHandler(bot))
