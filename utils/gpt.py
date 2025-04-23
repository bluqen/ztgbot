import openai
import re

client = openai.OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

async def extract_action_and_target(text: str) -> tuple[str, str] | None:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4",
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
    
async def extract_action(text: str) -> tuple[str, str] | None:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a Telegram bot helper. Extract the action (mute, unmute, kick, none) " +
                        "and the target username from the message. Be sure you were told to DO that thing, not otherwise, if not sure, return none .Do not just return for example mute, just because it's in the message, rather, return it if you were told to mute. If not sure, please ruturn none !IMPORTANT. Respond strictly as:\n" +
                        "Action: <action>"
                    )
                },
                {"role": "user", "content": text}
            ]
        )

        match = re.search(r"Action:\s*(\w+)", response.choices[0].message.content)
        print("[GPT raw response]", response.choices[0].message.content)
        if match:
            return match.group(1).lower()
        return None
    except Exception as e:
        print(f"[GPT error] {e}")
        return None

async def generate_gpt_reply(messages: list[dict]) -> str | None:
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content
    print(f"[GPT error] {e}")

async def tweak_reply(text: str) -> str | None:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a Telegram bot with a sassy and slightly rude personality. "
                        "You rephrase any input message with attitude, sarcasm, and confidence. "
                        "Don't be too nice. Be playful, sharp, and a bit cocky, but not actually offensive. "
                        "Keep it short and spicy. Add emojis if needed."
                    )
                },
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GPT tweak error] {e}")
        return None