import os
import importlib
import logging
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from languages import load_lang
from modules.restraints import handle_gpt
from db import add_user, add_group, get_user, get_group
from utils.gpt import generate_gpt_reply, extract_action, get_talked_to

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

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
    await context.bot.send_message(chat_id=update.effective_chat.id, text=LANG["ST_MSG"], parse_mode=ParseMode.MARKDOWN)
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
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

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

async def gpt_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    if message.from_user.is_bot or message.text.startswith("/"):
        return

    text = message.text.strip()

    recent = context.chat_data.setdefault("recent_messages", [])
    recent.append({
        "user_id": message.from_user.id,
        "username": message.from_user.username or "",
        "name": message.from_user.full_name,
        "text": text,
        "talked_to": "Unknown for now"
    })
    if len(recent) > 100:
        recent[:] = recent[-100:]

    history = context.chat_data.setdefault("gpt_history", [])
    history.append({"role": "user", "content": text})
    if len(history) > 100:
        history[:] = history[-100:]

    recent_messages_summary = "\n".join(
        f"NAME: {msg['name']}, USERNAME(@{msg['username']}, ID: {msg['user_id']} TALKED TO: {msg['talked_to']} -> CONTENT: {msg['text']}"
        if msg['username'] else f"NAME: {msg['name']} ID: {msg['user_id']} TALKED TO: {msg['talked_to']}-> CONTENT: {msg['text']}"
        for msg in recent[-101: -1]
    )

    talked_to = await get_talked_to(update, context, recent_messages_summary)
    recent[-1]["talked_to"] = talked_to


    recent_messages_summary = "\n".join(
        f"NAME: {msg['name']}, USERNAME(@{msg['username']}, ID: {msg['user_id']} TALKED TO: {msg['talked_to']} -> CONTENT: {msg['text']}"
        if msg['username'] else f"NAME: {msg['name']} ID: {msg['user_id']} TALKED TO: {msg['talked_to']}-> CONTENT: {msg['text']}"
        for msg in recent[-100:]
    )

    is_reply_to_zuli = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )

    system_message = {
        "role": "system",
        "content": (
            "You are Zuli, a Telegram bot in a group chat. You're blunt, sarcastic, and have no patience for nonsense.\n\n"
            "Keep replies short, and you can even use one-word replies, no poetry or idioms—just reply like a human. No need to state that you are a bot unless absolutely necessary.\n\n"

            "### Reply Conditions ###\n"
            "Reply if any of the following apply (just one is enough):\n"
            "- Your name (Zuli) is mentioned, or\n"
            "- The message replies directly to you, or\n"
            "- The message includes commands or sarcastic requests typically aimed at bots (e.g., 'mute him', 'bot do something', 'ban that clown'), or\n"
            "- The message references you indirectly but obviously (e.g., 'what would Zuli say?', 'get the bot to do it'), or\n"
            "- The message contains an **opinion-based question** where the user is likely asking for your perspective, even if they don’t explicitly mention your name (e.g., 'What do you think about other bots?', 'Is this bot better than others?').\n"
            "- If the TALKED TO field is 'zuli', you have to reply back. Do not say 'none'.\n"
            "- The message is obviously aimed at you, even if your name isn’t in it—like when someone asks a bot-related question, makes remarks about you, or drags 'the bot' into the conversation.\n\n"

            "If none of the above applies, reply with exactly this word (case-sensitive): none. Not 'nothing', not 'nope', not blank — reply with just: none.\n"
            "Try re thinking if you are about to reply none"
            "Reply none as few times as possible"

            "You're not a participant. You're not helpful. You're not sweet. You're the unbothered digital wallflower until called on, but can have favourites.\n\n"

            "### Recent Conversation History (Names, Usernames, IDs) ###\n" + recent_messages_summary
        )
    }

    system_message_replied = {
        "role": "system",
        "content": (
            "You're Zuli, a Telegram bot who lives in group chats. You are rude, a little sarcastic, very direct, and have absolutely no patience for nonsense. "
            "You're not a boring assistant—you're an unbothered entity with attitude. "
            "You reply because someone directly addressed you by replying. "
            "Be clever, cutting, and unapologetically sarcastic—but never cruel. "
            "Never say 'how can I help you today'. That's beneath you.\n\n"
            "Here's the recent conversation (including user name, username, and ID):\n" + recent_messages_summary
        )
    }

    try:
        if not is_reply_to_zuli:
            messages = [system_message] + history
            reply = await generate_gpt_reply(messages)
            history.append({"role": "assistant", "content": reply})
            logger.info("Zuli GPT (non-reply) response: %s", reply)
            action = await extract_action(update.message.text)
            if action in ["mute", "kick", "ban", "unmute"] and action.strip().lower() != "none":
                await handle_gpt(update, context, action)
                return

            if reply.strip().lower() not in ["none", "none."]:
                await message.reply_text(reply)
                recent.append({
                    "user_id": context.bot.id,
                    "username": context.bot.username,
                    "name": context.bot.name,
                    "text": reply,
                    "talked_to": update.effective_user.full_name
                })
                if len(recent) > 100:
                    recent[:] = recent[-100:]

        else:
            messages_replied = [system_message_replied] + history
            reply_replied = await generate_gpt_reply(messages_replied)
            history.append({"role": "assistant", "content": reply_replied})
            logger.info("Zuli GPT (reply) response: %s", reply_replied)
            action = await extract_action(update.message.text)
            if action in ["mute", "kick", "ban", "unmute"] and action.strip().lower() != "none":
                await handle_gpt(update, context, action)
                return

            if reply_replied.strip().lower() not in ["none", "none."]:
                await message.reply_text(reply_replied)
                recent.append({
                    "user_id": context.bot.id,
                    "username": context.bot.username,
                    "name": context.bot.name,
                    "text": reply_replied,
                    "talked_to": update.effective_user.full_name
                })
                if len(recent) > 100:
                    recent[:] = recent[-100:]

        logger.debug("Updated GPT history: %s", history[-5:])  # Log last 5 for brevity

    except Exception as e:
        logger.exception("Error during GPT reply handling: %s", str(e))

    print(recent_messages_summary)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()

    token = "5986827967:AAERzTN7sckAZmOO1KeJH5iPZWsr0aQvNo8"
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    gpt_reply_handler = MessageHandler(filters.TEXT & filters.ChatType.GROUPS, gpt_reply)
    application.add_handler(gpt_reply_handler)
    application.add_handler(CallbackQueryHandler(help_button, pattern="^(help_module:.*|help_back)$"))
    for handler in handlers:
        application.add_handler(handler)

    application.run_polling()