from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.database.db import db
import math

@Client.on_message(filters.command("addadmin") & filters.private)
async def add_admin(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    if len(message.command) < 2:
        await message.reply_text("Usage: /addadmin [User ID]")
        return
        
    try:
        new_admin_id = int(message.command[1])
        name = "Admin"
        try:
            user = await client.get_users(new_admin_id)
            name = user.first_name
        except:
            pass
            
        await db.add_admin(new_admin_id, name)
        await message.reply_text(f"Successfully added as admin {name} `{new_admin_id}`")
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

# /admins - Button UI
@Client.on_message(filters.command("admins") & filters.private)
async def list_admins(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    await send_admins_page(client, message.chat.id, 0)

async def send_admins_page(client, chat_id, page):
    admins = await db.get_admins()
    per_page = 5
    total_pages = math.ceil(len(admins) / per_page)
    
    start = page * per_page
    end = start + per_page
    current_admins = admins[start:end]
    
    buttons = []
    for admin in current_admins:
        buttons.append([InlineKeyboardButton(admin['name'], callback_data=f"admin_view_{admin['user_id']}")])
        
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"admins_page_{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"admins_page_{page+1}"))
    
    buttons.append([InlineKeyboardButton("➕ Add New Admin", callback_data="add_admin_prompt")])
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_admins")])
        
    text = f"**Admins List (Page {page+1}/{total_pages})**"
    await client.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^admins_page_"))
async def admins_pagination(client, callback_query: CallbackQuery):
    page = int(callback_query.data.split("_")[-1])
    await callback_query.message.delete()
    await send_admins_page(client, callback_query.message.chat.id, page)

@Client.on_callback_query(filters.regex(r"^admin_view_"))
async def admin_view(client, callback_query: CallbackQuery):
    admin_id = int(callback_query.data.split("_")[-1])
    try:
        user = await client.get_users(admin_id)
        username = f"@{user.username}" if user.username else "None"
        name = user.first_name
    except:
        username = "Unknown"
        name = "Unknown"
        
    text = (
        f"**Admin Details**\n"
        f"Name: {name}\n"
        f"ID: `{admin_id}`\n"
        f"Username: {username}"
    )
    
    buttons = [
        [InlineKeyboardButton("Remove Admin", callback_data=f"admin_remove_{admin_id}")],
        [InlineKeyboardButton("Back", callback_data="admins_page_0")]
    ]
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^admin_remove_"))
async def admin_remove_cb(client, callback_query: CallbackQuery):
    admin_id = int(callback_query.data.split("_")[-1])
    await db.remove_admin(admin_id)
    await callback_query.answer("Admin Removed", show_alert=True)
    await callback_query.message.delete()
    await send_admins_page(client, callback_query.message.chat.id, 0)

@Client.on_callback_query(filters.regex("add_admin_prompt"))
async def add_admin_prompt(client, callback_query):
    await callback_query.answer("Use /addadmin [ID]", show_alert=True)
    
@Client.on_callback_query(filters.regex("close_admins"))
async def close_admins(client, callback_query):
    await callback_query.message.delete()

