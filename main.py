import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.constants import ParseMode

from modules.mute import mute_handler, mute_button_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[
            InlineKeyboardButton("Bluebify", url="t.me/bluebify")
        ]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="*This* __is__ `my` _owner_", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

if __name__ == '__main__':
    application = ApplicationBuilder().token('5986827967:AAERzTN7sckAZmOO1KeJH5iPZWsr0aQvNo8').build()
    
    start_handler = CommandHandler('start', start)
    owner_handler = CommandHandler('owner', owner)
    application.add_handler(start_handler)
    application.add_handler(owner_handler)
    application.add_handler(mute_handler)
    application.add_handler(mute_button_handler)
    
    application.run_polling(timeout=-1)