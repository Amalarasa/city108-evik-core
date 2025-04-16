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

    # Проверка тайм-аута
    if telegram_id in user_last_active and now - user_last_active[telegram_id] > timedelta(seconds=SESSION_TIMEOUT):
        keyboard = [[InlineKeyboardButton("🔄 START", callback_data="start")]]
        await update.message.reply_text("Сессия завершена по таймеру. Нажми кнопку, чтобы начать заново:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    user_last_active[telegram_id] = now

    # Проверка регистрации
    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
    if not result.data:
        keyboard = [[InlineKeyboardButton("START", callback_data="start")]]
        await update.message.reply_text("Нажми кнопку, чтобы начать регистрацию:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    guest = result.data[0]
    update_data = {}

    for field in DIALOG_STEPS:
        # Если поле ещё не заполнено
        if not guest.get(field) or (field == "preferred_form" and guest[field] == guest.get("temp_name")):

            if field == "preferred_form":
                name = extract_name(text)
                update_data[field] = name
                reply = f"Приятно познакомиться, {name}! 😊 А теперь расскажи, откуда ты узнал о нашем городе City_108?"
            elif field == "source":
                update_data[field] = text
                reply = "Очень интересно! А какие у тебя есть интересы? Что тебе ближе всего?"
            elif field == "interests":
                interests = [i.strip() for i in text.split(',') if i.strip()]
                update_data[field] = interests
                reply = "А какие навыки ты уже освоил? Укажи их через запятую. 🛠"
            elif field == "skills":
                skills = [i.strip() for i in text.split(',') if i.strip()]
                update_data[field] = skills
                reply = "Спасибо большое! 🙌 Если хочешь — могу связать тебя с модератором лично."

            # Обновляем гостя в базе
            supabase.table("guests").update(update_data).eq("id_telegram", telegram_id).execute()

            # Если не последний шаг — спрашиваем следующий
            next_index = DIALOG_STEPS.index(field) + 1
            if next_index < len(DIALOG_STEPS):
                await update.message.reply_text(reply)
            else:
                await update.message.reply_text(reply + "\n\nЕсли появятся вопросы — пиши! 💬")

            return

    # Если всё уже заполнено
    await update.message.reply_text("Я на связи, если возникнут вопросы! 💬")

