from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.db import db
from bot.config import Config
from datetime import datetime, timedelta
import pytz
from bot.plugins.start import delete_message

async def handle_start_link(client, message: Message):
    token = message.command[1]
    
    # Check type
    if token.startswith("req_"):
        link_type = "request"
        channel_id_idx = token.replace("req_", "")
    elif token.startswith("norm_"):
        link_type = "normal"
        channel_id_idx = token.replace("norm_", "")
    else:
        return # Unknown token

    try:
        channel_row_id = int(channel_id_idx)
    except ValueError:
        return

    channels = await db.get_channels()
    channel = next((c for c in channels if c['id'] == channel_row_id), None)
    
    if not channel:
        await message.reply_text("Channel Not Found or Removed.")
        return

    user_id = message.from_user.id
    
    # Check existing link
    invite_link = None
    should_create_new = True
    
    # Find existing valid link for this user/channel/type
    async with db.pool.acquire() as conn:
        existing_link_row = await conn.fetchrow(
            "SELECT * FROM active_links WHERE user_id=$1 AND channel_id=$2 AND link_type=$3 ORDER BY created_at DESC LIMIT 1",
            user_id, channel.get('channel_id'), link_type
        )

    if existing_link_row:
        expires_at = existing_link_row['expires_at']
        if expires_at:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=pytz.UTC)
            now = datetime.now(pytz.UTC)
            if (expires_at - now).total_seconds() > 60:
                invite_link = existing_link_row['invite_link']
                should_create_new = False
    
    if should_create_new:
        # Generate new link
        expire_dt = datetime.now(pytz.UTC) + timedelta(minutes=30)
        
        try:
            invite = await client.create_chat_invite_link(
                chat_id=channel['channel_id'],
                name=f"{link_type} link for {user_id}",
                expire_date=expire_dt,
                creates_join_request=(link_type == "request")
            )
            invite_link = invite.invite_link
            
            await db.save_link(
                token=invite.invite_link,
                channel_id=channel['channel_id'],
                user_id=user_id,
                expires_at=expire_dt,
                link_type=link_type,
                invite_link=invite.invite_link
            )
        except Exception as e:
            await message.reply_text(f"Error generating link: {e}")
            return

    # Check Forward Protection
    forward_protect = await db.get_setting("forward_protect", "False")
    protect_content = (forward_protect == "True")

    # Send Response
    button_text = await db.get_setting("button_text", "⛩️ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗇 ⛩️")
    image_id = await db.get_setting("image_id")
    caption_template = await db.get_setting("caption", "Channel link 🔗 👇👇\n\n[link]\n[link]")
    
    final_caption = caption_template.replace("[link]", invite_link)
    
    second_msg_on = await db.get_setting("second_msg_on", "True")
    second_msg_text = await db.get_setting("second_msg", 
        "Please Join The Channel By Clicking The Link Or Button And This Link Will Expire within few minutes."
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, url=invite_link)]
    ])
    
    msgs_to_delete = []
    
    if image_id:
        try:
            msg1 = await message.reply_photo(
                photo=image_id,
                caption=final_caption,
                reply_markup=buttons,
                protect_content=protect_content
            )
        except:
             msg1 = await message.reply_text(
                text=final_caption,
                reply_markup=buttons,
                protect_content=protect_content
            )
    else:
        msg1 = await message.reply_text(
            text=final_caption,
            reply_markup=buttons,
            protect_content=protect_content
        )
    msgs_to_delete.append(msg1.id)
    
    if second_msg_on == "True":
        msg2 = await msg1.reply_text(second_msg_text, protect_content=protect_content)
        msgs_to_delete.append(msg2.id)
    
    run_date = datetime.now() + timedelta(minutes=30)
    for mid in msgs_to_delete:
        client.scheduler.add_job(delete_message, "date", run_date=run_date, args=[client, message.chat.id, mid])
