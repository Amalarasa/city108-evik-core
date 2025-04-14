import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client, Client
from datetime import datetime

# Ключи и настройки (Render зачитывает их из env)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Эвик, мэр города City_108. Добро пожаловать! \nНапиши мне что-нибудь, и я запомню твоё имя и интересы."
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    now = datetime.utcnow().isoformat()

    guest_data = {
        "temp_name": user.full_name,
        "preferred_form": "Evyk",
        "language": user.language_code or "unknown",
        "region": "unknown"
    }

    existing = sb.table("guests").select("id").eq("temp_name", guest_data["temp_name"]).execute()
    if not existing.data:
        guest_insert = sb.table("guests").insert(guest_data).execute()
        guest_id = guest_insert.data[0]["id"]
    else:
        guest_id = existing.data[0]["id"]

    analytics_data = {
        "guest_id": guest_id,
        "interest_trig": text,
        "session_dur": 0,
        "return_count": 1,
        "avg_depth": 1,
        "platform_type": "telegram",
        "traffic_source": "bot",
        "age_range": "unknown",
        "gender": "unknown",
        "lead_categor": "unknown"
    }
    sb.table("guest_analytics").insert(analytics_data).execute()

    await update.message.reply_text(f"Спасибо за сообщение, {user.first_name}! Я запомнил тебя.")

# Запуск бота
if __name__ == '__main__':
    import asyncio
    
    async def main():
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("Эвик работает в Telegram...")
        await app.run_polling()

    asyncio.run(main())
