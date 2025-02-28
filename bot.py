import asyncio
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo  # для московского времени
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

# Конфигурация
TOKEN = "7699973329:AAF1h3N8FuL0y8yhzu2zMU7bV28ZEdb0kJs"
CHANNEL_ID = -1002480574817  # числовой chat_id канала

# Списки администраторов для отчётов (ID администраторов группы)
DAILY_ADMIN_IDS = [168554128, 5607311019]
WEEKLY_ADMIN_IDS = [168554128, 5607311019]

WEBHOOK_HOST = "https://telegram-app-vhli.onrender.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Файл для хранения данных пользователей
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    """Загружает данные из файла subscribers.json или возвращает пустой словарь."""
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_subscribers(data):
    """Сохраняет данные в файл subscribers.json."""
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Обработчик для любых сообщений – сбор информации о пользователях, пишущих в канале
@dp.message()
async def log_user_data(message: types.Message):
    # Если сообщение не из нужного канала – можно не обрабатывать
    if message.chat.id != CHANNEL_ID:
        return

    user = message.from_user
    try:
        chat_member = await bot.get_chat_member(message.chat.id, user.id)
        status = chat_member.status
    except Exception:
        status = "Неизвестно"

    user_info = (
        f"ID: {user.id}, Имя: {user.first_name}, Username: {user.username}, Статус: {status}"
    )
    print(f"[{datetime.now(ZoneInfo('Europe/Moscow'))}] Сообщение от пользователя: {user_info}")

    # Сохраняем/обновляем данные о пользователе в subscribers.json
    subscribers = load_subscribers()
    subscribers[str(user.id)] = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "status": status,
        "last_seen": datetime.now(ZoneInfo("Europe/Moscow")).isoformat()
    }
    save_subscribers(subscribers)

# Пример функции для периодической отправки отчётов (дополнительно, для примера)
async def report_scheduler():
    while True:
        now = datetime.now(ZoneInfo("Europe/Moscow"))
        # Ежедневный отчёт в 18:30 по московскому времени
        if now.hour == 18 and now.minute == 30:
            await send_daily_report()
        # Еженедельный отчёт, например, в понедельник 10:00 по московскому времени
        if now.weekday() == 0 and now.hour == 10 and now.minute == 0:
            await send_weekly_report()
        await asyncio.sleep(60)

# Пример функций отправки отчётов администраторам (отправка производится только на заранее заданные ID)
async def send_daily_report():
    report = "Ежедневный отчёт..."
    for admin_id in DAILY_ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=report)
        except Exception as e:
            print("Ошибка отправки ежедневного отчёта:", e)

async def send_weekly_report():
    report = "Еженедельный отчёт..."
    for admin_id in WEEKLY_ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=report)
        except Exception as e:
            print("Ошибка отправки еженедельного отчёта:", e)

# Функция запуска приложения aiohttp
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(send_message_periodically())
    asyncio.create_task(report_scheduler())

# Функция остановки приложения
async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8443)


