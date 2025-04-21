from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from db import add_user, add_group

from languages import load_lang

# Supported language codes
AVAILABLE_LANGUAGES = ["en", "fr", "es"]
AVAILABLE_LANGUAGES_FORMAT = ["`en`", "`fr`", "`es`"]  # Add more as needed
language_full = {
    "en": "English",
    "fr": "French | Francais",
    "es": "Spanish | Espanol"
}

# Command: /setlang <language_code>
@load_lang
async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]
    if not context.args:
        available = ", ".join(AVAILABLE_LANGUAGES)
        return await update.message.reply_text(
            LANG["LNG_ERR_ARGS"].format(available=available)
        )

    lang_code = context.args[0].lower()

    if lang_code not in AVAILABLE_LANGUAGES:
        available = ", ".join(AVAILABLE_LANGUAGES_FORMAT)
        return await update.message.reply_text(
            LANG["LNG_ERR_404"].format(lang_code=lang_code, available=available), parse_mode="Markdown"
        )

    chat_type = update.effective_chat.type
    if chat_type == "private":
        user_id = update.message.from_user.id
        username = update.message.from_user.username

        # Save the new language for the user
        await add_user(user_id, username, lang_code)

        context.user_data["lang"] = lang_code

    elif chat_type in ["group", "supergroup"]:
        group_id = update.effective_chat.id

        # Save the new language for the group
        await add_group(group_id, lang_code)
        context.chat_data[f"{update.effective_chat.id}_lang"] = lang_code

    lf = language_full[lang_code.lower()]
    await update.message.reply_text(
        LANG["LNG_SET"].format(language_full=lf), parse_mode="Markdown"
    )

# Export handler for the bot to load
setlang_handler = CommandHandler("setlang", setlang)

__module_code__ = "LNG"
__handlers__ = [setlang_handler]