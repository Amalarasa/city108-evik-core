from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.supabase import supabase, user_last_active
from datetime import datetime

duty_moderators = set()

async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("guests").delete().eq("id_telegram", telegram_id).execute()
    await update.message.reply_text(
        "🗑️ Твои данные удалены. Хочешь начать всё заново? Просто нажми кнопку ниже:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 START", callback_data="start")]])
    )

async def duty_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moderator_id = update.effective_user.id
    duty_moderators.add(moderator_id)
    await update.message.reply_text("🧭 Ты отмечен как дежурный модератор. Я сообщу тебе, если гость захочет поговорить.")

async def verify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("guests").update({"verified_by_moderator": True}).eq("id_telegram", telegram_id).execute()
    await update.message.reply_text("✅ Твой профиль был подтверждён. Добро пожаловать в полноправные участники City_108!")

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    result = supabase.table("guests").select("*").eq("id_telegram", telegram_id).execute()
    if result.data:
        guest = result.data[0]
        await update.message.reply_text(
            f"📄 Твой профиль:\n"
            f"Имя: {guest['preferred_form']}\n"
            f"Источник: {guest['source']}\n"
            f"Интересы: {', '.join(guest['interests']) or 'не указаны'}\n"
            f"Навыки: {', '.join(guest['skills']) or 'не указаны'}\n"
            f"Регистрация: {'завершена' if guest['is_complete'] else 'в процессе'}"
        )
    else:
        await update.message.reply_text(
            "👤 Профиль не найден. Хочешь зарегистрироваться? Нажми кнопку ниже:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 START", callback_data="start")]])
        )
