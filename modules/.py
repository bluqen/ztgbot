from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import json

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("===== RAW UPDATE =====")
    print(json.dumps(update.to_dict(), indent=2))
    print("======================")

    msg = update.message
    if msg and msg.reply_to_message:
        user = msg.reply_to_message.from_user
        await msg.reply_text(f"Reply detected! User: {user.first_name} (ID: {user.id})")
    else:
        await msg.reply_text("No reply detected.")

app = ApplicationBuilder().token("5986827967:AAERzTN7sckAZmOO1KeJH5iPZWsr0aQvNo8").build()
app.add_handler(CommandHandler("mute", mute))
app.run_polling()