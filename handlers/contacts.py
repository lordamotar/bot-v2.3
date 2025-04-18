from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from keyboards.contacts_kb import (
    get_contact_types_keyboard,
    get_cities_keyboard,
    get_locations_keyboard
)
from keyboards.main_kb import get_main_keyboard
from database import Database


class ContactsStates(StatesGroup):
    """Состояния для контактов"""
    contact_type = State()
    city = State()
    location = State()


router = Router()
db = Database()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "Добро пожаловать! Я бот для поддержки клиентов.\n"
        "Выберите раздел:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "Контакты")
async def contacts_start(message: Message, state: FSMContext):
    """Обработчик начала работы с контактами"""
    await state.set_state(ContactsStates.contact_type)
    await message.answer(
        "Выберите тип контакта:",
        reply_markup=get_contact_types_keyboard()
    )


@router.message(ContactsStates.contact_type)
async def process_contact_type(message: Message, state: FSMContext):
    """Обработчик выбора типа контакта"""
    if message.text == "Назад":
        await state.clear()
        await message.answer(
            "Выберите раздел:",
            reply_markup=get_main_keyboard()
        )
        return

    contact_type = message.text
    if contact_type not in ["Магазин", "Сервис"]:
        await message.answer(
            "Пожалуйста, выберите тип контакта из предложенных"
        )
        return

    await state.update_data(contact_type=contact_type)
    cities = await db.get_all_cities()
    
    if not cities:
        await message.answer(
            "Список городов пуст",
            reply_markup=get_contact_types_keyboard()
        )
        return

    await state.set_state(ContactsStates.city)
    await message.answer(
        "Выберите город:",
        reply_markup=get_cities_keyboard(cities)
    )


@router.message(ContactsStates.city)
async def process_city(message: Message, state: FSMContext):
    """Обработчик выбора города"""
    if message.text == "Назад":
        await state.set_state(ContactsStates.contact_type)
        await message.answer(
            "Выберите тип контакта:",
            reply_markup=get_contact_types_keyboard()
        )
        return

    data = await state.get_data()
    city = message.text
    locations = await db.get_locations_by_city(city, data["contact_type"])
    
    if not locations:
        await message.answer(
            "В данном городе нет точек выбранного типа",
            reply_markup=get_cities_keyboard(await db.get_all_cities())
        )
        return

    await state.update_data(city=city)
    await state.set_state(ContactsStates.location)
    await message.answer(
        "Выберите адрес:",
        reply_markup=get_locations_keyboard(locations)
    )


@router.message(ContactsStates.location)
async def process_location(message: Message, state: FSMContext):
    """Обработчик выбора адреса"""
    if message.text == "Назад":
        data = await state.get_data()
        await state.set_state(ContactsStates.city)
        await message.answer(
            "Выберите город:",
            reply_markup=get_cities_keyboard(await db.get_all_cities())
        )
        return

    data = await state.get_data()
    location = message.text
    location_info = await db.get_location_info(data["city"], location)
    
    if not location_info:
        await message.answer(
            "Информация о торговой точке не найдена",
            reply_markup=get_locations_keyboard(
                await db.get_locations_by_city(data["city"], data["contact_type"])
            )
        )
        return

    response = f"📍 {location_info['address']}\n\n"
    
    if data["contact_type"] == "Магазин":
        if location_info.get("phone_store"):
            response += f"📞 Телефон: {location_info['phone_store']}\n"
        if location_info.get("work_schedule_weekdays"):
            response += f"🕒 График работы (будни): {location_info['work_schedule_weekdays']}\n"
        if location_info.get("work_schedule_weekend"):
            response += f"🕒 График работы (выходные): {location_info['work_schedule_weekend']}\n"
    else:  # Сервис
        if location_info.get("phone_service"):
            response += f"📞 Телефон: {location_info['phone_service']}\n"
        if location_info.get("service_schedule_weekdays"):
            response += f"🕒 График работы сервиса (будни): {location_info['service_schedule_weekdays']}\n"
        if location_info.get("service_schedule_weekend"):
            response += f"🕒 График работы сервиса (выходные): {location_info['service_schedule_weekend']}\n"
        if location_info.get("service_manager_name"):
            response += f"👨‍💼 Менеджер сервиса: {location_info['service_manager_name']}\n"

    if location_info.get("maps_2gis_link"):
        response += f"\n🗺 2ГИС: {location_info['maps_2gis_link']}\n"
    if location_info.get("google_maps_link"):
        response += f"🗺 Google Maps: {location_info['google_maps_link']}\n"

    await message.answer(
        response,
        reply_markup=get_locations_keyboard(
            await db.get_locations_by_city(data["city"], data["contact_type"])
        )
    ) 