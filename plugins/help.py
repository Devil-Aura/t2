from pyrogram import Client, filters
from pyrogram.types import Message
from bot.config import Config
from datetime import datetime, timedelta
from bot.plugins.start import delete_message
from bot.database.db import db

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    text = (
        "**🆘 Help & Support**\n"
        "Agar aapko kisi bhi help ki zaroorat hai, toh humse yahan sampark karein:\n"
        "**@CrunchyRollHelper**\n\n"
        "**🎬 More Anime**\n"
        "Agar aap aur anime dekna chahte hain, toh yahan se dekh sakte hain:\n"
        "**@CrunchyRollChannel**\n\n"
        "<blockquote expandable>\n"
        "**🤖 Bot Info**\n"
        "Bot ki jaankari ke liye /about ya /info ka istemal karein.\n"
        "</blockquote>"
    )
    
    forward_protect = await db.get_setting("forward_protect", "False")
    protect_content = (forward_protect == "True")
    
    msg = await message.reply_text(text, quote=True, protect_content=protect_content)
    
    run_date = datetime.now() + timedelta(seconds=Config.HELP_MSG_DELETE_TIME)
    client.scheduler.add_job(delete_message, "date", run_date=run_date, args=[client, message.chat.id, msg.id])
