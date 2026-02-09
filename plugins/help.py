from pyrogram import Client, filters
from pyrogram.types import Message
from bot.config import Config
from datetime import datetime, timedelta
from bot.plugins.start import delete_message

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
    
    msg = await message.reply_text(text, quote=True)
    
    run_date = datetime.now() + timedelta(seconds=Config.HELP_MSG_DELETE_TIME)
    client.scheduler.add_job(delete_message, "date", run_date=run_date, args=[client, message.chat.id, msg.id])
