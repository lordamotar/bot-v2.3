from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает основную клавиатуру"""
    keyboard = [
        [KeyboardButton(text="Каталог"), KeyboardButton(text="Контакты")],
        [KeyboardButton(text="Связаться с менеджером")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_manager_contact_keyboard(has_phone: bool = False) -> ReplyKeyboardMarkup:
    """Создает клавиатуру для связи с менеджером"""
    keyboard = []
    
    if not has_phone:
        keyboard.append([KeyboardButton(text="Поделиться профилем", request_contact=True)])
    
    keyboard.extend([
        [KeyboardButton(text="Хочу, чтобы мне перезвонили")],
        [KeyboardButton(text="Чат с менеджером")],
        [KeyboardButton(text="Назад")]
    ])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_chat_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для чата с менеджером"""
    keyboard = [
        [KeyboardButton(text="Завершить чат")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True) 