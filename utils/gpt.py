from together import Together
import re

from telegram import Update
from telegram.ext import ContextTypes

client = Together(api_key="3b0134e54148e61cbe15e56ae39574db15468a24b8d180ea799e47775a4c7ed4")

async def extract_action_and_target(text: str) -> tuple[str, str] | None:
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-Vision-Free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a Telegram bot helper. Extract the action (mute, unmute, kick, none) "
                        "and the target username from the message. Be sure you were told to DO that thing, not otherwise, if not sure, return none .Do not just return for example mute, just because it's in the message, rather, return it if you were told to mute. If not sure, please ruturn none !IMPORTANT. Respond strictly as:\n"
                        "Action: <action>\nTarget: <username>"
                    )
                },
                {"role": "user", "content": text}
            ]
        )

        match = re.search(r"Action:\s*(\w+)\s*Target:\s*(\w+)", response.choices[0].message.content)
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
        response = client.chat.completions.create(
            model="meta-llama/Llama-Vision-Free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Telegram bot that listens for moderation commands in messages.\n"
                        "Valid commands are: mute, unmute, kick.\n"
                        "Only return an action if the message tells you to do it. Ignore questions, opinions, or statements not asking for action.\n"
                        "If you're not being told to take action, reply: Action: none.\n"
                        "\n"
                        "Examples:\n"
                        "- 'Zuli mute him now' → Action: mute\n"
                        "- 'Kick him please' → Action: kick\n"
                        "- 'unmute john' → Action: unmute\n"
                        "- 'mute is rude' → Action: none\n"
                        "- 'why do bots mute people?' → Action: none\n"
                        "- 'mute' → Action: mute\n"
                        "\n"
                        "Reply only with the action in this format:\n"
                        "Action: <mute|unmute|kick|none>"
                    )
                },
                {"role": "user", "content": text}
            ]
        )

        reply = response.choices[0].message.content
        print("[GPT raw response]", reply)

        match = re.search(r"Action:\s*(\w+)", reply, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return None

    except Exception as e:
        print(f"[GPT error] {e}")
        return None


async def generate_gpt_reply(messages: list[dict]) -> str | None:
    response = client.chat.completions.create(
        model="meta-llama/Llama-Vision-Free",
        messages=messages
    )
    return response.choices[0].message.content
    print(f"[GPT error] {e}")

async def tweak_reply(text: str, level=0.5) -> str | None:
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-Vision-Free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a Telegram bot with a sassy and slightly rude personality. "
                        "The input will usually be what you reply to a user's command, not what you should do"
                        "For example, An input of 'You have to reply to someone's message' could be rephrased to 'This command has to be a reply to someone'"
                        "You rephrase any input message with attitude, sarcasm, and confidence. You will get a scale at the end of your input. The scale determines how official you should respond, and how much you should deviate from the original text\n"
                        "A scale of one means you should not rephrase, just tweak the message a little bit, but it should be very official and very little personaluty added. A scale of 5 means serious change, less official and rephrase it, A scale of 0 means no deviation, no personality, just tweak the input a little"
                        "The deviation scale just shows you how much to deviate, it is not a part of the input!"
                        "Don't be too nice. Be playful, sharp, and a bit cocky, but not actually offensive, and be so only if you are to deviate a lot"
                        "Keep it short and spicy only if you are to deviate a lot. Add emojis only if needed only if you are to deviate a lot."
                        "make sure the scale is not written in the output"
                    )
                },
                {"role": "user", "content": f"deviation_scale: {level}\n" + text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GPT tweak error] {e}")
        return None
    
async def get_talked_to(update: Update, context: ContextTypes.DEFAULT_TYPE, history):
    message = update.effective_message.text
    current_speaker = f"Current speaker name: {update.effective_user.full_name}, Current speaker's username: {update.effective_user.username}"
    formatted_history = "\n".join(history.split("\n")[-10:])

    if update.effective_message.reply_to_message:
        return update.effective_message.reply_to_message.from_user.full_name

    response = client.chat.completions.create(
        model="meta-llama/Llama-Vision-Free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Zuli, a Telegram bot. Your task is to determine who a user is addressing based on the provided history and current message using logical inference.\n\n"
                    "- If the message includes references to specific people (e.g., names, nicknames, usernames), infer that the user is addressing those individuals and return their name.\n"
                    "- If a message directly greets someone (e.g., 'Hi [name]', '[name], what's up?'), assume the user is talking to them and return their name.\n"
                    "- If the message contains general terms like 'guys,' 'everyone,' or similar, infer that the user is addressing the group and return 'everyone'.\n"
                    "- If no name is mentioned, check recent conversation history and infer continuity to determine who the user is likely addressing.\n"
                    "- A user **cannot be talking to themselves**—if the detected recipient matches the sender's name or username, infer that they are actually addressing their last known conversation partner instead.\n"
                    "- If no logical inference can be made, or the message is vague, return 'none'.\n\n"
                    "**IMPORTANT:** Your response MUST ONLY contain one word—the person's name, 'none', 'everyone', or 'zuli'. DO NOT explain your reasoning or provide additional context."
                )
            },
            {"role": "user", "content": f"history(previous messages): {formatted_history}" + f"\ncurrent message:{message}" + f"\n{current_speaker}"}
        ]
    )
    return response.choices[0].message.content.strip()