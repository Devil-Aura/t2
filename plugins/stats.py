from pyrogram import Client, filters
from pyrogram.types import Message
from bot.database.db import db
from bot.config import Config
from bot.helpers.utils import get_readable_time, get_uptime
from datetime import datetime
import psutil

# /stats
@Client.on_message(filters.command("stats") & filters.private)
async def stats(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    users, channels, links = await db.get_stats()
    text = (
        f"**📊 Stats**\n\n"
        f"Users: {users}\n"
        f"Channels: {channels}\n"
        f"Active Links: {links}"
    )
    await message.reply_text(text)

# /status
@Client.on_message(filters.command("status") & filters.private)
async def status(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    uptime = get_uptime(client.start_time)
    
    # Broadcasts count
    broadcasts = await db.get_all_broadcasts()
    pending = len([b for b in broadcasts if b['delete_at'] and b['delete_at'] > datetime.now()])
    
    started_at = client.start_time.strftime("%Y-%m-%d %H:%M:%S")
    
    text = (
        "⚙️ sʏsᴛᴇᴍ sᴛᴀᴛᴜs\n\n"
        f"🖥 CPU: {cpu}% | RAM: {mem}%\n"
        f"⏱ ᴜᴘᴛɪᴍᴇ: {uptime}\n"
        f"🕒 sᴛᴀʀᴛᴇᴅ: {started_at}\n"
        f"⏰ ᴘᴇɴᴅɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛs: {pending}"
    )
    await message.reply_text(text)

# /ping
@Client.on_message(filters.command("ping") & filters.private)
async def ping(client, message: Message):
    start = datetime.now()
    msg = await message.reply_text("Pinging...")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    await msg.edit_text(f"Pong! 🏓\n{ms}ms")
