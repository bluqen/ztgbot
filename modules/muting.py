import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatPermissions, MessageEntity
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

from datetime import datetime, timedelta

from utils.chat import is_admin, is_bot, has_admin_permission, has_user_restriction

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    target_user = None
    username = None
    permission_required = "can_restrict_members"

    keyboard = [[
        InlineKeyboardButton("Till unmute", callback_data="set_mute"),
        InlineKeyboardButton("+1 hour", callback_data="add_an_hr")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        username = target_user.username or target_user.first_name
        if target_user.username:
            username="@" + username

    else:
        await update.message.reply_text("Reply to the user's message with /mute")
        return
    if target_user:
        if await is_bot(update, context, target_user.id):
            await update.message.reply_text("I will not mute myself, thank you.")
        elif await has_admin_permission(context, chat_id, user_id, permission_required):
            if not await is_admin(update, context, target_user.id):
                await update.message.reply_text(f"Mute <a href='tg://user?id={target_user.id}'>{username}</a> for how long?", reply_markup=reply_markup, parse_mode="HTML")
            else:
                await update.message.reply_text("I can't mute an admin, unfortunately.")
        else:
            await update.message.reply_text(f"If you can't do it, I can't\nYou'll need permission: `{permission_required}`", parse_mode="MarkdownV2")
        
    context.chat_data["target_user"] = target_user
    context.chat_data["username"] = username
    context.chat_data["mute_dur"] = 0

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    target_user = None
    username = None
    permission_required = "can_restrict_members"

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        username = target_user.username or target_user.first_name
        if target_user.username:
            username="@" + username

    else:
        await update.message.reply_text("Reply to the user's message with /unmute")
        return
    if target_user:
        if await is_bot(update, context, target_user.id):
            await update.message.reply_text("I was probably not muted if you can see this.")
        elif await has_admin_permission(context, chat_id, user_id, permission_required):
            if not await has_user_restriction(context, chat_id, target_user.id, "can_send_messages"):
                await update.message.reply_text("This user isn't muted though.")
            else:
                await update.message.reply_text(f"Unmuted <a href='tg://user?id={target_user.id}'>{username}!</a>", parse_mode="HTML")
                await context.bot.restrict_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=target_user.id,
                    permissions=ChatPermissions(can_send_messages=True)
                )
        else:
            await update.message.reply_text(f"If you can't do it, I can't\nYou'll need permission: `{permission_required}`", parse_mode="MarkdownV2")
    context.chat_data["target_user"] = target_user
    context.chat_data["username"] = username
    context.chat_data["mute_dur"] = 0

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("Done", callback_data="set_mute"),
        InlineKeyboardButton("+1 hour", callback_data="add_an_hr")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    if query.data in []:
        await query.answer()  # Acknowledge the callback query

    # Get the target user and their username from the context
    target_user = context.chat_data.get('target_user')
    username = context.chat_data.get('username')

    if not target_user:
        await query.edit_message_text("Reply to the user's message with /mute")
        return

    unmute_keyboard = [[
        InlineKeyboardButton("Unmute", callback_data=f"unmute:{target_user.id}")
    ]]
    unmute_markup = InlineKeyboardMarkup(unmute_keyboard)

    if not target_user:
        await query.edit_message_text("Reply to the user's message with /mute")
        return

    if query.data == "add_an_hr":
        user = query.from_user
        chat = query.message.chat
        permission_required = "can_restrict_members"
        if await has_admin_permission(context, chat.id, user.id, permission_required):
            context.chat_data["mute_dur"] += 1
            await query.edit_message_text(f"Mute <a href='tg://user?id={target_user.id}'>{username}</a> for {context.chat_data.get('mute_dur')} hours?", reply_markup=reply_markup, parse_mode="HTML")
        else:
            await query.answer(f"If you can't do it, I can't\nYou'll need permission: {permission_required}", show_alert=True)

    if query.data == "set_mute":
        user = query.from_user
        chat = query.message.chat
        permission_required = "can_restrict_members"
        if await has_admin_permission(context, chat.id, user.id, permission_required):
            if context.chat_data.get("mute_dur") > 0:
                await query.edit_message_text(f"Muted <a href='tg://user?id={target_user.id}'>{username}</a> for {context.chat_data.get('mute_dur')} hours", parse_mode="HTML", reply_markup=unmute_markup)
                until = datetime.utcnow() + timedelta(hours=context.chat_data.get("mute_dur"))  # 1 hour mute
                await context.bot.restrict_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=target_user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until
                )
            else:
                await query.edit_message_text(f"Muted <a href='tg://user?id={target_user.id}'>{username}</a>!", parse_mode="HTML", reply_markup=unmute_markup)
                await context.bot.restrict_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=target_user.id,
                    permissions=ChatPermissions(can_send_messages=False)
                )
        else:
            await query.answer(f"If you can't do it, I can't\nYou'll need permission: {permission_required}", show_alert=True)

    if query.data.startswith("unmute:"):
        user = query.from_user
        chat = query.message.chat
        permission_required = "can_restrict_members"
        target_user_id = int(query.data.split(":")[1])

        if await has_admin_permission(context, chat.id, user.id, permission_required):
            if not has_user_restriction(context, chat.id, target_user_id, "can_send_messages"):
                await query.edit_message_text("This user isn't muted though.")
            else:
                await query.edit_message_text(f"Unmuted <a href='tg://user?id={target_user_id}'>{username}!</a>", parse_mode="HTML")
                await context.bot.restrict_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=target_user_id,
                    permissions=ChatPermissions(can_send_messages=True)
                )
        else:
            await query.answer(f"If you can't do it, I can't\nYou'll need permission: {permission_required}", show_alert=True)

mute_handler = CommandHandler("mute", mute)
mute_button_handler = CallbackQueryHandler(button)
unmute_handler = CommandHandler("unmute", unmute)

__module_name__ = "Muting"
__help__ = """
Short but efficient commands to silence those who deserve to be.

__Commands__
/mute - Reply this to a member's message to mute them, for a specific time or indefinitely.
/unmute - Reply this to a member's message to unmute them.
"""