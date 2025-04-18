async def is_admin(update, context, user_id=None):
    chat = update.effective_chat
    user_id = user_id or update.effective_user.id

    member = await context.bot.get_chat_member(chat.id, user_id)
    return member.status in ["administrator", "creator"]