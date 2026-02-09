from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.database.db import db
import asyncio
import uuid
from datetime import datetime, timedelta
import pytz

# /broadcast (Reply) - As Is
@Client.on_message(filters.command("broadcast") & filters.private & filters.reply)
async def broadcast(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    
    status_msg = await message.reply_text("Broadcasting...")
    users = await db.get_all_users()
    
    batch_id = str(uuid.uuid4())
    success = 0
    failed = 0
    
    for user in users:
        try:
            msg = await message.reply_to_message.copy(chat_id=user['user_id'])
            # Log for deletion capabilities
            await db.add_broadcast_log(batch_id, msg.id, user['user_id'], "normal")
            success += 1
            await asyncio.sleep(0.05) 
        except Exception:
            failed += 1
            
    await status_msg.edit_text(f"Broadcast Complete.\nSuccess: {success}\nFailed: {failed}")

# /batchbroadcast
@Client.on_message(filters.command("batchbroadcast") & filters.private)
async def batch_broadcast_start(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    # Simple state management via DB or memory? Memory is fine for single instance bot.
    # But better to use reply chain or force reply.
    await message.reply_text("Send all the messages you want to broadcast. When done, send /ddone", quote=True)
    # We need a way to capture next messages. 
    # For simplicity in this structure, we can use a dict global or db state. 
    # Let's use a simple state dict in main.py or here? 
    # Plugins share memory.
    client.broadcast_state = getattr(client, "broadcast_state", {})
    client.broadcast_state[message.from_user.id] = {"mode": "batch", "msgs": []}

@Client.on_message(filters.command("ddone") & filters.private)
async def batch_broadcast_done(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    
    state = getattr(client, "broadcast_state", {}).get(message.from_user.id)
    if not state or state["mode"] not in ["batch", "dbroadcast"]:
        return
        
    msgs = state["msgs"]
    if not msgs:
        await message.reply_text("No messages to broadcast.")
        return

    status_msg = await message.reply_text(f"Broadcasting {len(msgs)} messages...")
    users = await db.get_all_users()
    
    batch_id = str(uuid.uuid4())
    success = 0
    
    # Time for dbroadcast
    delete_at = state.get("delete_at")
    broadcast_type = "temp" if delete_at else "normal"
    
    for user in users:
        try:
            for m in msgs:
                sent_msg = await m.copy(chat_id=user['user_id'])
                await db.add_broadcast_log(batch_id, sent_msg.id, user['user_id'], broadcast_type, delete_at)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
            
    # Cleanup state
    del client.broadcast_state[message.from_user.id]
    await status_msg.edit_text(f"Batch Broadcast Complete to {success} users.")

# /pbroadcast - Pin
@Client.on_message(filters.command("pbroadcast") & filters.private & filters.reply)
async def pbroadcast(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    status_msg = await message.reply_text("Broadcasting (Pinned)...")
    users = await db.get_all_users()
    
    batch_id = str(uuid.uuid4())
    success = 0
    
    for user in users:
        try:
            msg = await message.reply_to_message.copy(chat_id=user['user_id'])
            await msg.pin()
            await db.add_broadcast_log(batch_id, msg.id, user['user_id'], "pin", is_pinned=True)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
            
    await status_msg.edit_text(f"Pinned Broadcast Complete.\nSuccess: {success}")

# /dbroadcast [time] - Reply
@Client.on_message(filters.command("dbroadcast") & filters.private & filters.reply)
async def dbroadcast(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    if len(message.command) < 2:
        await message.reply_text("Usage: /dbroadcast 1D 1H 30M")
        return
    
    time_str = " ".join(message.command[1:])
    duration = parse_time(time_str)
    if not duration:
        await message.reply_text("Invalid time format.")
        return
        
    delete_at = datetime.now() + duration
    
    status_msg = await message.reply_text(f"Broadcasting (Temp - {time_str})...")
    users = await db.get_all_users()
    batch_id = str(uuid.uuid4())
    success = 0
    
    for user in users:
        try:
            msg = await message.reply_to_message.copy(chat_id=user['user_id'])
            await db.add_broadcast_log(batch_id, msg.id, user['user_id'], "temp", delete_at)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
            
    await status_msg.edit_text(f"Temp Broadcast Complete.\nSuccess: {success}")

# /batchdbroadcast [time]
@Client.on_message(filters.command("batchdbroadcast") & filters.private)
async def batch_dbroadcast_start(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    if len(message.command) < 2:
        await message.reply_text("Usage: /batchdbroadcast 1H")
        return
        
    time_str = " ".join(message.command[1:])
    duration = parse_time(time_str)
    
    client.broadcast_state = getattr(client, "broadcast_state", {})
    client.broadcast_state[message.from_user.id] = {
        "mode": "dbroadcast", 
        "msgs": [], 
        "delete_at": datetime.now() + duration
    }
    await message.reply_text("Send messages for temp batch. Send /ddone when finished.")

# Catch messages for batch
@Client.on_message(filters.private & ~filters.command(["ddone", "batchbroadcast", "batchdbroadcast"]), group=1)
async def capture_batch(client, message: Message):
    state = getattr(client, "broadcast_state", {}).get(message.from_user.id)
    if state:
        state["msgs"].append(message)

# /delallpbroadcast
@Client.on_message(filters.command("delallpbroadcast") & filters.private)
async def del_all_pin(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    await delete_broadcasts(client, message, "pin")

# /delallbroadcast
@Client.on_message(filters.command("delallbroadcast") & filters.private)
async def del_all_normal(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    await delete_broadcasts(client, message, "normal")

# /clearpendingdbroadcast
@Client.on_message(filters.command("clearpendingdbroadcast") & filters.private)
async def clear_pending_temp(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    # Delete where delete_at < now
    # We need a periodic task for this actually, but this command can force it.
    await check_temp_broadcasts(client)
    await message.reply_text("Checked and deleted expired broadcasts.")

# /allbroadcastclear
@Client.on_message(filters.command("allbroadcastclear") & filters.private)
async def clear_all(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    await message.reply_text("Deleting ALL broadcasts...")
    logs = await db.get_all_broadcasts()
    for log in logs:
        try:
            await client.delete_messages(log['chat_id'], log['message_id'])
        except:
            pass
    await db.clear_all_broadcasts()
    await message.reply_text("All broadcasts cleared.")

# Helpers
def parse_time(time_str):
    time_str = time_str.lower()
    total_seconds = 0
    try:
        if "d" in time_str:
            parts = time_str.split("d")
            total_seconds += int(parts[0]) * 86400
            time_str = parts[1]
        if "h" in time_str:
            parts = time_str.split("h")
            total_seconds += int(parts[0]) * 3600
            time_str = parts[1]
        if "m" in time_str:
            parts = time_str.split("m")
            total_seconds += int(parts[0]) * 60
    except:
        return None
    return timedelta(seconds=total_seconds) if total_seconds > 0 else None

async def delete_broadcasts(client, message, b_type):
    msg = await message.reply_text(f"Deleting {b_type} broadcasts...")
    logs = await db.get_broadcasts_by_type(b_type)
    count = 0
    for log in logs:
        try:
            await client.delete_messages(log['chat_id'], log['message_id'])
            await db.delete_broadcast_log(log['id'])
            count += 1
        except:
            pass
    await msg.edit_text(f"Deleted {count} {b_type} messages.")

async def check_temp_broadcasts(client):
    # This should be run by scheduler periodically too
    logs = await db.get_broadcasts_by_type("temp")
    now = datetime.now()
    for log in logs:
        if log['delete_at'] and log['delete_at'] < now:
            try:
                await client.delete_messages(log['chat_id'], log['message_id'])
                await db.delete_broadcast_log(log['id'])
            except:
                pass
