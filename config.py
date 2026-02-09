import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    
    # Defaults
    START_MSG_DELETE_TIME = 900 # 15 mins
    HELP_MSG_DELETE_TIME = 120 # 2 mins
    ABOUT_MSG_DELETE_TIME = 60 # 1 min
    LINK_REVOKE_TIME = 1800 # 30 mins
