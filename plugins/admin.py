from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.database.db import db

@Client.on_message(filters.command("addadmin") & filters.private)
async def add_admin(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    if len(message.command) < 2:
        await message.reply_text("Usage: /addadmin [User ID]")
        return
        
    try:
        new_admin_id = int(message.command[1])
        # Try to get user info if possible (optional)
        name = "Unknown"
        try:
            user = await client.get_users(new_admin_id)
            name = user.first_name
        except:
            pass
            
        await db.add_admin(new_admin_id, name)
        await message.reply_text(f"Admin Added: {new_admin_id} ({name})")
    except ValueError:
        await message.reply_text("Invalid ID")

@Client.on_message(filters.command("deladmin") & filters.private)
async def del_admin(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    
    if len(message.command) < 2:
        await message.reply_text("Usage: /deladmin [User ID]")
        return
        
    try:
        admin_id = int(message.command[1])
        await db.remove_admin(admin_id)
        await message.reply_text("Admin Removed.")
    except ValueError:
        await message.reply_text("Invalid ID")

@Client.on_message(filters.command("admins") & filters.private)
async def list_admins(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    admins = await db.get_admins()
    
    text = "**Admins List**\n"
    for admin in admins:
        text += f"- {admin['name']} (`{admin['user_id']}`)\n"
        
    await message.reply_text(text)
