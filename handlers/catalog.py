from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from keyboards.catalog_kb import (
    get_categories_keyboard,
    get_vehicle_types_keyboard,
    get_subtypes_keyboard,
    get_sizes_keyboard
)
from keyboards.main_kb import get_main_keyboard
from database import Database


class CatalogStates(StatesGroup):
    """Состояния для каталога"""
    category = State()
    vehicle_type = State()
    subtype = State()
    size = State()


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


@router.message(F.text == "Каталог")
async def catalog_start(message: Message, state: FSMContext):
    """Обработчик начала работы с каталогом"""
    await state.set_state(CatalogStates.category)
    await message.answer(
        "Выберите категорию:",
        reply_markup=get_categories_keyboard()
    )


@router.message(CatalogStates.category)
async def process_category(message: Message, state: FSMContext):
    """Обработчик выбора категории"""
    if message.text == "Назад":
        await state.clear()
        await message.answer(
            "Выберите раздел:",
            reply_markup=get_main_keyboard()
        )
        return

    category = message.text
    if category not in ["Шины", "Диски"]:
        await message.answer("Пожалуйста, выберите категорию из предложенных")
        return

    await state.update_data(category=category)
    vehicle_types = await db.get_vehicle_types(category)
    
    if not vehicle_types:
        await message.answer(
            "В данной категории пока нет товаров",
            reply_markup=get_categories_keyboard()
        )
        return

    await state.set_state(CatalogStates.vehicle_type)
    await message.answer(
        "Выберите тип транспортного средства:",
        reply_markup=get_vehicle_types_keyboard(vehicle_types)
    )


@router.message(CatalogStates.vehicle_type)
async def process_vehicle_type(message: Message, state: FSMContext):
    """Обработчик выбора типа ТС"""
    if message.text == "Назад":
        await state.set_state(CatalogStates.category)
        await message.answer(
            "Выберите категорию:",
            reply_markup=get_categories_keyboard()
        )
        return

    data = await state.get_data()
    vehicle_type = message.text
    
    # Для шин всегда показываем размеры сразу
    if data["category"] == "Шины":
        await state.update_data(vehicle_type=vehicle_type)
        sizes = await db.get_sizes(
            data["category"],
            vehicle_type,
            None
        )
        
        if not sizes:
            await message.answer(
                "Для данного типа ТС пока нет товаров",
                reply_markup=get_vehicle_types_keyboard(
                    await db.get_vehicle_types(data["category"])
                )
            )
            return

        await state.set_state(CatalogStates.size)
        await message.answer(
            "Выберите размер:",
            reply_markup=get_sizes_keyboard(sizes)
        )
        return

    # Для других категорий (например, Диски) проверяем подтипы
    subtypes = await db.get_subtypes(data["category"], vehicle_type)
    
    await state.update_data(vehicle_type=vehicle_type)
    sizes = await db.get_sizes(
        data["category"],
        vehicle_type,
        None
    )
    
    if not sizes:
        await message.answer(
            "Для данного типа ТС пока нет товаров",
            reply_markup=get_vehicle_types_keyboard(
                await db.get_vehicle_types(data["category"])
            )
        )
        return

    if subtypes:
        # Если есть подтипы, показываем их
        await state.set_state(CatalogStates.subtype)
        await message.answer(
            "Выберите подтип:",
            reply_markup=get_subtypes_keyboard(subtypes)
        )
    else:
        # Если подтипов нет, сразу показываем размеры
        await state.set_state(CatalogStates.size)
        await message.answer(
            "Выберите размер:",
            reply_markup=get_sizes_keyboard(sizes)
        )


@router.message(CatalogStates.subtype)
async def process_subtype(message: Message, state: FSMContext):
    """Обработчик выбора подтипа"""
    if message.text == "Назад":
        data = await state.get_data()
        await state.set_state(CatalogStates.vehicle_type)
        await message.answer(
            "Выберите тип транспортного средства:",
            reply_markup=get_vehicle_types_keyboard(
                await db.get_vehicle_types(data["category"])
            )
        )
        return

    data = await state.get_data()
    subtype = message.text
    sizes = await db.get_sizes(
        data["category"],
        data["vehicle_type"],
        subtype
    )
    
    if not sizes:
        await message.answer(
            "Для данного подтипа пока нет товаров",
            reply_markup=get_subtypes_keyboard(
                await db.get_subtypes(data["category"], data["vehicle_type"])
            )
        )
        return

    await state.update_data(subtype=subtype)
    await state.set_state(CatalogStates.size)
    await message.answer(
        "Выберите размер:",
        reply_markup=get_sizes_keyboard(sizes)
    )


@router.message(CatalogStates.size)
async def process_size(message: Message, state: FSMContext):
    """Обработчик выбора размера"""
    if message.text == "Назад":
        data = await state.get_data()
        if data.get("subtype"):
            await state.set_state(CatalogStates.subtype)
            await message.answer(
                "Выберите подтип:",
                reply_markup=get_subtypes_keyboard(
                    await db.get_subtypes(data["category"], data["vehicle_type"])
                )
            )
        else:
            await state.set_state(CatalogStates.vehicle_type)
            await message.answer(
                "Выберите тип транспортного средства:",
                reply_markup=get_vehicle_types_keyboard(
                    await db.get_vehicle_types(data["category"])
                )
            )
        return

    data = await state.get_data()
    size = message.text
    product_link = await db.get_product_link(
        data["category"],
        data["vehicle_type"],
        data.get("subtype"),
        size
    )
    
    if not product_link:
        available_sizes = await db.get_sizes(
            data["category"],
            data["vehicle_type"],
            data.get("subtype")
        )
        
        if not available_sizes:
            await message.answer(
                "Извините, в данной категории пока нет товаров.\n"
                "Пожалуйста, выберите другой тип или категорию.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
            
        await message.answer(
            "Товар с таким размером не найден.\n"
            "Пожалуйста, выберите один из доступных размеров:",
            reply_markup=get_sizes_keyboard(available_sizes)
        )
        return

    await message.answer(
        f"Ссылка на товар: {product_link}\n\n"
        "Для выбора другого товара нажмите 'Назад'.",
        reply_markup=get_sizes_keyboard(
            await db.get_sizes(
                data["category"],
                data["vehicle_type"],
                data.get("subtype")
            )
        )
    ) 