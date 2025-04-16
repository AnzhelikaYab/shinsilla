from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from flask import Flask
from threading import Thread
import os

# === Веб-сервер для UptimeRobot ===
app = Flask('')

@app.route('/')
def home():
    return "Я живой!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# === Переменные окружения ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
if ADMIN_ID is None:
    raise ValueError("Переменная окружения ADMIN_ID не установлена.")
else:
    ADMIN_ID = int(ADMIN_ID)

# === Этапы диалога ===
FIO, PHONE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пожалуйста, введите своё ФИО:")
    return FIO

async def get_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fio'] = update.message.text
    contact_button = KeyboardButton("Отправить номер", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Теперь отправьте ваш номер телефона:", reply_markup=keyboard)
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    fio = context.user_data['fio']
    message = f"📥 Новая заявка:\n👤 ФИО: {fio}\n📞 Телефон: {phone}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    await update.message.reply_text("Спасибо! Мы с вами свяжемся.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)],
            PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("✅ Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()
