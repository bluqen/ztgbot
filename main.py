import os
import importlib
import logging
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

from languages import load_lang

from db import add_user, add_group, get_user, get_group

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Flask Dummy Server ---
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- Telegram Bot Setup ---
def load_modules_and_handlers():
    modules = {}
    handlers = []

    for filename in os.listdir('modules'):
        if filename.endswith('.py') and filename != '__init__.py':
            file_module_name = filename[:-3]
            module = importlib.import_module(f'modules.{file_module_name}')
            display_name = getattr(module, "__module_name__", file_module_name)
            modules[display_name] = module
            if hasattr(module, "__handlers__"):
                handlers.extend(module.__handlers__)
    return modules, handlers

modules, handlers = load_modules_and_handlers()

@load_lang
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=LANG["ST_MSG"], parse_mode="Markdown")
    if update.effective_chat.type in ["group", "supergroup"]:
        group_id = update.effective_chat.id
        group_data = await get_group(group_id)
        language = group_data.get("language", "en")
        other_settings = group_data.get("other_settings", {})
        await add_group(group_id, language, other_settings)
    elif update.effective_chat.type == "private":
        user_id = update.effective_chat.id
        username = update.effective_user.username
        user_data = await get_user(user_id, username)
        language = user_data.get("language", "en")
        other_settings = user_data.get("other_settings", {})
        await add_user(user_id, username, language, other_settings)

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
    await update.message.reply_text(LANG["HP_MSG"], reply_markup=reply_markup)

@load_lang
async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("help_module:"):
        mod_name = data.split(":", 1)[1]
        module = modules.get(mod_name)
        help_text = LANG.get(f"HP_{getattr(module, '__module_code__')}", LANG["HP_404"])
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

# --- Run bot + server ---
if __name__ == '__main__':
    # Run Flask in a separate thread
    threading.Thread(target=run_flask).start()

    # Get token from environment
    #token = os.environ["BOT_TOKEN"]
    token = "5986827967:AAERzTN7sckAZmOO1KeJH5iPZWsr0aQvNo8"
    # Run Telegram bot
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CallbackQueryHandler(help_button, pattern="^(help_module:.*|help_back)$"))
    for handler in handlers:
        application.add_handler(handler)

    application.run_polling()
