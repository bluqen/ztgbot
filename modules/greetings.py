from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from languages import load_lang

from db import get_group, add_group # Directly interact with the database to get group data

# Create a greeting message when new members join
@load_lang
async def greet_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]
    group_id = update.effective_chat.id
    
    # Fetch the group greeting message from the database
    group_data = await get_group(group_id)
    greeting_message = group_data.get("other_settings", {}).get("greeting_message", LANG["GRT_GRT_MSG"])  # Default message if no custom greeting is set
    
    # Loop through all new members in the chat
    for new_member in update.message.new_chat_members:
        fullname = new_member.full_name
        firstname = new_member.first_name
        username = new_member.username if new_member.username else new_member.first_name
        id = new_member.id
        lastname = new_member.last_name
        # Send the greeting message
        await update.message.reply_text(greeting_message.format(fullname=fullname, firstname=firstname, username=username, id=id, lastname=lastname))

# Create a farewell message when a member leaves
@load_lang
async def farewell_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LANG = context.chat_data["LANG"]
    group_id = update.effective_chat.id
    
    # Fetch the group greeting message from the database
    group_data = await get_group(group_id)
    farewell_message = group_data.get("other_settings", {}).get("farewell_message", LANG["GRT_FRW_MSG"])  # Default message if no custom greeting is set
    
    left_member = update.message.left_chat_member
    fullname = left_member.full_name
    firstname = left_member.first_name
    username = left_member.username if left_member.username else left_member.first_name
    id = left_member.id
    lastname = left_member.last_name
    # Send the greeting message
    await update.message.reply_text(farewell_message.format(fullname=fullname, firstname=firstname, username=username, id=id, lastname=lastname))

# Handlers for new members joining and members leaving
greet_new_member_handler = MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_members)
farewell_member_handler = MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, farewell_left_member)

@load_lang
async def set_greeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    if context.args:
        greeting_message = " ".join(context.args)
        # Save the new greeting message to the database
        group_data = await get_group(group_id)
        other_settings = group_data.get("other_settings", {})
        other_settings["greeting_message"] = greeting_message
        await add_group(group_id, other_settings=other_settings)
        await update.message.reply_text(f"Group greeting message updated to: {greeting_message}")
    else:
        await update.message.reply_text("Please provide a greeting message after the command.")

@load_lang
async def set_farewell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    if context.args:
        farewell_message = " ".join(context.args)
        # Save the new greeting message to the database
        group_data = await get_group(group_id)
        other_settings = group_data.get("other_settings", {})
        other_settings["farewell_message"] = farewell_message
        await add_group(group_id, other_settings=other_settings)
        await update.message.reply_text(f"Group farewell message updated to: {farewell_message}")
    else:
        await update.message.reply_text("Please provide a farewell message after the command.")


# Add the handler for the set_greeting command
set_greeting_handler = CommandHandler("setgreeting", set_greeting)
set_farewell_handler = CommandHandler("setfarewell", set_farewell)

__module_code__ = "GRT"
__handlers__ = [greet_new_member_handler, farewell_member_handler, set_greeting_handler, set_farewell_handler]
