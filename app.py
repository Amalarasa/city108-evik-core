import os
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SESSION_TIMEOUT = 600  # 10 минут
user_last_active = {}
duty_moderators = set()

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

# Обработка кнопки START
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start":
        user = query.from_user
        telegram_id = user.id
        full_name = user.full_name
        user_last_active[telegram_id] = datetime.utcnow()

        result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
        if result.data:
            await context.bot.send_message(chat_id=query.message.chat_id, text="Ты уже зарегистрирован в City_108.")
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

            await context.bot.send_message(chat_id=query.message.chat_id, text="Добро пожаловать в City_108! Рад встрече. Как тебя зовут?")

        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    full_name = user.full_name
    user_last_active[telegram_id] = datetime.utcnow()

    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()

    if result.data:
        guest = result.data[0]
        await update.effective_chat.send_message(f"С возвращением, {guest['preferred_form']}! Рады видеть тебя снова в City_108.")
        supabase.table("guests").update({
            "last_active": datetime.utcnow().isoformat(),
            "return_count": guest.get("return_count", 0) + 1
        }).eq("id_telegram", telegram_id).execute()
    else:
        keyboard = [[InlineKeyboardButton("🚀 START", callback_data="start")]]
        await update.effective_chat.send_message(
            "Добро пожаловать в City_108! Я — Эвик, мэр цифрового города.\nНажми кнопку, чтобы начать общение:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Команда /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("guests").delete().eq("id_telegram", telegram_id).execute()
    await update.message.reply_text("Данные сброшены. Для начала заново нажми кнопку START.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("START", callback_data="start")]]))

# Команда /duty
async def duty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moderator_id = update.effective_user.id
    duty_moderators.add(moderator_id)
    await update.message.reply_text("Ты назначен дежурным модератором. Ожидай сообщений от новых гостей!")

# Команда /verify
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("guests").update({"verified_by_moderator": True}).eq("id_telegram", telegram_id).execute()
    await update.message.reply_text("Профиль подтвержден модератором.")

# Команда /profile
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
    if result.data:
        guest = result.data[0]
        await update.message.reply_text(f"Твой профиль: \nИмя: {guest['preferred_form']}\nЯзык: {guest['language']}\nРегион: {guest['region']}\nНавыки: {guest['skills']}\nИнтересы: {guest['interests']}")
    else:
        await update.message.reply_text("Профиль не найден. Нажми START для начала.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("START", callback_data="start")]]))

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    text = update.message.text.strip()

    now = datetime.utcnow()
    if telegram_id in user_last_active and now - user_last_active[telegram_id] > timedelta(seconds=SESSION_TIMEOUT):
        keyboard = [[InlineKeyboardButton("🔄 START", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Сессия завершена по таймеру. Нажми кнопку, чтобы начать заново:", reply_markup=reply_markup)
        return
    user_last_active[telegram_id] = now

    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
    if not result.data:
        keyboard = [[InlineKeyboardButton("START", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Нажми кнопку, чтобы начать регистрацию:", reply_markup=reply_markup)
        return

    # Продолжение диалога с гостем: логика подбора модератора, вопросов и т.п.
    if text.lower() in ["да", "да, можно", "да, конечно", "да, я не против"]:
        if duty_moderators:
            moderator_id = list(duty_moderators)[0]
            await context.bot.send_message(moderator_id, f"🔔 Новый гость: {user.full_name} (ID: {telegram_id}) хочет пообщаться лично!")
            await update.message.reply_text("Я сообщил модератору. Ожидай связи 👨‍💻")
        else:
            await update.message.reply_text("Пока нет дежурных модераторов. Напиши позже или задай вопрос здесь.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("duty", duty))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
