import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client

# Настройки Supabase и Telegram
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    full_name = update.effective_user.full_name

    user = supabase.table("guest").select("*").eq("telegram_id", telegram_id).execute().data

    if user:
        user = user[0]
        await update.message.reply_text(f"С возвращением, {user['full_name']}! 👋 Ты уже зарегистрирован в City_108 как гость.")
        supabase.table("guest").update({"last_active": datetime.utcnow().isoformat()}).eq("telegram_id", telegram_id).execute()
    else:
        supabase.table("guest").insert({
            "telegram_id": telegram_id,
            "full_name": full_name,
            "status": "guest",
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "return_count": 1
        }).execute()

        await update.message.reply_text(
            "Welcome to City_108! I'm Evyk, the mayor of this digital city. It's wonderful to meet you. "
            "How may I address you? Could you tell me your name or nickname?"
        )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    text = update.message.text

    user_result = supabase.table("guest").select("*").eq("telegram_id", telegram_id).execute().data
    if not user_result:
        await update.message.reply_text("You are not registered yet. Please type /start.")
        return

    user = user_result[0]

    if not user.get('language'):
        supabase.table("guest").update({"language": text}).eq("telegram_id", telegram_id).execute()
        await update.message.reply_text("Спасибо! Теперь скажи, пожалуйста, откуда ты узнал о City_108?")
    elif not user.get('source'):
        supabase.table("guest").update({"source": text}).eq("telegram_id", telegram_id).execute()
        await update.message.reply_text("Отлично! У тебя есть вопросы о городе? Задавай!")
    elif not user.get('interests'):
        interests = text.split(', ')
        supabase.table("guest").update({"interests": interests}).eq("telegram_id", telegram_id).execute()
        await update.message.reply_text("Спасибо! Теперь расскажи немного о своих навыках или опыте, связанных с твоими интересами.")
    elif not user.get('skills'):
        skills = text.split(', ')
        supabase.table("guest").update({"skills": skills}).eq("telegram_id", telegram_id).execute()
        await update.message.reply_text("Здорово! Хочешь ли ты пообщаться с модератором напрямую?")
    else:
        if text.lower() in ['да', 'yes']:
            await update.message.reply_text("Отлично! Я сообщу модератору, и он свяжется с тобой скоро.")
        else:
            await update.message.reply_text(
                f"Хорошо, {user['full_name']}, я уважаю твоё решение. City_108 всегда открыт для тебя. "
                "Буду рад видеть тебя снова. Желаю хорошего дня!"
            )

    # Обновление активности
    supabase.table("guest").update({"last_active": datetime.utcnow().isoformat(), "return_count": user['return_count'] + 1}).eq("telegram_id", telegram_id).execute()

# Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Эвик работает и ждёт гостей в City_108.")
    app.run_polling()
