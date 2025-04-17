import asyncio
from bot import dp, bot
from handlers.contacts import router
from utils.logger import logger, setup_logger


async def shutdown(dispatcher: dp):
    logger.info("Начало процесса выключения бота...")
    await dispatcher.storage.close()
    await dispatcher.bot.session.close()
    logger.info("Бот успешно выключен")


async def main():
    # Настройка логирования
    setup_logger()
    logger.info("Запуск бота...")
    
    # Регистрация роутеров
    dp.include_router(router)
    logger.info("Роутеры успешно зарегистрированы")
    
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True) 