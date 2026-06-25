from telegram import Update, Bot
from auth import get_user_by_chat_id, link_telegram, unlink_telegram, authenticate_user
import os

BASE_URL = os.environ.get("BASE_URL", "https://trusted.vercel.app")


async def handle_update(update: Update, bot: Bot):
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == "/start":
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "Welcome to Trusted Bot!\n\n"
                "Available commands:\n"
                "/login - Connect your Telegram to your account\n"
                "/link <email> <password> - Link this chat to your account\n"
                "/logoff - Disconnect Telegram from your account\n"
                "/help - Show this message"
            )
        )
    elif text == "/help":
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "Available commands:\n"
                "/start - Welcome message\n"
                "/login - Get login link\n"
                "/link <email> <password> - Link this chat to your account\n"
                "/logoff - Disconnect Telegram from your account\n"
                "/help - This message"
            )
        )
    elif text.startswith("/login"):
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"Visit {BASE_URL}/login to log in to your account.\n\n"
                f"Use /link youremail@example.com yourpassword to connect this chat."
            )
        )
    elif text.startswith("/link"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await bot.send_message(
                chat_id=chat_id,
                text="Usage: /link youremail@example.com yourpassword"
            )
            return
        email = parts[1].strip()
        password = parts[2].strip()
        user = authenticate_user(email, password)
        if not user:
            await bot.send_message(
                chat_id=chat_id,
                text="Invalid email or password. Sign up at " + BASE_URL + "/signup"
            )
            return
        if user.telegram_chat_id:
            await bot.send_message(
                chat_id=chat_id,
                text="This email is already linked to a Telegram account."
            )
            return
        link_telegram(user, str(chat_id))
        await bot.send_message(
            chat_id=chat_id,
            text=f"✅ Telegram linked to {email} successfully!"
        )
    elif text.startswith("/logoff"):
        user = get_user_by_chat_id(str(chat_id))
        if user:
            unlink_telegram(str(chat_id))
            await bot.send_message(
                chat_id=chat_id,
                text="Your Telegram account has been disconnected."
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="Your Telegram is not linked to any account."
            )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text="Unknown command. Use /help to see available commands."
        )
