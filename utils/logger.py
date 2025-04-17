import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


# Создаем директорию для логов, если её нет
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Настройка формата логов
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Настройка обработчика для файла
file_handler = RotatingFileHandler(
    filename=log_dir / 'bot.log',
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Настройка обработчика для консоли
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Создаем логгер
logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def setup_logger():
    """Настройка логгера для всего приложения"""
    # Логгер для aiogram
    aiogram_logger = logging.getLogger('aiogram')
    aiogram_logger.setLevel(logging.WARNING)
    aiogram_logger.addHandler(file_handler)
    aiogram_logger.addHandler(console_handler)

    # Логгер для asyncio
    asyncio_logger = logging.getLogger('asyncio')
    asyncio_logger.setLevel(logging.WARNING)
    asyncio_logger.addHandler(file_handler)
    asyncio_logger.addHandler(console_handler)

    logger.info("Логгер успешно настроен") 