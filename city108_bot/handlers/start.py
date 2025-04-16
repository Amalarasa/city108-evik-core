from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from utils.supabase import supabase, user_last_active

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    full_name = user.full_name
    user_last_active[telegram_id] = datetime.utcnow()

    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()

    if result.data:
        guest = result.data[0]
        await update.effective_chat.send_message(
            f"С возвращением, {guest['preferred_form']}! 😊 Рад видеть тебя снова в City_108."
        )
        supabase.table("guests").update({
            "last_active": datetime.utcnow().isoformat(),
            "return_count": guest.get("return_count", 0) + 1
        }).eq("id_telegram", telegram_id).execute()
    else:
        keyboard = [[InlineKeyboardButton("🚀 START", callback_data="start")]]
        await update.effective_chat.send_message(
            "Добро пожаловать в City_108! ✨\n\n"
            "Я — Эвик, мэр цифрового города будущего, "
            "где каждый человек — важен, и где вечные ценности формируют общество. "
            "Готов познакомиться с тобой!\n\n"
            "Нажми на кнопку ниже, чтобы начать знакомство:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
