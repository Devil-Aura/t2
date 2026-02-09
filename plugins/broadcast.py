from pyrogram import Client, filters
from pyrogram.types import Message
from bot.database.db import db
import asyncio

# /broadcast (Reply)
@Client.on_message(filters.command("broadcast") & filters.private & filters.reply)
async def broadcast(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    
    await message.reply_text("Broadcasting...")
    users = await db.get_all_users()
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await message.reply_to_message.copy(chat_id=user['user_id'])
            success += 1
            await asyncio.sleep(0.1) # Avoid flood
        except Exception:
            failed += 1
            
    await message.reply_text(f"Broadcast Complete.\nSuccess: {success}\nFailed: {failed}")

# /pbroadcast (Reply) - Pin
@Client.on_message(filters.command("pbroadcast") & filters.private & filters.reply)
async def pbroadcast(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    await message.reply_text("Broadcasting (Pinned)...")
    users = await db.get_all_users()
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            msg = await message.reply_to_message.copy(chat_id=user['user_id'])
            await msg.pin()
            success += 1
            await asyncio.sleep(0.1)
        except Exception:
            failed += 1
            
    await message.reply_text(f"Pinned Broadcast Complete.\nSuccess: {success}\nFailed: {failed}")

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
