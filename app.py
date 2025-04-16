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

# Обработка кнопки START (по таймеру или первой встрече)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start":
        await start(update, context)
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
        await update.effective_chat.send_message(
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

        await update.effective_chat.send_message(
            "Добро пожаловать в City_108! Я — Эвик, мэр цифрового города. Как могу к тебе обращаться?"
        )

# Остальные команды, включая /reset, /duty, /verify, /profile — здесь ...

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

    # Продолжение логики общения с гостем (skills, интересы и т.д.) ...

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
