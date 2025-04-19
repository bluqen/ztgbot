import json
import os

from functools import wraps

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
        
        # Check if it's a private chat or a group
        if update.effective_chat.type == "private":
            lang_code = context.user_data.get("lang", "en")  # User-specific language
        elif update.effective_chat.type in ['group', 'supergroup']:
            lang_code = context.chat_data.get(f"{chat_id}_lang", "en")  # Group-specific language
        
        # Load the corresponding language
        LANG = load_language(lang_code)
        
        # Store the LANG in context to be accessed in the handler
        context.chat_data["LANG"] = LANG
        
        # Call the original function
        return await func(update, context, *args, **kwargs)
    return wrapper