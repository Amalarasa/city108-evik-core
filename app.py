import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client, Client

# Подключение к Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Telegram токен
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # Проверяем, есть ли пользователь в базе
    result = supabase.table("users").select("*").eq("telegram_id", user_id).execute()

    if result.data:
        user = result.data[0]
        await update.message.reply_text(
            f"С возвращением, {user['full_name']}! 👋\n"
            f"Ты уже зарегистрирован в городе City_108 как {user['status']}."
        )
        # Обновляем время активности
        supabase.table("users").update({
            "last_active": datetime.utcnow().isoformat()
        }).eq("telegram_id", user_id).execute()

    else:
        # Новый пользователь — создаём как гостя
        supabase.table("users").insert({
            "telegram_id": user_id,
            "full_name": full_name,
            "status": "guest",
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat()
        }).execute()

        await update.message.reply_text(
            f"Привет, {full_name}! 👋\n"
            "Ты пока гость в городе City_108. Расскажи немного о себе, чтобы я помог тебе найти своё место ✨"
        )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Проверка в базе
    result = supabase.table("users").select("*").eq("telegram_id", user_id).execute()

    if not result.data:
        await update.message.reply_text(
            "Ты пока не зарегистрирован. Напиши /start, чтобы я мог узнать тебя."
        )
        return

    user = result.data[0]
    name = user['full_name']

    await update.message.reply_text(
        f"{name}, я услышал: «{text}». Спасибо за доверие! 🙏"
    )

    # В будущем можно сохранять интересы в JSON-поле

# Запуск приложения
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Эвик активен.")
    app.run_polling()
