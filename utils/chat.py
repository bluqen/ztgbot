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