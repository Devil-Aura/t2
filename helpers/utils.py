from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import pytz

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

def get_bot_age():
    start_date = datetime(2026, 1, 26, tzinfo=pytz.UTC)
    now = datetime.now(pytz.UTC)
    diff = now - start_date
    return f"{diff.days} Days"

def get_uptime(start_time):
    now = datetime.now()
    diff = now - start_time
    return str(diff)

async def format_buttons(buttons_list):
    # Convert list of dicts to InlineKeyboardMarkup
    # This is a helper for dynamic buttons if needed
    pass
