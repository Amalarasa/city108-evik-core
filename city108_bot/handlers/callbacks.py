from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from utils.supabase import supabase, user_last_active

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
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Ты уже зарегистрирован в City_108. Добро пожаловать обратно! 😊"
            )
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

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=(
                    "Приветствую тебя в City_108! ✨\n\n"
                    "Я — Эвик, мэр этого цифрового города. Здесь ты можешь раскрыть свои таланты, "
                    "присоединиться к проектам и почувствовать настоящую ценность общения.\n\n"
                    "Давай начнём с простого. Как мне к тебе обращаться?"
                )
            )

        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
