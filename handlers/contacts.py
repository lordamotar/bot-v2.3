from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.contacts_kb import (
    get_main_menu, get_contact_type_keyboard, get_cities_keyboard,
    get_locations_keyboard
)
from database import Database
from utils.logger import logger

router = Router()
db = Database()

class ContactStates(StatesGroup):
    select_type = State()
    select_city = State()
    select_location = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await message.answer(
        "Добро пожаловать! Выберите раздел:",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "Контакты")
async def contacts_menu(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} открыл раздел 'Контакты'")
    await state.set_state(ContactStates.select_type)
    await message.answer(
        "Выберите тип контакта:",
        reply_markup=get_contact_type_keyboard()
    )

@router.message(ContactStates.select_type, F.text == "Назад")
async def back_to_main(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню")
    await state.clear()
    await message.answer(
        "Выберите раздел:",
        reply_markup=get_main_menu()
    )

@router.message(ContactStates.select_type)
async def select_contact_type(message: Message, state: FSMContext):
    if message.text not in ["Магазин", "Сервис"]:
        logger.warning(
            f"Пользователь {message.from_user.id} ввел неверный тип: "
            f"{message.text}"
        )
        await message.answer("Пожалуйста, выберите тип из списка.")
        return
        
    contact_type = message.text
    logger.info(
        f"Пользователь {message.from_user.id} выбрал тип: {contact_type}"
    )
    await state.update_data(contact_type=contact_type)
    await state.set_state(ContactStates.select_city)
    
    cities = await db.get_all_cities()
    if not cities:
        await message.answer("Извините, в данный момент нет доступных городов.")
        return
        
    await message.answer(
        "Выберите город:",
        reply_markup=get_cities_keyboard(cities)
    )

@router.message(ContactStates.select_city, F.text == "Назад")
async def back_to_types(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} вернулся к выбору типа")
    await state.set_state(ContactStates.select_type)
    await message.answer(
        "Выберите тип контакта:",
        reply_markup=get_contact_type_keyboard()
    )

@router.message(ContactStates.select_city)
async def select_city(message: Message, state: FSMContext):
    cities = await db.get_all_cities()
    if message.text not in cities:
        logger.warning(
            f"Пользователь {message.from_user.id} ввел несуществующий город: "
            f"{message.text}"
        )
        await message.answer("Пожалуйста, выберите город из списка.")
        return
        
    city = message.text
    logger.info(f"Пользователь {message.from_user.id} выбрал город: {city}")
    await state.update_data(city=city)
    
    data = await state.get_data()
    contact_type = data["contact_type"]
    locations = await db.get_locations_by_city(city, contact_type)
    
    if not locations:
        await message.answer(
            f"В городе {city} нет доступных {contact_type.lower()}ов."
        )
        return
        
    await state.set_state(ContactStates.select_location)
    await message.answer(
        f"Выберите адрес в городе {city}:",
        reply_markup=get_locations_keyboard(locations)
    )

@router.message(ContactStates.select_location, F.text == "Назад")
async def back_to_cities(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} вернулся к выбору города")
    await state.set_state(ContactStates.select_city)
    
    cities = await db.get_all_cities()
    await message.answer(
        "Выберите город:",
        reply_markup=get_cities_keyboard(cities)
    )

@router.message(ContactStates.select_location)
async def show_location_info(message: Message, state: FSMContext):
    data = await state.get_data()
    city = data["city"]
    contact_type = data["contact_type"]
    address = message.text
    
    location_info = await db.get_location_info(city, address)
    if not location_info:
        logger.warning(
            f"Пользователь {message.from_user.id} выбрал несуществующий адрес: "
            f"{address} в городе {city}"
        )
        await message.answer("Адрес не найден. Пожалуйста, выберите из списка.")
        return
    
    logger.info(
        f"Пользователь {message.from_user.id} запросил информацию об адресе: "
        f"{address} в городе {city}"
    )
    
    # Создаем инлайн-кнопку для 2GIS
    map_buttons = []
    if location_info.get('maps_2gis_link'):
        map_buttons.append(InlineKeyboardButton(
            text="Открыть в 2GIS",
            url=location_info['maps_2gis_link']
        ))
    
    map_keyboard = InlineKeyboardMarkup(inline_keyboard=[map_buttons])
    
    # Формируем сообщение с информацией в зависимости от типа контакта
    if contact_type == "Магазин":
        info_text = (
            f"🏪 Магазин\n"
            f"🏙️ Город: {location_info['city']}\n"
            f"📍 Адрес: {location_info['address']}\n"
            f"📞 Телефон: {location_info['phone_store']}\n\n"
            f"🕒 График работы:\n"
            f"Будни: {location_info['work_schedule_weekdays']}\n"
            f"Выходные: {location_info['work_schedule_weekend']}"
        )
    else:  # Сервис
        info_text = (
            f"🔧 Сервис\n"
            f"🏙️ Город: {location_info['city']}\n"
            f"📍 Адрес: {location_info['address']}\n"
            f"📞 Телефон: {location_info['phone_service']}\n\n"
            f"🕒 График работы:\n"
            f"Будни: {location_info['service_schedule_weekdays']}\n"
            f"Выходные: {location_info['service_schedule_weekend']}\n\n"
            f"👨‍💼 Менеджер: {location_info['service_manager_name']}"
        )
    
    await message.answer(
        info_text,
        reply_markup=map_keyboard
    ) 