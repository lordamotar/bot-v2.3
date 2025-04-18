from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.main_kb import get_main_keyboard, get_manager_contact_keyboard
from database import Database
from config import MANAGER_ID, BOT_TOKEN
from utils.logger import logger

router = Router()
db = Database()
bot = Bot(token=BOT_TOKEN)

class ManagerStates(StatesGroup):
    """Состояния для общения с менеджером"""
    waiting_for_manager = State()
    chat_message = State()

def get_manager_keyboard(chat_id: int) -> ReplyKeyboardMarkup:
    """Создание клавиатуры для менеджера"""
    keyboard = [
        [KeyboardButton(text=f"Принять чат {chat_id}")],
        [KeyboardButton(text="Отклонить")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(F.text == "Связаться с менеджером")
async def start_manager_contact(message: Message, state: FSMContext):
    """Начало процесса связи с менеджером"""
    try:
        # Проверяем существование пользователя
        user = await db.get_user(message.from_user.id)
        if not user:
            # Создаем нового пользователя
            user_data = {
                'user_id': message.from_user.id,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'username': message.from_user.username,
                'phone_number': None,
                'birth_date': None
            }
            if not await db.save_user(user_data):
                logger.error(
                    f"Не удалось сохранить пользователя {message.from_user.id}"
                )
                await message.answer(
                    "Произошла ошибка при сохранении данных. Попробуйте позже.",
                    reply_markup=get_main_keyboard()
                )
                return

        await state.set_state(ManagerStates.waiting_for_manager)
        await message.answer(
            "Выберите способ связи с менеджером:",
            reply_markup=get_manager_contact_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при начале связи с менеджером: {e}")
        await message.answer(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )

@router.message(ManagerStates.waiting_for_manager, F.text == "Чат с менеджером")
async def start_chat(message: Message, state: FSMContext):
    """Начало чата с менеджером"""
    try:
        # Создаем новый чат
        chat_id = await db.create_chat(message.from_user.id, MANAGER_ID)
        if not chat_id:
            logger.error(
                f"Не удалось создать чат для пользователя {message.from_user.id}"
            )
            await message.answer(
                "Произошла ошибка при создании чата. Попробуйте позже.",
                reply_markup=get_manager_contact_keyboard()
            )
            return

        # Получаем информацию о пользователе
        user = await db.get_user(message.from_user.id)
        if not user:
            logger.error(f"Пользователь {message.from_user.id} не найден")
            await message.answer(
                "Произошла ошибка. Попробуйте позже.",
                reply_markup=get_manager_contact_keyboard()
            )
            return

        # Формируем текст кнопки для менеджера
        user_info = []
        if user['first_name']:
            user_info.append(user['first_name'])
        if user['last_name']:
            user_info.append(user['last_name'])
        if user['phone_number']:
            user_info.append(user['phone_number'])
        if not user_info:  # Если нет никакой информации
            user_info.append(f"ID: {user['user_id']}")

        button_text = f"Принять чат с {' '.join(user_info)}"

        # Отправляем уведомление менеджеру
        manager_message = (
            f"Новый запрос на чат!\n\n"
            f"Пользователь: {user['first_name']} {user['last_name']}\n"
            f"Username: @{user['username']}\n"
            f"ID: {user['user_id']}\n"
            f"Телефон: {user['phone_number'] or 'не указан'}\n"
            f"Дата рождения: {user['birth_date'] or 'не указана'}\n\n"
            f"ID чата: {chat_id}"
        )
        await bot.send_message(
            MANAGER_ID,
            manager_message,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=button_text)]],
                resize_keyboard=True
            )
        )

        await state.set_state(ManagerStates.chat_message)
        await message.answer(
            "Ваш запрос на чат отправлен менеджеру. Ожидайте подтверждения.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Ошибка при начале чата: {e}")
        await message.answer(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=get_manager_contact_keyboard()
        )

@router.message(F.text.startswith("Принять чат с "))
async def accept_chat(message: Message, state: FSMContext):
    """Обработка принятия чата менеджером"""
    if message.from_user.id != MANAGER_ID:
        return

    try:
        # Получаем последний ожидающий чат
        pending_chats = await db.get_pending_chats()
        if not pending_chats:
            await message.answer("Нет ожидающих чатов")
            return

        chat = pending_chats[0]  # Берем первый ожидающий чат
        chat_id = chat['id']

        # Обновляем статус чата
        if not await db.update_chat_status(chat_id, "active"):
            await message.answer("Ошибка при обновлении статуса чата")
            return

        # Создаем клавиатуру для клиента
        client_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Завершить чат")],
                [KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        )

        # Уведомление пользователю
        await bot.send_message(
            chat['user_id'],
            "Менеджер принял ваш запрос на чат. Теперь вы можете общаться.",
            reply_markup=client_keyboard
        )

        # Создаем клавиатуру для менеджера
        manager_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Завершить чат")]],
            resize_keyboard=True
        )

        await message.answer(
            f"Чат с пользователем {chat['user_id']} начат.",
            reply_markup=manager_keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка при принятии чата: {e}")
        await message.answer("Ошибка при обработке запроса")

@router.message(F.text == "Завершить чат")
async def end_chat(message: Message):
    """Завершение чата"""
    try:
        # Получаем активный чат
        if message.from_user.id == MANAGER_ID:
            chat = await db.get_active_chat_by_manager(MANAGER_ID)
        else:
            chat = await db.get_chat(message.from_user.id)
            
        if not chat:
            await message.answer("У вас нет активных чатов")
            return

        # Обновляем статус чата
        if not await db.update_chat_status(chat['id'], "closed"):
            await message.answer("Ошибка при завершении чата")
            return

        # Уведомление другому участнику чата
        if message.from_user.id == MANAGER_ID:
            await bot.send_message(
                chat['user_id'],
                "Чат завершен менеджером.",
                reply_markup=get_main_keyboard()
            )
            await message.answer(
                "Чат завершен",
                reply_markup=get_main_keyboard()
            )
        else:
            # Уведомляем менеджера и возвращаем на главную страницу
            await bot.send_message(
                MANAGER_ID,
                "Пользователь завершил чат.",
                reply_markup=get_main_keyboard()
            )
            await message.answer(
                "Чат завершен",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка при завершении чата: {e}")
        await message.answer("Ошибка при обработке запроса")

@router.message(F.text == "Отклонить")
async def reject_chat(message: Message, state: FSMContext):
    """Обработка отклонения чата менеджером"""
    if message.from_user.id != MANAGER_ID:
        return

    try:
        # Получаем последний ожидающий чат
        pending_chats = await db.get_pending_chats()
        if not pending_chats:
            await message.answer("Нет ожидающих чатов")
            return

        chat = pending_chats[0]  # Берем первый ожидающий чат
        chat_id = chat['id']
        user_id = chat['user_id']

        # Обновляем статус чата
        if not await db.update_chat_status(chat_id, "rejected"):
            await message.answer("Ошибка при обновлении статуса чата")
            return

        # Уведомление пользователю
        await bot.send_message(
            user_id,
            "Менеджер отклонил ваш запрос на чат.",
            reply_markup=get_main_keyboard()
        )

        await message.answer(
            "Чат отклонен",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Ошибка при отклонении чата: {e}")
        await message.answer("Ошибка при обработке запроса")

@router.message(ManagerStates.chat_message)
async def handle_chat_message(message: Message, state: FSMContext):
    """Обработка сообщений в чате с менеджером"""
    try:
        # Получаем информацию о чате
        chat = await db.get_chat(message.from_user.id)
        if not chat:
            await message.answer(
                "Чат не найден. Пожалуйста, начните новый чат.",
                reply_markup=get_manager_contact_keyboard()
            )
            await state.clear()
            return

        # Если чат не активен
        if chat['status'] != 'active':
            await message.answer(
                "Чат не активен. Пожалуйста, дождитесь ответа менеджера.",
                reply_markup=get_manager_contact_keyboard()
            )
            return

        # Создаем клавиатуру для клиента
        client_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Завершить чат")],
                [KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        )

        # Отправляем сообщение менеджеру
        manager_id = chat['manager_id']
        await bot.send_message(manager_id, message.text)
        
        # Сохраняем сообщение в истории
        await db.save_message(chat['id'], message.from_user.id, message.text)
        
        # Обновляем клавиатуру клиента
        await message.answer(
            "Сообщение отправлено",
            reply_markup=client_keyboard
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения в чате: {e}")
        await message.answer(
            "Произошла ошибка при отправке сообщения. Попробуйте позже.",
            reply_markup=get_manager_contact_keyboard()
        )
        await state.clear()

@router.message(F.from_user.id == MANAGER_ID)
async def handle_manager_message(message: Message):
    """Обработка сообщений от менеджера"""
    try:
        # Получаем активный чат для менеджера
        chat = await db.get_active_chat_by_manager(MANAGER_ID)
        if not chat:
            await message.answer("У вас нет активных чатов")
            return

        # Создаем клавиатуру для клиента
        client_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Завершить чат")],
                [KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        )

        # Отправляем сообщение пользователю
        await bot.send_message(
            chat['user_id'],
            message.text,
            reply_markup=client_keyboard
        )
        
        # Сохраняем сообщение в истории
        await db.save_message(chat['id'], message.from_user.id, message.text)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения менеджера: {e}")
        await message.answer("Ошибка при отправке сообщения") 