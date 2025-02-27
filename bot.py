import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

# Конфигурация
TOKEN = "7699973329:AAF1h3N8FuL0y8yhzu2zMU7bV28ZEdb0kJs"  # ваш токен
CHANNEL_ID = "-1002480574817"  # числовой chat_id канала

# Публичный домен вашего приложения на Render
WEBHOOK_HOST = "https://telegram-app-vhli.onrender.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start (пример)
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я работаю на вебхуках.")

# Периодическая отправка сообщений в канал
async def send_message_periodically():
    while True:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text="Привет")
        except Exception as e:
        await asyncio.sleep(600)  # 600 секунд = 10 минут

# Функция запуска приложения aiohttp
async def on_startup(app: web.Application):
    # Устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    # Запускаем периодическую задачу
    asyncio.create_task(send_message_periodically())

# Функция остановки приложения
async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()

# Создаем приложение aiohttp и регистрируем обработчик вебхука
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    # Запускаем сервер на порту 8443 (можно изменить, если требуется)
    web.run_app(app, host="0.0.0.0", port=8443)
