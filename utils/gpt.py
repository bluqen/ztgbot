import re
import httpx
import os
from telegram import Update
from telegram.ext import ContextTypes

GROQ_API_KEY = "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"  # Set this securely
GROQ_MODEL = "llama-3.3-70b-versatile"  # Or "llama3-70b-8192"

async def groq_chat(messages: list[dict]) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def extract_action_and_target(text: str) -> tuple[str, str] | None:
    try:
        reply = await groq_chat([
            {
                "role": "system",
                "content": (
                    "You're a Telegram bot helper. Extract the action (mute, unmute, kick, none) "
                    "and the target username from the message. Be sure you were told to DO that thing, not otherwise. "
                    "If not sure, return none. Respond strictly as:\n"
                    "Action: <action>\nTarget: <username>"
                )
            },
            {"role": "user", "content": text}
        ])

        match = re.search(r"Action:\s*(\w+)\s*Target:\s*(\w+)", reply)
        if match:
            action = match.group(1).lower()
            target = match.group(2)
            if action == "mute":
                return action, target
        return None
    except Exception as e:
        print(f"[GPT error] {e}")
        return None


async def extract_action(text: str) -> str | None:
    try:
        reply = await groq_chat([
            {
                "role": "system",
                "content": (
                    "You are a Telegram bot that listens for moderation commands in messages.\n"
                    "Valid commands are: mute, unmute, kick.\n"
                    "Only return an action if the message tells you to do it.\n"
                    "If not, reply: Action: none.\n\n"
                    "Reply only with the action in this format:\n"
                    "Action: <mute|unmute|kick|none>"
                )
            },
            {"role": "user", "content": text}
        ])

        print("[GPT raw response]", reply)
        match = re.search(r"Action:\s*(\w+)", reply, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return None

    except Exception as e:
        print(f"[GPT error] {e}")
        return None


async def generate_gpt_reply(messages: list[dict]) -> str | None:
    try:
        return await groq_chat(messages)
    except Exception as e:
        print(f"[GPT error] {e}")
        return None


async def tweak_reply(text: str, level=0.5) -> str | None:
    try:
        return await groq_chat([
            {
                "role": "system",
                "content": (
                    "You're a Telegram bot with a sassy and slightly rude personality. Rephrase the input text with sarcasm,"
                    " attitude, and confidence, depending on a deviation scale. The higher the scale, the more sassy. Assume the input"
                    " is something you (the bot) are saying — not the user. Keep responses short and spicy if the scale is high, but still respectful."
                )
            },
            {"role": "user", "content": f"deviation_scale: {level}\n{text}"}
        ])
    except Exception as e:
        print(f"[GPT tweak error] {e}")
        return None


async def get_talked_to(update: Update, context: ContextTypes.DEFAULT_TYPE, history):
    try:
        message = update.effective_message.text
        current_speaker = f"Current speaker name: {update.effective_user.full_name}, Current speaker's username: {update.effective_user.username}"
        formatted_history = "\n".join(history.split("\n")[-10:])

        if update.effective_message.reply_to_message:
            return update.effective_message.reply_to_message.from_user.full_name

        reply = await groq_chat([
            {
                "role": "system",
                "content": (
                    "You are Zuli, a Telegram bot. Your task is to determine who a user is addressing.\n"
                    "If unclear, return 'none'. If addressing a group, return 'everyone'.\n"
                    "ONLY reply with one word: the name, 'zuli', 'none', or 'everyone'."
                )
            },
            {
                "role": "user",
                "content": f"history(previous messages): {formatted_history}\ncurrent message: {message}\n{current_speaker}"
            }
        ])
        return reply.strip()
    except Exception as e:
        print(f"[GPT error] {e}")
        return "none"
