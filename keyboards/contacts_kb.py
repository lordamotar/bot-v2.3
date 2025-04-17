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
def get_cities_keyboard(cities: list) -> ReplyKeyboardMarkup:
    """Создает клавиатуру со списком городов в два ряда"""
    # Разбиваем список городов на пары
    city_rows = []
    for i in range(0, len(cities), 2):
        row = [KeyboardButton(text=city) for city in cities[i:i+2]]
        city_rows.append(row)
    
    # Добавляем кнопку "Назад" в отдельный ряд
    city_rows.append([KeyboardButton(text="Назад")])
    
    return ReplyKeyboardMarkup(keyboard=city_rows, resize_keyboard=True)

# Клавиатура с торговыми точками
def get_locations_keyboard(locations: list) -> ReplyKeyboardMarkup:
    """Создает клавиатуру со списком адресов в два ряда"""
    # Разбиваем список адресов на пары
    location_rows = []
    for i in range(0, len(locations), 2):
        row = [KeyboardButton(text=location) for location in locations[i:i+2]]
        location_rows.append(row)
    
    # Добавляем кнопку "Назад" в отдельный ряд
    location_rows.append([KeyboardButton(text="Назад")])
    
    return ReplyKeyboardMarkup(keyboard=location_rows, resize_keyboard=True)

def get_contact_type_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для выбора типа контакта"""
    keyboard = [
        [KeyboardButton(text="Магазин")],
        [KeyboardButton(text="Сервис")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True) 