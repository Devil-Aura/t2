from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import Config
from bot.helpers.utils import get_bot_age
from datetime import datetime, timedelta
from bot.plugins.start import delete_message

@Client.on_message(filters.command(["about", "info"]) & filters.private)
async def about_command(client, message: Message):
    bot_age = get_bot_age()
    text = (
        "About The Bot\n"
        "🤖 My Name :- <a href='https://telegra.ph/Crunchy-Roll-Vault-04-08'>Crunchyroll Link Provider</a>\n"
        f"Bot Age :- {bot_age} (26/01/2026)\n"
        "Anime Channel :- <a href='https://t.me/Crunchyrollchannel'>Crunchy Roll Channel</a>\n"
        "Language :- <a href='https://t.me/Crunchyrollchannel'>Python</a>\n"
        "Developer: :- <a href='https://t.me/World_Fastest_Bots'>World Fastest Bots</a>\n\n"
        "This Is Private/Paid Bot Provided By\n"
        "@World_Fastest_Bots."
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆", url="https://t.me/World_Fastest_Bots")],
        [InlineKeyboardButton("World Fastest Bots", url="https://t.me/World_Fastest_Bots")]
    ])
    
    msg = await message.reply_text(text, reply_markup=buttons, quote=True, disable_web_page_preview=True)
    
    run_date = datetime.now() + timedelta(seconds=Config.ABOUT_MSG_DELETE_TIME)
    client.scheduler.add_job(delete_message, "date", run_date=run_date, args=[client, message.chat.id, msg.id])
