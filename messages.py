from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from utils.supabase import supabase, user_last_active, SESSION_TIMEOUT
from utils.helpers import extract_name

dialog_steps = ["preferred_form", "source", "interests", "skills"]
questions = {
    "preferred_form": "Как мне к тебе обращаться?",
    "source": "Откуда ты узнал о городе City_108?",
    "interests": "Какие у тебя интересы? Укажи через запятую.",
    "skills": "Какие у тебя есть навыки? Укажи через запятую."
}

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
        await update.message.reply_text("Нажми кнопку, чтобы начать регистрацию:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    guest = result.data[0]
    update_data = {}

    for field in dialog_steps:
        if not guest.get(field) or (field == "preferred_form" and guest[field] == guest["temp_name"]):
            if field == "preferred_form":
                update_data[field] = extract_name(text)
            elif field in ["interests", "skills"]:
                update_data[field] = [i.strip() for i in text.split(',') if i.strip()]
            else:
                update_data[field] = text.strip()
            supabase.table("guests").update(update_data).eq("id_telegram", telegram_id).execute()
            next_index = dialog_steps.index(field) + 1
            if next_index < len(dialog_steps):
                next_field = dialog_steps[next_index]
                await update.message.reply_text(questions[next_field])
            else:
                await update.message.reply_text("Спасибо! Ты можешь пообщаться с модератором, если хочешь.")
            return

    await update.message.reply_text("Если у тебя есть дополнительные вопросы — я всегда на связи!")
