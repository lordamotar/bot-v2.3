from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает основную клавиатуру с кнопками Каталог и Контакты"""
    keyboard = [
        [KeyboardButton(text="Каталог"), KeyboardButton(text="Контакты")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True) 