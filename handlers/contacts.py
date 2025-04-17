from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.contacts_kb import get_main_menu, get_cities_keyboard, get_locations_keyboard
from data.locations import get_location_info, get_cities

router = Router()

class ContactStates(StatesGroup):
    select_city = State()
    select_location = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать! Выберите раздел:",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "Контакты")
async def contacts_menu(message: Message, state: FSMContext):
    await state.set_state(ContactStates.select_city)
    await message.answer(
        "Выберите город:",
        reply_markup=get_cities_keyboard()
    )

@router.message(ContactStates.select_city, F.text == "Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите раздел:",
        reply_markup=get_main_menu()
    )

@router.message(ContactStates.select_city)
async def select_city(message: Message, state: FSMContext):
    if message.text not in get_cities():
        await message.answer("Пожалуйста, выберите город из списка.")
        return
        
    city = message.text
    await state.update_data(city=city)
    await state.set_state(ContactStates.select_location)
    await message.answer(
        f"Выберите торговую точку в городе {city}:",
        reply_markup=get_locations_keyboard(city)
    )

@router.message(ContactStates.select_location, F.text == "Назад")
async def back_to_cities(message: Message, state: FSMContext):
    await state.set_state(ContactStates.select_city)
    await message.answer(
        "Выберите город:",
        reply_markup=get_cities_keyboard()
    )

@router.message(ContactStates.select_location)
async def show_location_info(message: Message, state: FSMContext):
    data = await state.get_data()
    city = data["city"]
    location = message.text
    
    location_info = get_location_info(city, location)
    if not location_info:
        await message.answer("Торговая точка не найдена. Пожалуйста, выберите из списка.")
        return
    
    # Создаем инлайн-кнопку для карты
    map_button = InlineKeyboardButton(
        text="Открыть в Яндекс Картах",
        url=location_info["map_link"]
    )
    map_keyboard = InlineKeyboardMarkup(inline_keyboard=[[map_button]])
    
    # Формируем сообщение с информацией
    info_text = (
        f"🏪 {location}\n\n"
        f"📍 Адрес: {location_info['address']}\n"
        f"📞 Телефон: {location_info['phone']}\n"
        f"🔧 Сервис: {location_info['service_phone']}\n\n"
        f"🕒 График работы:\n"
        f"Будни: {location_info['workdays_hours']}\n"
        f"Выходные: {location_info['weekend_hours']}\n\n"
        f"🛠️ График работы сервиса:\n"
        f"Будни: {location_info['service_workdays_hours']}\n"
        f"Выходные: {location_info['service_weekend_hours']}\n\n"
        f"👨‍💼 Менеджер сервиса: {location_info['service_manager']}"
    )
    
    await message.answer(
        info_text,
        reply_markup=map_keyboard
    ) 