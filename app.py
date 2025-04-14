from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

# Получаем токен из переменных окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Эвик, мэр города City_108. Добро пожаловать! 🌟\n"
        "Напиши мне что-нибудь, и я запомню твоё имя и интересы."
    )

# Создаём приложение
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

# Запуск
if __name__ == '__main__':
    print("Эвик работает в Telegram...")
    app.run_polling()
