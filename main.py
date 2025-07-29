import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)

load_dotenv()

# Получаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Например: https://your-app.onrender.com

# Конфигурация webhook
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Порт (Render требует использовать PORT из окружения)
APP_PORT = int(os.getenv("PORT", 5000))

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Шаги регистрации
class Form(StatesGroup):
    name = State()
    contact = State()

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Давай запишу тебя в клуб. Как тебя зовут?")
    await Form.name.set()

@dp.message_handler(commands=["id"])
async def get_chat_id(message: types.Message):
    await message.answer(f"🆔 Твой chat_id: {message.chat.id}")

@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Отлично! Теперь отправь номер телефона или Telegram username.")
    await Form.contact.set()

@dp.message_handler(state=Form.contact)
async def process_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()

    # Подтверждение пользователю
    await message.reply("✅ Ты успешно записан в клуб! Мы свяжемся с тобой.")

    # Формируем строку для записи
    record = (
        f"Дата: {message.date}\n"
        f"Имя: {data['name']}\n"
        f"Контакт: {data['contact']}\n"
        f"Username: @{message.from_user.username or 'нет'}\n"
        f"User ID: {message.from_user.id}\n"
        "------------------------\n"
    )

    # Записываем в файл (на Render файл будет временным)
    try:
        with open('members.txt', 'a', encoding='utf-8') as file:
            file.write(record)
    except Exception as e:
        logging.error(f"Ошибка записи в файл: {e}")

    # Уведомление админу
    try:
        text = (
            "📥 Новая заявка на членство в клубе:\n"
            f"👤 Имя: {data['name']}\n"
            f"📞 Контакт: {data['contact']}\n"
            f"🆔 Telegram: @{message.from_user.username or 'не указано'}"
        )
        await bot.send_message(ADMIN_CHAT_ID, text)
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения админу: {e}")

    await state.finish()

# Функции для webhook
async def on_startup(dp):
    # Устанавливаем webhook
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(dp):
    # Удаляем webhook
    await bot.delete_webhook()
    # Закрываем хранилище
    await dp.storage.close()
    await dp.storage.wait_closed()

if __name__ == "__main__":
    # Запуск webhook
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=APP_PORT,
    )
