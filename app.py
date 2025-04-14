import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Простой словарь для хранения пользователей (в памяти)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Эвик, мэр города City_108. Добро пожаловать! 👋\n"
        "Напиши мне что-нибудь, и я запомню твоё имя и интересы."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        user_data[user_id] = {
            "name": update.effective_user.first_name,
            "interests": [text]
        }
        await update.message.reply_text(
            f"Я запомнил тебя, {update.effective_user.first_name}! "
            f"Ты написал: «{text}». Это уже интересно 🤖"
        )
    else:
        user_data[user_id]["interests"].append(text)
        await update.message.reply_text(
            f"Ты уже в базе, {user_data[user_id]['name']}! "
            f"Хочешь рассказать больше? 😉"
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Эвик активен.")
    app.run_polling()
