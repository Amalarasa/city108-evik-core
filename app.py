import os
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client

# Подключение к Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Вспомогательная функция для извлечения имени из текста
def extract_name(text):
    patterns = [
        r"(?:меня зовут|меня звать|мо[её] имя|я|зови меня|называй меня)[\s:]+([А-Яа-яA-Za-z\-]+)",
        r"^([А-Яа-яA-Za-z\-]{3,})$"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().capitalize()
    return text.strip().split()[0].capitalize()

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
            "is_complete": False,
            "verified_by_moderator": False,
            "waits_for_moderator_reply": False
        }).execute()

        new_guest_id = guest_insert.data[0]['id']

        supabase.table("guest_profiles").insert({"guest_id": new_guest_id}).execute()
        supabase.table("guest_analytics").insert({"guest_id": new_guest_id}).execute()

        await update.message.reply_text(
            "Добро пожаловать в City_108! Я — Эвик, мэр цифрового города. Очень рад знакомству.\n"
            "Как могу к тебе обращаться? Напиши своё имя или ник."
        )

# Команда /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("guests").delete().eq("id_telegram", telegram_id).execute()
    await update.message.reply_text("Данные удалены. Напиши /start, чтобы начать сначала.")

# Команда /profile
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
    if not result.data:
        await update.message.reply_text("Ты ещё не зарегистрирован. Напиши /start для начала.")
        return

    guest = result.data[0]
    await update.message.reply_text(
        f"Имя: {guest['preferred_form']}\n"
        f"Источник: {guest['source']}\n"
        f"Интересы: {', '.join(guest['interests']) if guest['interests'] else 'не указаны'}\n"
        f"Навыки: {', '.join(guest['skills']) if guest['skills'] else 'не указаны'}\n"
        f"Статус регистрации: {'завершена' if guest['is_complete'] else 'не завершена'}"
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

    # Проверка на ожидание ответа модератору
    if guest.get("waits_for_moderator_reply"):
        if text.lower() in ["да", "yes", "хочу", "можно"]:
            supabase.table("guests").update({"waits_for_moderator_reply": False}).eq("id_telegram", telegram_id).execute()
            await update.message.reply_text("Отлично! Я передам твое желание модератору. Он скоро с тобой свяжется.")
        elif text.lower() in ["нет", "не хочу", "не надо"]:
            supabase.table("guests").update({"waits_for_moderator_reply": False}).eq("id_telegram", telegram_id).execute()
            await update.message.reply_text("Понял. Если передумаешь — просто напиши.")
        else:
            await update.message.reply_text("Просто напиши «да» или «нет» — хочешь ли ты пообщаться с модератором?")
        return

    # Логика диалога поэтапно
    if not guest.get("preferred_form") or guest["preferred_form"] == guest["temp_name"]:
        name = extract_name(text)
        supabase.table("guests").update({"preferred_form": name}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Благодарю. Теперь скажи, пожалуйста, откуда ты узнал о нашем городе?")
    elif not guest.get("source") or guest["source"] == "unknown":
        supabase.table("guests").update({"source": text}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Очень интересно. А что тебя вдохновило прийти в City_108? Чем бы ты хотел заняться?")
    elif not guest.get("interests"):
        interests = [i.strip() for i in text.split(',') if i.strip()]
        supabase.table("guests").update({"interests": interests}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Спасибо! А какие у тебя есть навыки или умения, которые ты хотел бы применить здесь?")
    elif not guest.get("skills"):
        skills = [i.strip() for i in text.split(',') if i.strip()]
        supabase.table("guests").update({
            "skills": skills,
            "is_complete": True,
            "waits_for_moderator_reply": True
        }).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Отлично. Это поможет нам найти тебе подходящие направления. Хочешь ли ты пообщаться с модератором лично?")
    else:
        if text.lower() in ["да", "yes"]:
            await update.message.reply_text("Я передам твоё желание модератору. Он скоро с тобой свяжется.")
        elif "сколько" in text.lower() and "людей" in text.lower():
            await update.message.reply_text("City_108 — город, который растёт каждый день. Уже десятки людей участвуют в его строительстве!")
        else:
            await update.message.reply_text("City_108 всегда открыт для тебя. Если появятся вопросы — пиши!")

    supabase.table("guests").update({"last_active": datetime.utcnow().isoformat()}).eq("id_telegram", telegram_id).execute()

# Команда для модератора: подтвердить участника
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Пожалуйста, укажи telegram_id участника. Пример: /verify 123456789")
        return

    try:
        target_id = int(args[0])
        result = supabase.table("guests").select("*").eq("id_telegram", target_id).execute()
        if result.data:
            supabase.table("guests").update({
                "verified_by_moderator": True
            }).eq("id_telegram", target_id).execute()
            await update.message.reply_text(f"Участник с id {target_id} подтвержден.")
        else:
            await update.message.reply_text("Такой участник не найден.")
    except ValueError:
        await update.message.reply_text("Неверный формат id. Укажи числовой telegram_id.")

# Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
