import os
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Например: https://ваш_сервис_на_render.com
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=MemoryStorage())


# Шаги регистрации
class Form(StatesGroup):
    name = State()
    contact = State()

# Старт
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Давай запишу тебя в клуб. Как тебя зовут?")
    await Form.name.set()

@dp.message_handler(commands=["id"])
async def get_chat_id(message: types.Message):
    print(f"Получено сообщение /id от пользователя: {message.from_user.id}")
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

    # Записываем в файл
    with open('members.txt', 'a', encoding='utf-8') as file:
        file.write(record)

    # Уведомление админу
    text = (
        "📥 Новая заявка на членство в клубе:\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Контакт: {data['contact']}\n"
        f"🆔 Telegram: @{message.from_user.username or 'не указано'}"
    )
    await bot.send_message(ADMIN_CHAT_ID, text)

    await state.finish()

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
