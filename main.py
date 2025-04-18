import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.contacts import router as contacts_router
from handlers.catalog import router as catalog_router
from keyboards.main_kb import get_main_keyboard
from database import Database
from utils.logger import logger, setup_logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключение роутеров
dp.include_router(contacts_router)
dp.include_router(catalog_router)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "Добро пожаловать! Я бот для поддержки клиентов.\n"
        "Выберите раздел:",
        reply_markup=get_main_keyboard()
    )

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "Я бот для поддержки клиентов.\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n\n"
        "Выберите раздел:",
        reply_markup=get_main_keyboard()
    )

async def shutdown(dispatcher: dp):
    logger.info("Начало процесса выключения бота...")
    await dispatcher.storage.close()
    await dispatcher.bot.session.close()
    logger.info("Бот успешно выключен")

async def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    setup_logger()
    logger.info("Запуск бота...")
    
    # Инициализация базы данных
    db = Database()
    await db.init_db()
    
    try:
        # Запуск бота
        logger.info("Бот запущен и готов к работе")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Получен сигнал на выключение бота")
        await shutdown(dp)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)
        await shutdown(dp)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Программа завершена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True) 