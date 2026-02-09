from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.database.db import db
from bot.config import Config
import asyncio

# /customize
@Client.on_message(filters.command("customize") & filters.private)
async def customize_menu(client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return
        
    text = "Here you can customise all the things of bot."
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Image Post", callback_data="cust_image_post"),
            InlineKeyboardButton("Second Message", callback_data="cust_second_msg")
        ],
        [
            InlineKeyboardButton("Forward", callback_data="cust_forward"),
            InlineKeyboardButton("Revoke Time", callback_data="cust_revoke")
        ],
        [
            InlineKeyboardButton("Force Sub", callback_data="cust_fsub"),
            InlineKeyboardButton("Maintenance Mode", callback_data="cust_maint")
        ],
        [InlineKeyboardButton("Close", callback_data="close_cust")]
    ])
    await message.reply_text(text, reply_markup=buttons)

# --- Image Post Customization ---
@Client.on_callback_query(filters.regex("cust_image_post"))
async def cust_image_post(client, callback_query: CallbackQuery):
    text = "Here you can customise Image Post Message"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Caption", callback_data="cust_caption")],
        [InlineKeyboardButton("Image", callback_data="cust_image")],
        [InlineKeyboardButton("Button Text", callback_data="cust_btn_text")],
        [InlineKeyboardButton("Back", callback_data="cust_main"), InlineKeyboardButton("Close", callback_data="close_cust")]
    ])
    await callback_query.message.edit_text(text, reply_markup=buttons)

# Caption
@Client.on_callback_query(filters.regex("cust_caption"))
async def cust_caption(client, callback_query: CallbackQuery):
    curr = await db.get_setting("caption", "Default Caption")
    text = (
        f"Current Caption: {curr}\n\n"
        "Use [link] in caption for link position."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Set Caption", callback_data="set_caption_prompt")],
        [InlineKeyboardButton("Back", callback_data="cust_image_post"), InlineKeyboardButton("Close", callback_data="close_cust")]
    ])
    await callback_query.message.edit_text(text, reply_markup=buttons)

@Client.on_callback_query(filters.regex("set_caption_prompt"))
async def set_caption_prompt(client, callback_query: CallbackQuery):
    await callback_query.message.reply_text("Send new caption:", quote=True)
    # State handling would be needed here for next message capture
    client.broadcast_state = getattr(client, "broadcast_state", {})
    client.broadcast_state[callback_query.from_user.id] = {"mode": "set_caption"}

# Image
@Client.on_callback_query(filters.regex("cust_image"))
async def cust_image(client, callback_query: CallbackQuery):
    text = "After Clicking Set Image Button Send The Image."
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Current Image", callback_data="curr_image")],
        [InlineKeyboardButton("Set Image", callback_data="set_image_prompt")],
        [InlineKeyboardButton("Delete Image", callback_data="del_image_confirm")],
        [InlineKeyboardButton("Back", callback_data="cust_image_post")]
    ])
    await callback_query.message.edit_text(text, reply_markup=buttons)

@Client.on_callback_query(filters.regex("curr_image"))
async def curr_image(client, callback_query: CallbackQuery):
    img_id = await db.get_setting("image_id")
    if img_id:
        await callback_query.message.reply_photo(img_id)
    else:
        await callback_query.answer("No image set", show_alert=True)

@Client.on_callback_query(filters.regex("set_image_prompt"))
async def set_image_prompt(client, callback_query: CallbackQuery):
    await callback_query.message.reply_text("Please send new image which you want to set.")
    client.broadcast_state = getattr(client, "broadcast_state", {})
    client.broadcast_state[callback_query.from_user.id] = {"mode": "set_image"}

@Client.on_callback_query(filters.regex("del_image_confirm"))
async def del_image_confirm(client, callback_query: CallbackQuery):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes", callback_data="del_image_yes"), InlineKeyboardButton("No", callback_data="cust_image")]
    ])
    await callback_query.message.edit_text("Are you sure to delete the current image?", reply_markup=buttons)

@Client.on_callback_query(filters.regex("del_image_yes"))
async def del_image_yes(client, callback_query: CallbackQuery):
    await db.delete_setting("image_id")
    await callback_query.message.edit_text("Successfully deleted current image.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="cust_image")]]))

# Button Text
@Client.on_callback_query(filters.regex("cust_btn_text"))
async def cust_btn_text(client, callback_query: CallbackQuery):
    curr = await db.get_setting("button_text", "⛩️ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗇 ⛩️")
    text = f"This Is Current Button text\n{curr}"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Set Button Text", callback_data="set_btn_text_prompt")],
        [InlineKeyboardButton("Delete Button", callback_data="del_btn_confirm")],
        [InlineKeyboardButton("Back", callback_data="cust_image_post"), InlineKeyboardButton("Close", callback_data="close_cust")]
    ])
    await callback_query.message.edit_text(text, reply_markup=buttons)

@Client.on_callback_query(filters.regex("set_btn_text_prompt"))
async def set_btn_text_prompt(client, callback_query: CallbackQuery):
    await callback_query.message.reply_text("Please send the button text that you want to set.")
    client.broadcast_state = getattr(client, "broadcast_state", {})
    client.broadcast_state[callback_query.from_user.id] = {"mode": "set_btn_text"}

@Client.on_callback_query(filters.regex("del_btn_confirm"))
async def del_btn_confirm(client, callback_query: CallbackQuery):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes", callback_data="del_btn_yes"), InlineKeyboardButton("No", callback_data="cust_btn_text")]
    ])
    await callback_query.message.edit_text("Are you sure you want to delete button?", reply_markup=buttons)

@Client.on_callback_query(filters.regex("del_btn_yes"))
async def del_btn_yes(client, callback_query: CallbackQuery):
    await db.delete_setting("button_text")
    await callback_query.message.edit_text("Successfully button is deleted.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="cust_btn_text")]]))


# --- Second Message ---
@Client.on_callback_query(filters.regex("cust_second_msg"))
async def cust_second_msg(client, callback_query: CallbackQuery):
    status = await db.get_setting("second_msg_on", "True")
    status_text = "Off Message" if status == "True" else "On Message"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Current Message", callback_data="curr_sec_msg")],
        [InlineKeyboardButton("Set New Message", callback_data="set_sec_msg_prompt")],
        [InlineKeyboardButton(status_text, callback_data="toggle_sec_msg")],
        [InlineKeyboardButton("Back", callback_data="cust_main")]
    ])
    await callback_query.message.edit_text("Here you can customize The second message.", reply_markup=buttons)

@Client.on_callback_query(filters.regex("curr_sec_msg"))
async def curr_sec_msg(client, callback_query: CallbackQuery):
    msg = await db.get_setting("second_msg", "Default Second Message")
    await callback_query.message.reply_text(msg)

@Client.on_callback_query(filters.regex("set_sec_msg_prompt"))
async def set_sec_msg_prompt(client, callback_query: CallbackQuery):
    await callback_query.message.reply_text("Send New Message:")
    client.broadcast_state = getattr(client, "broadcast_state", {})
    client.broadcast_state[callback_query.from_user.id] = {"mode": "set_sec_msg"}

@Client.on_callback_query(filters.regex("toggle_sec_msg"))
async def toggle_sec_msg(client, callback_query: CallbackQuery):
    curr = await db.get_setting("second_msg_on", "True")
    new_val = "False" if curr == "True" else "True"
    await db.set_setting("second_msg_on", new_val)
    
    status_text = "Off Message" if new_val == "True" else "On Message"
    # Re-render buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Current Message", callback_data="curr_sec_msg")],
        [InlineKeyboardButton("Set New Message", callback_data="set_sec_msg_prompt")],
        [InlineKeyboardButton(status_text, callback_data="toggle_sec_msg")],
        [InlineKeyboardButton("Back", callback_data="cust_main")]
    ])
    await callback_query.message.edit_text(f"Second Message is now {'on' if new_val == 'True' else 'off'}", reply_markup=buttons)

# --- Forward ---
@Client.on_callback_query(filters.regex("cust_forward"))
async def cust_forward(client, callback_query: CallbackQuery):
    status = await db.get_setting("forward_protect", "False") # False means protection OFF (forwarding allowed)
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("On" if status == "False" else "On ✅", callback_data="fwd_on"),
            InlineKeyboardButton("Off" if status == "True" else "Off ✅", callback_data="fwd_off")
        ],
        [InlineKeyboardButton("Back", callback_data="cust_main")]
    ])
    await callback_query.message.edit_text("Here you can customise the bot forward on or off (Forward Protection)", reply_markup=buttons)

@Client.on_callback_query(filters.regex("fwd_on"))
async def fwd_on(client, callback_query: CallbackQuery):
    await db.set_setting("forward_protect", "False") # Allow forward
    await callback_query.answer("Forwarding Enabled")
    await cust_forward(client, callback_query)

@Client.on_callback_query(filters.regex("fwd_off"))
async def fwd_off(client, callback_query: CallbackQuery):
    await db.set_setting("forward_protect", "True") # Disallow forward
    await callback_query.answer("Forwarding Disabled (Content Protected)")
    await cust_forward(client, callback_query)

# --- Main/Back Handler ---
@Client.on_callback_query(filters.regex("cust_main"))
async def cust_main(client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    # Re-trigger customize command manually or just show menu
    await customize_menu(client, callback_query.message)

@Client.on_callback_query(filters.regex("close_cust"))
async def close_cust(client, callback_query: CallbackQuery):
    await callback_query.message.delete()

# --- Capture Inputs for Customization ---
@Client.on_message(filters.private & ~filters.command("customize"), group=2)
async def capture_cust_input(client, message: Message):
    state = getattr(client, "broadcast_state", {}).get(message.from_user.id)
    if not state:
        return
        
    mode = state.get("mode")
    if mode == "set_caption":
        await db.set_setting("caption", message.text_html)
        await message.reply_text("Successfully added new caption.")
    elif mode == "set_image":
        if message.photo:
            await db.set_setting("image_id", message.photo.file_id)
            await message.reply_text("Image is successful setted.")
        else:
            await message.reply_text("Please send an image.")
            return
    elif mode == "set_btn_text":
        await db.set_setting("button_text", message.text)
        await message.reply_text("Successfully button text is update now.")
    elif mode == "set_sec_msg":
        await db.set_setting("second_msg", message.text_html) # Preserves formatting
        await message.reply_text("Successfully setted the new messages as second message.")
    
    # Clear state
    if mode in ["set_caption", "set_image", "set_btn_text", "set_sec_msg"]:
        del client.broadcast_state[message.from_user.id]
