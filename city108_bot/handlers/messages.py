from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from utils.supabase import supabase, user_last_active, SESSION_TIMEOUT
from utils.helpers import extract_name

# Порядок диалога и вопросы
DIALOG_STEPS = ["preferred_form", "source", "interests", "skills"]
QUESTIONS = {
    "preferred_form": "Скажи, как мне к тебе обращаться? 😊",
    "source": "Приятно познакомиться, {name}! А как ты узнал о нашем городе City_108?",
    "interests": "Здорово! А чем бы ты хотел заниматься в городе? Поделись своими интересами. 🎯",
    "skills": "Отлично, а какие у тебя есть навыки? Укажи через запятую. 🛠"
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

    for field in DIALOG_STEPS:
        if not guest.get(field) or (field == "preferred_form" and guest[field] == guest.get("temp_name")):
            if field == "preferred_form":
                name = extract_name(text)
                update_data[field] = name
                reply = QUESTIONS[field]
            elif field in ["interests", "skills"]:
                values = [i.strip() for i in text.split(',') if i.strip()]
                update_data[field] = values
                reply = QUESTIONS[field]
            else:
                update_data[field] = text
                name = guest.get("preferred_form", "друг")
                reply = QUESTIONS[field].format(name=name)

            supabase.table("guests").update(update_data).eq("id_telegram", telegram_id).execute()

            next_index = DIALOG_STEPS.index(field) + 1
            if next_index < len(DIALOG_STEPS):
                next_field = DIALOG_STEPS[next_index]
                await update.message.reply_text(reply)
            else:
                await update.message.reply_text("Благодарю тебя за ответы 🙏 Если хочешь — могу связать тебя с модератором лично.")
            return

    await update.message.reply_text("Я на связи, если возникнут вопросы! 💬")
