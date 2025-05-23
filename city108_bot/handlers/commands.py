from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.supabase import supabase, user_last_active
from datetime import datetime
from utils.supabase import moderator_on_duty

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
    moderator_name = update.effective_user.full_name or "Без имени"

    # Обновляем текущего дежурного в оперативной памяти
    moderator_on_duty["id"] = moderator_id

    # Добавляем или обновляем дежурного в Supabase
    supabase.table("moderators_on_duty").upsert({
        "telegram_id": moderator_id,
        "name": moderator_name,
        "on_duty_since": datetime.utcnow().isoformat()
    }).execute()

    await update.message.reply_text(
        "🧭 Ты теперь дежурный модератор. Я сообщу тебе, если гость захочет пообщаться."
    )

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
