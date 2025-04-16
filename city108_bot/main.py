# main.py — основной запуск Telegram-бота
import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from handlers.start import start_handler
from handlers.messages import handle_message
from handlers.commands import reset_handler, duty_handler, verify_handler, profile_handler
from handlers.callbacks import button_handler

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Получение токена из переменных среды
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in environment variables.")

# Инициализация бота
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Обработчики команд
app.add_handler(CommandHandler("start", start_handler))
app.add_handler(CommandHandler("reset", reset_handler))
app.add_handler(CommandHandler("duty", duty_handler))
app.add_handler(CommandHandler("verify", verify_handler))
app.add_handler(CommandHandler("profile", profile_handler))

# Обработчики обычных сообщений и inline-кнопок
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == '__main__':
    app.run_polling()
