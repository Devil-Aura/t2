from pyrogram import Client, filters
from pyrogram.types import Message
from bot.config import Config
from bot.database.db import db
from datetime import datetime, timedelta

async def delete_message(client, chat_id, message_id):
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception as e:
        print(f"Failed to delete message: {e}")

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    await db.add_user(user_id, username)
    
    # Check if it's a token link (e.g. /start token)
    if len(message.command) > 1:
        from bot.plugins.links import handle_start_link
        await handle_start_link(client, message)
        return

    text = (
        "Konnichiwa! 🤗\n"
        "Mera Naam **Crunchyroll Link Provider** hai.\n\n"
        "Main aapko **anime channels** ki links provide karta hu, Iss Anime Ke Channel Se.\n\n"
        "<blockquote>\n"
        "🔹 Agar aapko kisi anime ki link chahiye,<br>\n"
        "🔹 Ya channel ki link nahi mil rahi hai,<br>\n"
        "🔹 Ya link expired ho gayi hai\n"
        "</blockquote>\n"
        "Toh aap **@CrunchyRollChannel** se New aur working links le sakte hain.\n\n"
        "Shukriya! ❤️"
    )
    
    forward_protect = await db.get_setting("forward_protect", "False")
    protect_content = (forward_protect == "True")
    
    msg = await message.reply_text(text, quote=True, protect_content=protect_content)
    
    # Schedule deletion
    run_date = datetime.now() + timedelta(seconds=Config.START_MSG_DELETE_TIME)
    client.scheduler.add_job(delete_message, "date", run_date=run_date, args=[client, message.chat.id, msg.id])

