import asyncio
from bot import dp, bot
from handlers.contacts import router


async def shutdown(dispatcher: dp):
    await dispatcher.storage.close()
    await dispatcher.bot.session.close()


async def main():
    # Регистрация роутеров
    dp.include_router(router)
    
    try:
        # Запуск бота
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключается...")
        await shutdown(dp)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        await shutdown(dp)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот успешно выключен") 