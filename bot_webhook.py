import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from database import Database

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

# Инициализация бота и БД
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Шаги регистрации
class Form(StatesGroup):
    name = State()
    contact = State()

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Давай запишу тебя в клуб. Как тебя зовут?")
    await state.set_state(Form.name)

@dp.message(Command("id"))
async def get_chat_id(message: Message):
    await message.answer(f"🆔 Твой chat_id: {message.chat.id}")

@dp.message(Command("stats"))
async def get_stats(message: Message):
    """Команда для просмотра статистики (только для админа)"""
    if message.from_user.id == ADMIN_CHAT_ID:
        count = db.get_member_count()
        await message.answer(f"📊 Всего участников: {count}")
    else:
        await message.answer("У вас нет доступа к этой команде.")

@dp.message(StateFilter(Form.name))
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Отлично! Теперь отправь номер телефона или Telegram username.")
    await state.set_state(Form.contact)

@dp.message(StateFilter(Form.contact))
async def process_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()

    # Подтверждение пользователю
    await message.answer("✅ Ты успешно записан в клуб! Мы свяжемся с тобой.")

    # Сохраняем в базу данных
    success = db.add_member(
        date=str(message.date),
        name=data['name'],
        contact=data['contact'],
        username=message.from_user.username,
        user_id=message.from_user.id
    )

    if success:
        # Уведомление админу
        try:
            text = (
                "📥 Новая заявка на членство в клубе:\n"
                f"👤 Имя: {data['name']}\n"
                f"📞 Контакт: {data['contact']}\n"
                f"🆔 Telegram: @{message.from_user.username or 'не указано'}\n"
                f"🆔 User ID: {message.from_user.id}"
            )
            await bot.send_message(ADMIN_CHAT_ID, text)
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения админу: {e}")
    else:
        await message.answer("⚠️ Произошла ошибка при сохранении данных. Попробуйте позже.")

    await state.clear()

# Функции для webhook
async def on_startup(bot: Bot):
    # Устанавливаем webhook
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    # Удаляем webhook
    await bot.delete_webhook()

def main():
    # Создаем aiohttp веб-приложение
    app = web.Application()
    
    # Подключаем хендлеры бота
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    # Запускаем веб-сервер
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    web.run_app(app, host="0.0.0.0", port=APP_PORT)

if __name__ == "__main__":
    main()
