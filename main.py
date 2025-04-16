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
FIO, IVENT, PHONE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! Вас приветствует Культурный центр «Строгино». "
        "Культурный центр «Строгино» — многофункциональная современная площадка для проведения мероприятий любых форматов и степени сложности. "
        "Расположен в Северо-Западном административном округе города Москвы рядом со станцией метро «Строгино». "
        "Площадь культурного центра составляет 5 783 кв.м. Стандартная вместимость культурного центра — 750 человек, "
        "вместимость концертного зала — 510 человек. Для артистов предусмотрены 6 гримёрных комнат вместимостью до 150 человек.\n\n"
        "Как мы можем к Вам обращаться?"
    )
    return FIO

async def get_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fio'] = update.message.text
    await update.message.reply_text(
        "Чтобы предоставить вам точную информацию о стоимости аренды площадки, мне нужно немного больше данных о планируемом мероприятии. "
        "Пожалуйста, укажите:\n\n1. Дату и время мероприятия.\n2. Ожидаемое количество гостей.\n3. Формат мероприятия (например, банкет, фуршет, конференция и т.д.)."
    )
    return IVENT

async def get_ivent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ivent'] = update.message.text
    contact_button = KeyboardButton("Отправить номер", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Теперь отправьте ваш номер телефона:", reply_markup=keyboard)
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    fio = context.user_data['fio']
    ivent = context.user_data.get('ivent', 'не указано')
    message = f"📥 Новая заявка:\n👤 ФИО: {fio}\n📞 Телефон: {phone}\n🎉 Мероприятие: {ivent}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    await update.message.reply_text("Спасибо! Мы с вами свяжемся.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)],
            IVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ivent)],
            PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    print("✅ Бот запущен.")
    application.run_polling()

if __name__ == "__main__":
    main()
