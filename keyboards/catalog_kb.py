from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_categories_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора категории"""
    keyboard = [
        [KeyboardButton(text="Шины"), KeyboardButton(text="Диски")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_vehicle_types_keyboard(types: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа ТС"""
    keyboard = []
    row = []
    for i, vehicle_type in enumerate(types):
        row.append(KeyboardButton(text=vehicle_type))
        if len(row) == 2 or i == len(types) - 1:
            keyboard.append(row)
            row = []
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_subtypes_keyboard(subtypes: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура выбора подтипа"""
    keyboard = []
    row = []
    for i, subtype in enumerate(subtypes):
        row.append(KeyboardButton(text=subtype))
        if len(row) == 2 or i == len(subtypes) - 1:
            keyboard.append(row)
            row = []
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_sizes_keyboard(sizes: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура выбора размера"""
    keyboard = []
    row = []
    for i, size in enumerate(sizes):
        row.append(KeyboardButton(text=size))
        if len(row) == 3 or i == len(sizes) - 1:
            keyboard.append(row)
            row = []
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True) 