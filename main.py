from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from handlers.start import start_handler
from handlers.messages import handle_message
from handlers.commands import reset_handler, duty_handler, verify_handler, profile_handler
from handlers.callbacks import button_handler

from utils.supabase import SUPABASE_URL, SUPABASE_KEY

app = ApplicationBuilder().token(SUPABASE_KEY).build()

# Команды
app.add_handler(CommandHandler("start", start_handler))
app.add_handler(CommandHandler("reset", reset_handler))
app.add_handler(CommandHandler("duty", duty_handler))
app.add_handler(CommandHandler("verify", verify_handler))
app.add_handler(CommandHandler("profile", profile_handler))

# Сообщения и кнопки
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == '__main__':
    app.run_polling()
