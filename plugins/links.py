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
    # We need to fetch from active_links table for this user and channel and type
    # But wait, token is unique per link? No, token is global for the channel.
    # The active_links table uses 'token' as PK? No, 'token' in active_links should be the UNIQUE INVITE LINK identifier or something.
    # My active_links schema: token, channel_id, user_id, ...
    # Here 'token' in schema probably referred to the 'invite link' string itself or a unique ID.
    # Let's use the Invite Link as the unique key for revocation, but for lookup we need user_id + channel_id.
    
    # DB Update needed: active_links table primary key is token?
    # "CREATE TABLE IF NOT EXISTS active_links (token TEXT PRIMARY KEY...)"
    # I should query by user_id and channel_id.
    
    existing_link_row = None
    # Assuming we can query active_links. I'll need a method in db.py for this.
    # "SELECT * FROM active_links WHERE user_id=$1 AND channel_id=$2 AND link_type=$3"
    
    # Since I can't easily modify db.py methods right now without rewriting the file, I'll add the raw query here if needed or just use `db.pool`.
    # But wait, I defined `db` instance. I can add methods to `Database` class in `db.py` by re-writing `db.py` or just accessing `db.pool` directly if I made it public (it is `self.pool`).
    
    # Direct pool access
    async with db.pool.acquire() as conn:
        existing_link_row = await conn.fetchrow(
            "SELECT * FROM active_links WHERE user_id=$1 AND channel_id=$2 AND link_type=$3 ORDER BY created_at DESC LIMIT 1",
            user_id, channel.get('channel_id'), link_type
        )

    invite_link = None
    should_create_new = True

    if existing_link_row:
        expires_at = existing_link_row['expires_at']
        # Check if expires in > 1 min
        # expires_at is datetime
        if expires_at:
             # Make timezone aware
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
            
            # Save to DB
            await db.save_link(
                token=invite.invite_link, # Using invite link as unique token in active_links
                channel_id=channel['channel_id'],
                user_id=user_id,
                expires_at=expire_dt,
                link_type=link_type,
                invite_link=invite.invite_link
            )
        except Exception as e:
            await message.reply_text(f"Error generating link: {e}")
            return

    # Send Response
    # Image + Button
    # Second Message
    
    # Get Customization
    button_text = await db.get_setting("button_text", "⛩️ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗇 ⛩️")
    image_id = await db.get_setting("image_id") # file_id
    second_msg_text = await db.get_setting("second_msg", 
        "Please Join The Channel By Clicking The Link Or Button And This Link Will Expire within few minutes."
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, url=invite_link)]
    ])
    
    links_text = f"Channel link 🔗 👇👇\n\n{invite_link}\n{invite_link}"
    
    msgs_to_delete = []
    
    if image_id:
        msg1 = await message.reply_photo(
            photo=image_id,
            caption=links_text,
            reply_markup=buttons
        )
    else:
        msg1 = await message.reply_text(
            text=links_text,
            reply_markup=buttons
        )
    msgs_to_delete.append(msg1.id)
    
    # Second Message (Reply to first)
    msg2 = await msg1.reply_text(second_msg_text)
    msgs_to_delete.append(msg2.id)
    
    # Schedule Delete (30 mins)
    run_date = datetime.now() + timedelta(minutes=30)
    for mid in msgs_to_delete:
        client.scheduler.add_job(delete_message, "date", run_date=run_date, args=[client, message.chat.id, mid])

