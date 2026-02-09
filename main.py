from pyrogram import Client, idle
from bot.config import Config
from bot.database.db import db
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

class Bot(Client):
    def __init__(self):
        super().__init__(
            "CrunchyrollBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="bot/plugins")
        )
        self.start_time = datetime.now()
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        await db.connect()
        self.scheduler.start()
        
        # Schedule periodic tasks
        # Check temp broadcasts every minute
        from bot.plugins.broadcast import check_temp_broadcasts
        self.scheduler.add_job(check_temp_broadcasts, "interval", minutes=1, args=[self])
        
        await super().start()
        logging.info("Bot Started!")

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot Stopped!")

app = Bot()

if __name__ == "__main__":
    app.run()
