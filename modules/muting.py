import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

from datetime import datetime, timedelta

from utils.chat import is_admin

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    target_user = None
    username = None

    keyboard = [[
        InlineKeyboardButton("Till unmute", callback_data="set_mute"),
        InlineKeyboardButton("+1 hour", callback_data="add_an_hr")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        username = target_user.username or target_user.first_name
        username_type = 0 if target_user.username else 1
    
    elif context.args:
        username = context.args[0].lstrip('@')
        try:
            member = await context.bot.get_chat_member(chat_id, f"@{username}")
            target_user = member.user
        except Exception as e:
            await update.message.reply_text(f"Couldn't find @{username} in this chat.")
            return
    else:
        await update.message.reply_text("Usage: /mute @username or reply to a user with /mute")
        return
    if target_user:
        if not await is_admin(update, context, target_user.id):
            print("DDDD")
            if not username_type:
                await update.message.reply_text(f"Mute @{username} for how long?", reply_markup=reply_markup)
            else:
                await update.message.reply_text(f"Mute {username} for how long?", reply_markup=reply_markup)
        else:
            await update.message.reply_text("I can't mute an admin, unfortunately")
    
    context.user_data["target_user"] = target_user
    context.user_data["username"] = username
    context.user_data["username_type"] = username_type
    context.user_data["mute_dur"] = 0

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("+1 hour", callback_data="add_an_hr"),
        InlineKeyboardButton("Done", callback_data="set_mute")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    # Get the target user and their username from the context
    target_user = context.user_data.get('target_user')
    username = context.user_data.get('username')

    if not target_user:
        await query.edit_message_text("No user selected for mute.")
        return

    if query.data == "add_an_hr":
        context.user_data["mute_dur"] += 1
        if not context.user_data.get("username_type"):
            await query.edit_message_text(f"Mute @{username} for {context.user_data.get('mute_dur')} hours?", reply_markup=reply_markup)
        else:
            await query.edit_message_text(f"Mute {username} for {context.user_data.get('mute_dur')} hours?", reply_markup=reply_markup)

    if query.data == "set_mute":
        if not context.user_data.get("username_type"):
            await query.edit_message_text(f"Muted @{username} for {context.user_data.get('mute_dur')} hours")
        else:
            await query.edit_message_text(f"Muted {username} for {context.user_data.get('mute_dur')} hours")

    if context.user_data.get("mute_dur") > 0:
        until = datetime.utcnow() + timedelta(hours=context.user_data.get("mute_dur"))  # 1 hour mute
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
    else:
        await query.edit_message_text(f"Muted {username}!")
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )

mute_handler = CommandHandler("mute", mute)
mute_button_handler = CallbackQueryHandler(button)