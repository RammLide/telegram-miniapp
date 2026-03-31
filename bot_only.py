import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Импортируем все обработчики из main.py
from main import dp, bot, init_db

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска бота БЕЗ веб-сервера"""
    await init_db()
    logger.info("🤖 Бот запущен и готов к работе!")
    logger.info("⚠️ Веб-сервер НЕ запущен (только бот)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
