import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

from datetime import datetime, timedelta

from utils.chat import is_admin, is_bot, has_admin_permission, has_user_restriction, group_only

from languages import load_language, load_lang

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

@group_only
@load_lang
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    target_user = None
    permission_required = "can_restrict_members"

    keyboard = [[
        InlineKeyboardButton(LANG["MTG_KB_IDF"], callback_data="set_mute"),
        InlineKeyboardButton(LANG["MTG_KB_PLS1"], callback_data="add_an_hr")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        fullname = target_user.full_name
    else:
        await update.message.reply_text(LANG["MTG_ERR_REP"], parse_mode="Markdown")
        return

    if target_user:
        if await is_bot(update, context, target_user.id):
            await update.message.reply_text(LANG["MTG_ERR_SLF"])
        elif await has_admin_permission(context, chat_id, user_id, permission_required):
            if not await is_admin(update, context, target_user.id):
                await update.message.reply_text(
                    LANG["MTG_TIME"].format(user_id=target_user.id, fullname=fullname),
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(LANG["MTG_ERR_ADM"])
        else:
            await update.message.reply_text(
                LANG["MTG_ERR_PRM"].format(permission_required=permission_required),
                parse_mode="Markdown"
            )

    context.chat_data["target_user"] = target_user
    context.chat_data["fullname"] = fullname
    context.chat_data["mute_dur"] = 0

@group_only
@load_lang
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    target_user = None
    permission_required = "can_restrict_members"

    if update.effective_chat.type in ["group", "supergroup"]:
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            fullname=target_user.first_name
        else:
            await update.message.reply_text(LANG["MTG_ERR_REP"])
            return

        if target_user:
            if await is_bot(update, context, target_user.id):
                await update.message.reply_text(LANG["MTG_ERR_UNMUTE_SLF"])
            elif await has_admin_permission(context, chat_id, user_id, permission_required):
                if not await has_user_restriction(context, chat_id, target_user.id, "can_send_messages"):
                    await update.message.reply_text(LANG["MTG_ERR_NOTMUTED"])
                else:
                    await update.message.reply_text(
                        LANG["MTG_UNMUTED"].format(user_id=target_user.id, fullname=fullname),
                        parse_mode="HTML"
                    )
                    await context.bot.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=target_user.id,
                        permissions=ChatPermissions(can_send_messages=True)
                    )
            else:
                await update.message.reply_text(
                    LANG["MTG_ERR_PRM"].format(permission_required=permission_required),
                    parse_mode="Markdown"
                )

        context.chat_data["target_user"] = target_user
        context.chat_data["fullname"] = fullname
        context.chat_data["mute_dur"] = 0
    else:
        await update.message.reply_text(LANG["ERR_PM"])

@load_lang
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]

    keyboard = [[
        InlineKeyboardButton(LANG["MTG_KB_DONE"], callback_data="set_mute"),
        InlineKeyboardButton(LANG["MTG_KB_PLS1"], callback_data="add_an_hr")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query

    target_user = context.chat_data.get("target_user")
    fullname = context.chat_data.get("fullname")

    if not target_user:
        await query.edit_message_text(LANG["MTG_ERR_REP"])
        return

    unmute_keyboard = [[
        InlineKeyboardButton(LANG["MTG_KB_UNMUTE"], callback_data=f"unmute:{target_user.id}")
    ]]
    unmute_markup = InlineKeyboardMarkup(unmute_keyboard)

    user = query.from_user
    chat = query.message.chat
    permission_required = "can_restrict_members"
    

    hour_label = "hour" if context.chat_data["mute_dur"] == 0 else "hours"
    if query.data == "add_an_hr":
        if await has_admin_permission(context, chat.id, user.id, permission_required):
            context.chat_data["mute_dur"] += 1
            await query.edit_message_text(
                LANG["MTG_HRS"].format(
                    user_id=target_user.id,
                    fullname=fullname,
                    hours=context.chat_data["mute_dur"],
                    hour_label=hour_label
                ),
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await query.answer(LANG["MTG_ERR_PRM"].format(permission_required=permission_required), show_alert=True)

    elif query.data == "set_mute":
        if await has_admin_permission(context, chat.id, user.id, permission_required):
            if context.chat_data.get("mute_dur") > 0:
                await query.edit_message_text(
                    LANG["MTG_MUTED_HRS"].format(
                        user_id=target_user.id,
                        fullname=fullname,
                        hours=context.chat_data["mute_dur"],
                        hour_label=hour_label
                    ),
                    parse_mode="HTML",
                    reply_markup=unmute_markup
                )
                until = datetime.utcnow() + timedelta(hours=context.chat_data.get("mute_dur"))
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=target_user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until
                )
            else:
                await query.edit_message_text(
                    LANG["MTG_MUTED"].format(
                        user_id=target_user.id,
                        fullname=fullname
                    ),
                    parse_mode="HTML",
                    reply_markup=unmute_markup
                )
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=target_user.id,
                    permissions=ChatPermissions(can_send_messages=False)
                )
        else:
            await query.answer(LANG["MTG_ERR_PRM"].format(permission_required=permission_required), show_alert=True)

    elif query.data.startswith("unmute:"):
        target_user_id = int(query.data.split(":" )[1])
        if await has_admin_permission(context, chat.id, user.id, permission_required):
            if not await has_user_restriction(context, chat.id, target_user_id, "can_send_messages"):
                await query.edit_message_text(LANG["MTG_ERR_NOTMUTED"])
            else:
                await query.edit_message_text(
                    LANG["MTG_UNMUTED"].format(user_id=target_user_id, fullname=fullname),
                    parse_mode="HTML"
                )
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=target_user_id,
                    permissions=ChatPermissions(can_send_messages=True)
                )
        else:
            await query.answer(LANG["MTG_ERR_PRM"].format(permission_required=permission_required), show_alert=True)

mute_handler = CommandHandler("mute", mute)
mute_button_handler = CallbackQueryHandler(button, pattern="^(add_an_hr|set_mute|unmute:.*)$")
unmute_handler = CommandHandler("unmute", unmute)

__module_code__ = "MTG"
__handlers__ = [mute_handler, mute_button_handler, unmute_handler]
