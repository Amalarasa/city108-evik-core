from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.supabase import supabase, user_last_active
from datetime import datetime

duty_moderators = set()

async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("guests").delete().eq("id_telegram", telegram_id).execute()
    await update.message.reply_text(
        "Данные сброшены. Для начала заново нажми кнопку START.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("START", callback_data="start")]])
    )

async def duty_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moderator_id = update.effective_user.id
    duty_moderators.add(moderator_id)
    await update.message.reply_text("Ты назначен дежурным модератором. Ожидай запросов от гостей.")

async def verify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("guests").update({"verified_by_moderator": True}).eq("id_telegram", telegram_id).execute()
    await update.message.reply_text("Профиль подтверждён модератором.")

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
    if result.data:
        guest = result.data[0]
        await update.message.reply_text(
            f"Твой профиль:\nИмя: {guest['preferred_form']}\n"
            f"Источник: {guest['source']}\nИнтересы: {', '.join(guest['interests'])}\n"
            f"Навыки: {', '.join(guest['skills'])}\n"
            f"Статус регистрации: {'завершена' if guest['is_complete'] else 'в процессе'}"
        )
    else:
        await update.message.reply_text(
            "Профиль не найден. Нажми START, чтобы начать.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("START", callback_data="start")]])
        )
