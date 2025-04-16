import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client

# Подключение к Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    full_name = user.full_name

    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()

    if result.data:
        guest = result.data[0]
        await update.message.reply_text(
            f"С возвращением, {guest['preferred_form']}! Рады видеть тебя снова в City_108."
        )
        supabase.table("guests").update({
            "last_active": datetime.utcnow().isoformat(),
            "return_count": guest.get("return_count", 0) + 1
        }).eq("id_telegram", telegram_id).execute()
    else:
        guest_insert = supabase.table("guests").insert({
            "id_telegram": telegram_id,
            "temp_name": full_name,
            "preferred_form": full_name,
            "language": user.language_code or "unknown",
            "region": "unknown",
            "source": "unknown",
            "interests": [],
            "skills": [],
            "status": "guest",
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "return_count": 1,
            "is_complete": False
        }).execute()

        new_guest_id = guest_insert.data[0]['id']

        supabase.table("guest_profiles").insert({"guest_id": new_guest_id}).execute()
        supabase.table("guest_analytics").insert({"guest_id": new_guest_id}).execute()

        await update.message.reply_text(
            "Welcome to City_108! I'm Evyk, the mayor of this digital city. It's wonderful to meet you.\n"
            "How may I address you? Could you tell me your name or nickname?"
        )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    text = update.message.text.strip()

    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
    if not result.data:
        await update.message.reply_text("Пожалуйста, напиши /start, чтобы начать общение.")
        return

    guest = result.data[0]
    guest_id = guest['id']

    # Логирование сообщения
    supabase.table("messages_log").insert({
        "guest_id": guest_id,
        "message_text": text,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    if not guest.get("language") or guest["language"] == "unknown":
        supabase.table("guests").update({"language": text}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Спасибо! Теперь скажи, пожалуйста, откуда ты узнал о City_108?")
    elif not guest.get("source") or guest["source"] == "unknown":
        supabase.table("guests").update({"source": text}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Благодарю. Теперь расскажи, что бы ты хотел узнать о городе?")
    elif not guest.get("interests"):
        interests = [i.strip() for i in text.split(',') if i.strip()]
        supabase.table("guests").update({"interests": interests}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Спасибо! А теперь можешь рассказать немного о своих навыках?")
    elif not guest.get("skills"):
        skills = [i.strip() for i in text.split(',') if i.strip()]
        supabase.table("guests").update({"skills": skills, "is_complete": True}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Благодарю тебя, это очень поможет. Хочешь ли ты пообщаться с модератором напрямую?")
    else:
        if text.lower() in ["да", "yes"]:
            await update.message.reply_text("Хорошо, я передам твоё желание модератору. Он скоро свяжется с тобой.")
        else:
            await update.message.reply_text("City_108 всегда открыт для тебя. Если появятся вопросы — пиши!")

    supabase.table("guests").update({"last_active": datetime.utcnow().isoformat()}).eq("id_telegram", telegram_id).execute()

# Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
