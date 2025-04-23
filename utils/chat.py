from telegram import Update, ChatMemberAdministrator, ChatMemberOwner, ChatMemberRestricted
from telegram.ext import ContextTypes

from functools import wraps
from languages import load_lang

def group_only(func):
    @wraps(func)
    @load_lang
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        LANG = context.chat_data["LANG"]
        chat_type = update.effective_chat.type
        if chat_type not in ['group', 'supergroup']:
            await update.effective_message.reply_text(LANG["ERR_PM"])
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


async def has_admin_permission(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, permission: str) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)

        # Owners have all permissions
        if isinstance(member, ChatMemberOwner):
            return True

        # Check if admin and has the requested permission
        if isinstance(member, ChatMemberAdministrator):
            return getattr(member, permission, False)

        # Not an admin
        return False

    except Exception as e:
        print(f"Error checking permission: {e}")
        return False

def only_admin(func):
    @wraps(func)
    @load_lang
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        LANG = context.chat_data["LANG"]
        user_id = update.effective_user.id
        chat = update.effective_chat

        # Only apply in groups/supergroups
        if chat.type not in ["group", "supergroup"]:
            return

        # Get chat admins
        chat_administrators = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in chat_administrators]

        # Check if the user is an admin
        if user_id not in admin_ids:
            await update.message.reply_text(LANG["ERR_ADM"])
            return

        return await func(update, context, *args, **kwargs)

    return wrapper

async def is_admin(update, context, user_id=None):
    chat_id = update.effective_chat.id
    user_id = user_id or update.effective_user.id

    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False
    
async def is_bot(update, context, user_id=None):
    bot_id = context.bot.id
    user_id = user_id or update.effective_user.id
    return bot_id == user_id

async def has_user_restriction(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    restriction: str
) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)

        # Only restricted users can have restrictions
        if isinstance(member, ChatMemberRestricted):
            # Check if the attribute exists and return its value
            return not getattr(member, restriction, True)

        # Admins/members usually have all permissions
        return False

    except Exception as e:
        print(f"Error checking restriction: {e}")
        return False
    
def bot_admin_required(required_perms=None):
    required_perms = required_perms or []

    def decorator(func):
        @wraps(func)
        @load_lang
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            LANG = context.chat_data["LANG"]
            chat = update.effective_chat
            bot = context.bot

            bot_member = await bot.get_chat_member(chat_id=chat.id, user_id=bot.id)

            # Check if bot is admin
            if bot_member.status not in ["administrator", "creator"]:
                await update.message.reply_text(LANG["ERR_BOT_ADM"])
                return

            # Check required permissions
            missing_perms = [
                perm for perm in required_perms
                if not getattr(bot_member, perm, False)
            ]

            if missing_perms:
                await update.message.reply_text(LANG["ERR_BOT_PRM"].format(perms=', '.join(missing_perms)), parse_mode="Markdown")
                return

            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator