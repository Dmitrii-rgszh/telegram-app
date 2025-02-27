import asyncio
from aiogram import Bot, Dispatcher

TOKEN = "7699973329:AAF1h3N8FuL0y8yhzu2zMU7bV28ZEdb0kJs"  # замените на ваш токен
CHANNEL_ID = "-1002480574817"  # замените на @username канала или числовой chat_id

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def send_message_periodically():
    while True:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text="Привет")
            print("Сообщение отправлено!")
        except Exception as e:
            print("Ошибка при отправке сообщения:", e)
        await asyncio.sleep(60)

async def main():
    # Запускаем периодическую задачу
    asyncio.create_task(send_message_periodically())
    # Запускаем polling
    await dp.start_polling(bot)
    print('Бот запущен!')
if __name__ == "__main__":
    asyncio.run(main())