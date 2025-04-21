LOG_GRP_ID = -1002662799867

LOG_GROUP_ID = int(LOG_GRP_ID)

async def log_event(bot, message: str):
    try:
        await bot.send_message(chat_id=LOG_GRP_ID, text=message)
    except Exception as e:
        print(f"Failed to log event: {e}")
