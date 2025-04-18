from telegram import ChatMemberAdministrator, ChatMemberOwner, ChatMemberRestricted
from telegram.ext import ContextTypes

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