import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import contacts
from database import Database
from utils.logger import logger, setup_logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрация роутеров
dp.include_router(contacts.router)

async def shutdown(dispatcher: dp):
    logger.info("Начало процесса выключения бота...")
    await dispatcher.storage.close()
    await dispatcher.bot.session.close()
    logger.info("Бот успешно выключен")


async def main():
    # Настройка логирования
    setup_logger()
    logger.info("Запуск бота...")
    
    # Инициализация базы данных
    db = Database()
    await db.init_db()
    
    try:
        # Запуск бота
        logger.info("Бот запущен и готов к работе")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
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
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True) 