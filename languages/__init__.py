import json
import os

from functools import wraps

from db import get_group, get_user

def load_language(lang_code: str):
    path = os.path.join(os.path.dirname(__file__), f"{lang_code}.json")
    if not os.path.isfile(path):
        path = os.path.join(os.path.dirname(__file__), "en.json")  # fallback

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def load_lang(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        chat_id = update.effective_chat.id
        lang_code = "en"  # Default language
        
        user_id = None
        if update.message:
            user_id = update.message.from_user.id
        else:
            pass
        group_id = update.effective_chat.id if update.effective_chat.type in ["group", "supergroup"] else None
        
        if user_id:
            user_data = await get_user(user_id)
            lang_code = user_data.get("language", "en")

        # If in a group, override the language based on group setting
        if group_id:
            group_data = await get_group(group_id)
            group_lang_code = group_data.get("language", "en")
            lang_code = group_lang_code  # Group language takes precedence

        # Load the corresponding language
        LANG = load_language(lang_code)
        
        # Store the LANG in context to be accessed in the handler
        context.chat_data["LANG"] = LANG
        
        # Call the original function
        return await func(update, context, *args, **kwargs)
    return wrapper