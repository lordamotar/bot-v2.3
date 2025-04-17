from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.locations import get_cities, get_locations

# Главное меню
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Каталог")],
            [KeyboardButton(text="Контакты")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Клавиатура с городами
def get_cities_keyboard():
    cities = get_cities()
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=city)] for city in cities] + [[KeyboardButton(text="Назад")]],
        resize_keyboard=True
    )
    return keyboard

# Клавиатура с торговыми точками
def get_locations_keyboard(city: str):
    locations = get_locations(city)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=location)] for location in locations] + [[KeyboardButton(text="Назад")]],
        resize_keyboard=True
    )
    return keyboard 