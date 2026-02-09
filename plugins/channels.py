from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.database.db import db
from bot.config import Config
import math

# /addchannel [Anime Name] [Channel Id]
@Client.on_message(filters.command("addchannel") & filters.private)
async def add_channel(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    if len(message.command) < 3:
        await message.reply_text("Usage: /addchannel [Anime Name] [Channel ID]")
        return
        
    channel_id = message.command[-1]
    anime_name = " ".join(message.command[1:-1])
    
    try:
        channel_id = int(channel_id)
    except ValueError:
        await message.reply_text("Invalid Channel ID")
        return

    # Check permissions
    try:
        chat_member = await client.get_chat_member(channel_id, "me")
        if not chat_member.privileges or not chat_member.privileges.can_invite_users:
             await message.reply_text("I am not added in channel or do not have 'Invite Users' permission.")
             return
    except Exception as e:
        await message.reply_text(f"Error accessing channel: {e}\nMake sure I am added to the channel.")
        return

    # Generate Primary Link
    try:
        primary_link = await client.create_chat_invite_link(channel_id, name="primary link")
        await db.add_channel(anime_name, channel_id, primary_link.invite_link)
        await message.reply_text(f"Successfully Added Channel {anime_name}")
    except Exception as e:
         await message.reply_text(f"Failed to create primary link: {e}")

# /channels (Pagination)
@Client.on_message(filters.command("channels") & filters.private)
async def list_channels(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    await send_channels_page(client, message.chat.id, 0)

async def send_channels_page(client, chat_id, page):
    channels = await db.get_channels()
    total_channels = len(channels)
    per_page = 5
    total_pages = math.ceil(total_channels / per_page)
    
    start = page * per_page
    end = start + per_page
    current_channels = channels[start:end]
    
    text = f"**Channels List (Page {page+1}/{total_pages})**\n\n"
    for idx, ch in enumerate(current_channels, start=1):
        # Format: 1. Anime Name(Channel Primary Link) [Request Link] [Normal Link]
        # Request Link: https://t.me/bot?start=req_{id}
        # Normal Link: https://t.me/bot?start=norm_{id}
        bot_username = client.me.username
        req_link = f"https://t.me/{bot_username}?start=req_{ch['id']}"
        norm_link = f"https://t.me/{bot_username}?start=norm_{ch['id']}"
        
        text += f"{idx}. {ch['anime_name']} (<a href='{ch['primary_link']}'>Primary</a>) [<a href='{req_link}'>Request</a>] [<a href='{norm_link}'>Normal</a>]\n\n"
        
    buttons = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"channels_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"channels_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
        
    buttons.append([InlineKeyboardButton("➕ Add Channel", callback_data="add_channel_prompt")])
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_channels")])
    
    await client.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Client.on_callback_query(filters.regex(r"^channels_page_"))
async def channels_pagination(client, callback_query: CallbackQuery):
    page = int(callback_query.data.split("_")[-1])
    await callback_query.message.delete()
    await send_channels_page(client, callback_query.message.chat.id, page)

@Client.on_callback_query(filters.regex("close_channels"))
async def close_channels(client, callback_query):
    await callback_query.message.delete()

@Client.on_callback_query(filters.regex("add_channel_prompt"))
async def add_channel_prompt(client, callback_query):
    await callback_query.answer("Use /addchannel [Name] [ID]", show_alert=True)

# /delchannel [ID]
@Client.on_message(filters.command("delchannel") & filters.private)
async def del_channel(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return
    
    channel_id = int(message.command[1])
    await db.remove_channel(channel_id)
    await message.reply_text("Channel Removed.")

# /search [Name]
@Client.on_message(filters.command("search") & filters.private)
async def search_channel(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /search [Anime Name]")
        return
    
    query = " ".join(message.command[1:])
    results = await db.get_channel_by_name(query)
    
    if not results:
        await message.reply_text("No results found.")
        return
        
    buttons = []
    for ch in results:
        buttons.append([InlineKeyboardButton(ch['anime_name'], callback_data=f"view_channel_{ch['id']}")])
        
    await message.reply_text(f"Here Are Some Search Results 🔎", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^view_channel_"))
async def view_channel(client, callback_query: CallbackQuery):
    ch_id = int(callback_query.data.split("_")[-1])
    # Fetch channel details (need single fetch method in db or filter)
    # Reusing list logic efficiently
    channels = await db.get_channels()
    ch = next((c for c in channels if c['id'] == ch_id), None)
    
    if ch:
        bot_username = client.me.username
        req_link = f"https://t.me/{bot_username}?start=req_{ch['id']}"
        norm_link = f"https://t.me/{bot_username}?start=norm_{ch['id']}"
        
        text = (
            f"**{ch['anime_name']}**\n"
            f"Primary: {ch['primary_link']}\n"
            f"Request: {req_link}\n"
            f"Normal: {norm_link}"
        )
        await callback_query.message.edit_text(text, disable_web_page_preview=True)
    else:
        await callback_query.answer("Channel not found", show_alert=True)
