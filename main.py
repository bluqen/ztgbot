import logging, importlib, os
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

from modules.muting import mute_handler, mute_button_handler, unmute_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

def load_modules():
    modules = {}
    for filename in os.listdir('modules'):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]  # Remove '.py' extension
            module = importlib.import_module(f'modules.{module_name}')
            modules[module_name] = module
    return modules

modules = load_modules()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(module_name, callback_data=module_name)]
        for module_name in modules
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Click on a module to view its help content:",
        reply_markup=reply_markup
    )

async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    module_name = query.data

    # Get the help content from the selected module
    module = modules.get(module_name)
    if module and hasattr(module, '__help__'):
        help_content = module.__help__
    else:
        help_content = "No help content available for this module."

    # Edit the message with the help content of the selected module
    await query.edit_message_text(help_content)

@app.route('/')
def home():
    return 'Bot is running!'

if __name__ == '__main__':
    application = ApplicationBuilder().token('5986827967:AAERzTN7sckAZmOO1KeJH5iPZWsr0aQvNo8').build()
    
    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    help_button_handler = CallbackQueryHandler(help_button)
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(help_button_handler)
    application.add_handler(mute_handler)
    application.add_handler(unmute_handler)
    application.add_handler(mute_button_handler)
    
    application.run_polling(timeout=-1)

    app.run(host='0.0.0.0', port=5000)