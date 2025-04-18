from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню
def get_main_menu() -> ReplyKeyboardMarkup:
    """Создает главное меню бота"""
    keyboard = [
        [KeyboardButton(text="Каталог")],
        [KeyboardButton(text="Контакты")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Клавиатура с городами
def get_cities_keyboard(cities: list[str]) -> ReplyKeyboardMarkup:
    """Создает клавиатуру выбора города"""
    keyboard = []
    row = []
    for i, city in enumerate(cities):
        row.append(KeyboardButton(text=city))
        if len(row) == 2 or i == len(cities) - 1:
            keyboard.append(row)
            row = []
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Клавиатура с торговыми точками
def get_locations_keyboard(locations: list[str]) -> ReplyKeyboardMarkup:
    """Создает клавиатуру выбора адреса"""
    keyboard = [[KeyboardButton(text=location)] for location in locations]
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_contact_types_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру выбора типа контакта"""
    keyboard = [
        [KeyboardButton(text="Магазин"), KeyboardButton(text="Сервис")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True) 