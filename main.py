import os
import importlib
import logging
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

from languages import load_language, load_lang

from modules.muting import mute_handler, mute_button_handler, unmute_handler

from db import add_user, get_user

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

def load_modules_and_handlers():
    modules = {}
    handlers = []

    for filename in os.listdir('modules'):
        if filename.endswith('.py') and filename != '__init__.py':
            file_module_name = filename[:-3]  # Remove '.py' extension
            module = importlib.import_module(f'modules.{file_module_name}')
            display_name = getattr(module, "__module_name__", file_module_name)
            modules[display_name] = module
        if hasattr(module, "__handlers__"):
            handlers.extend(module.__handlers__)
    return modules, handlers

modules = load_modules_and_handlers()[0]
handlers = load_modules_and_handlers()[1]

@load_lang
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=LANG["ST_MSG"], parse_mode="Markdown")

@load_lang
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]
    keyboard = []
    row = []

    for i, name in enumerate(modules.keys(), 1):
        row.append(InlineKeyboardButton(LANG[modules.get(name).__module_code__], callback_data=f"help_module:{name}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        LANG["HP_MSG"],
        reply_markup=reply_markup
    )

@load_lang
async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]

    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("help_module:"):
        mod_name = data.split(":", 1)[1]
        module = modules.get(mod_name)
        help_text = getattr(module, "__help__", LANG["HP_404"])
        help_text = LANG[f"HP_{getattr(module, "__module_code__")}"]

        # Add back button
        keyboard = [[InlineKeyboardButton("« Back", callback_data="help_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")

    elif data == "help_back":
        keyboard = []
        row = []

        for i, name in enumerate(modules.keys(), 1):
            row.append(InlineKeyboardButton(LANG[modules.get(name).__module_code__], callback_data=f"help_module:{name}"))
            if i % 3 == 0:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(LANG["HP_MSG"], reply_markup=reply_markup)

@app.route('/')
def home():
    return 'Bot is running!'

if __name__ == '__main__':
    application = ApplicationBuilder().token('5986827967:AAERzTN7sckAZmOO1KeJH5iPZWsr0aQvNo8').build()
    
    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    help_button_handler = CallbackQueryHandler(help_button, pattern="^(help_module:.*|help_back)$")
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(help_button_handler)
    for handler in handlers:
        application.add_handler(handler)
    
    application.run_polling(timeout=-1)

    app.run(host='0.0.0.0', port=5000)