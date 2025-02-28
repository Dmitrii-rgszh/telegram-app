import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import sqlite3  # Или любая другая СУБД

# Конфигурация
TOKEN = "7699973329:AAF1h3N8FuL0y8yhzu2zMU7bV28ZEdb0kJs"
CHANNEL_ID = -1002367711236  # числовой chat_id канала

# Списки администраторов для отчётов (ID администраторов группы)
DAILY_ADMIN_IDS = [168554128, 5607311019]
WEEKLY_ADMIN_IDS = [168554128, 5607311019]

WEBHOOK_HOST = "https://telegram-app-vhli.onrender.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализируем БД (пример с SQLite)
conn = sqlite3.connect("stats.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    timestamp DATETIME,
    value INTEGER,
    extra TEXT
)''')
conn.commit()


# Функция для сохранения событий
def log_event(event_type: str, value: int = 1, extra: str = ""):
    cursor.execute("INSERT INTO stats (event_type, timestamp, value, extra) VALUES (?, ?, ?, ?)",
                   (event_type, datetime.now(), value, extra))
    conn.commit()


# Обработка обновлений статуса участников с фильтром, требующим member_status_changed=True
@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=True))
async def on_chat_member_update(update: types.ChatMemberUpdated):
    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    if old_status not in ("member", "administrator") and new_status == "member":
        log_event("new_subscriber")
    elif old_status == "member" and new_status in ("left", "kicked"):
        log_event("unsubscriber")


# Обработка публикации нового поста в канале
@dp.channel_post()
async def on_channel_post(message: types.Message):
    log_event("new_post")
    if message.view_count:
        log_event("post_views", value=message.view_count)
    log_event("post_time", extra=str(message.date.time()))


# Функция формирования ежедневного отчёта
async def send_daily_report():
    since = datetime.now() - timedelta(days=1)
    cursor.execute("SELECT event_type, SUM(value) FROM stats WHERE timestamp >= ? GROUP BY event_type", (since,))
    results = cursor.fetchall()

    report = "Ежедневная статистика:\n"
    stats = {row[0]: row[1] for row in results}
    report += f"Новых подписчиков: {stats.get('new_subscriber', 0)}\n"
    report += f"Отписок: {stats.get('unsubscriber', 0)}\n"
    report += f"Новых постов: {stats.get('new_post', 0)}\n"
    total_views = stats.get("post_views", 0)
    count_posts = stats.get("new_post", 0)
    avg_views = total_views / count_posts if count_posts else 0
    report += f"Среднее количество просмотров на пост: {avg_views:.2f}\n"

    for admin_id in DAILY_ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=report)
        except Exception as e:
            print("Ошибка отправки отчёта администратору:", e)


# Функция формирования еженедельного отчёта
async def send_weekly_report():
    since = datetime.now() - timedelta(weeks=1)
    cursor.execute("SELECT event_type, SUM(value) FROM stats WHERE timestamp >= ? GROUP BY event_type", (since,))
    results = cursor.fetchall()

    report = "Еженедельная статистика:\n"
    stats = {row[0]: row[1] for row in results}
    report += f"Новых подписчиков: {stats.get('new_subscriber', 0)}\n"
    report += f"Отписок: {stats.get('unsubscriber', 0)}\n"
    report += f"Новых постов: {stats.get('new_post', 0)}\n"
    total_views = stats.get("post_views", 0)
    count_posts = stats.get("new_post", 0)
    avg_views = total_views / count_posts if count_posts else 0
    report += f"Среднее количество просмотров на пост: {avg_views:.2f}\n"

    for admin_id in WEEKLY_ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=report)
        except Exception as e:
            print("Ошибка отправки отчёта администратору:", e)


# Планировщик для отправки отчётов
async def report_scheduler():
    while True:
        now = datetime.now(ZoneInfo("Europe/Moscow"))
        if now.hour == 18 and now.minute == 0:
            await send_daily_report()
        if now.weekday() == 0 and now.hour == 10 and now.minute == 0:
            await send_weekly_report()
        await asyncio.sleep(60)


# Функция запуска приложения
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(report_scheduler())


# Функция остановки приложения
async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()
    conn.close()


app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8443)


