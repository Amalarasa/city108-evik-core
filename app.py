import os
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SESSION_TIMEOUT = 600  # 10 минут

user_last_active = {}  # Временный словарь для контроля простоя

# Извлечение имени из сообщения
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
    user_last_active[telegram_id] = datetime.utcnow()

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
            "Добро пожаловать в City_108! Я — Эвик, мэр цифрового города. Как могу к тебе обращаться?"
        )

# Команда /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("guests").delete().eq("id_telegram", telegram_id).execute()
    await update.message.reply_text("Данные удалены. Нажми /start, чтобы начать сначала.")

# Команда /duty
async def duty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    name = update.effective_user.full_name
    supabase.table("moderators_on_duty").upsert({
        "telegram_id": telegram_id,
        "name": name,
        "on_duty_since": datetime.utcnow().isoformat()
    }, on_conflict=["telegram_id"]).execute()
    await update.message.reply_text("Ты отмечен как дежурный модератор. Я буду направлять тебе запросы гостей.")

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

# Уведомление всех дежурных модераторов
async def notify_moderators(context, guest):
    moderators = supabase.table("moderators_on_duty").select("*").execute().data
    if not moderators:
        return
    text = (
        f"🔔 Новый запрос на связь с модератором:\n\n"
        f"Имя: {guest['preferred_form']}\n"
        f"Интересы: {', '.join(guest['interests'])}\n"
        f"Навыки: {', '.join(guest['skills'])}\n"
        f"Telegram ID: {guest['id_telegram']}\n\n"
        f"Подтвердить: /verify {guest['id_telegram']}"
    )
    for mod in moderators:
        try:
            await context.bot.send_message(chat_id=mod['telegram_id'], text=text)
        except:
            continue

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    text = update.message.text.strip()

    now = datetime.utcnow()
    if telegram_id in user_last_active and now - user_last_active[telegram_id] > timedelta(seconds=SESSION_TIMEOUT):
        keyboard = [[InlineKeyboardButton("🔄 START", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Сессия завершена по таймеру. Нажми кнопку, чтобы начать сначала:", reply_markup=reply_markup)
        return
    user_last_active[telegram_id] = now

    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
    if not result.data:
        await update.message.reply_text("Напиши /start, чтобы начать заново.")
        return

    guest = result.data[0]
    guest_id = guest['id']
    supabase.table("messages_log").insert({
        "guest_id": guest_id,
        "message_text": text,
        "timestamp": now.isoformat()
    }).execute()

    if guest.get("waits_for_moderator_reply"):
        if text.lower() in ["да", "yes", "хочу"]:
            supabase.table("guests").update({"waits_for_moderator_reply": False}).eq("id_telegram", telegram_id).execute()
            await update.message.reply_text("Отлично! Я передам твоё желание модератору.")
            await notify_moderators(context, guest)
        elif text.lower() in ["нет", "не хочу"]:
            supabase.table("guests").update({"waits_for_moderator_reply": False}).eq("id_telegram", telegram_id).execute()
            await update.message.reply_text("Понял. Если передумаешь — просто напиши.")
        else:
            await update.message.reply_text("Напиши «да» или «нет», чтобы я понял твой ответ.")
        return

    if not guest.get("preferred_form") or guest["preferred_form"] == guest["temp_name"]:
        name = extract_name(text)
        supabase.table("guests").update({"preferred_form": name}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Спасибо. Скажи, откуда ты узнал о нашем городе?")
    elif not guest.get("source") or guest["source"] == "unknown":
        supabase.table("guests").update({"source": text}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("А что тебя вдохновило прийти в City_108? Чем бы ты хотел заняться?")
    elif not guest.get("interests"):
        interests = [i.strip() for i in text.split(',') if i.strip()]
        supabase.table("guests").update({"interests": interests}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Спасибо! А какие у тебя есть навыки?")
    elif not guest.get("skills"):
        skills = [i.strip() for i in text.split(',') if i.strip()]
        supabase.table("guests").update({"skills": skills, "is_complete": True, "waits_for_moderator_reply": True}).eq("id_telegram", telegram_id).execute()
        await update.message.reply_text("Спасибо, это поможет нам подобрать тебе проект. Хочешь ли ты пообщаться с модератором?")
    else:
        await update.message.reply_text("City_108 открыт для тебя. Если будут вопросы — пиши!")
    supabase.table("guests").update({"last_active": now.isoformat()}).eq("id_telegram", telegram_id).execute()

# Подтверждение участника командой /verify
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Укажи telegram_id участника. Пример: /verify 123456789")
        return
    try:
        target_id = int(args[0])
        result = supabase.table("guests").select("*").eq("id_telegram", target_id).execute()
        if result.data:
            supabase.table("guests").update({"verified_by_moderator": True}).eq("id_telegram", target_id).execute()
            await update.message.reply_text(f"Участник с id {target_id} подтвержден.")
        else:
            await update.message.reply_text("Такой участник не найден.")
    except ValueError:
        await update.message.reply_text("Неверный формат id. Укажи числовой telegram_id.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("duty", duty))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
