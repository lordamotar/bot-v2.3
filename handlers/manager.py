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
    rating_chat = State()  # Новое состояние для оценки

def get_manager_keyboard(chat_id: int) -> ReplyKeyboardMarkup:
    """Создание клавиатуры для менеджера"""
    keyboard = [
        [KeyboardButton(text=f"Принять чат {chat_id}")],
        [KeyboardButton(text="Отклонить")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_rating_keyboard() -> ReplyKeyboardMarkup:
    """Создание клавиатуры для оценки"""
    keyboard = [
        [KeyboardButton(text="⭐️"), KeyboardButton(text="⭐️⭐️")],
        [KeyboardButton(text="⭐️⭐️⭐️"), KeyboardButton(text="⭐️⭐️⭐️⭐️")],
        [KeyboardButton(text="⭐️⭐️⭐️⭐️⭐️")]
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

        # Проверяем наличие активного чата
        active_chat = await db.get_chat(message.from_user.id)
        if active_chat:
            if active_chat['status'] == 'active':
                # Если есть активный чат, продолжаем общение
                await state.set_state(ManagerStates.chat_message)
                await message.answer(
                    "У вас уже есть активный чат с менеджером. Продолжайте общение.",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(text="Завершить чат")],
                            [KeyboardButton(text="Назад")]
                        ],
                        resize_keyboard=True
                    )
                )
                # Логируем действие
                await db.save_user_log(
                    message.from_user.id,
                    "continue_chat",
                    "Продолжение активного чата с менеджером"
                )
                return
            elif active_chat['status'] == 'pending':
                # Если есть ожидающий чат, отправляем новый запрос
                await start_chat(message, state)
                return

        await state.set_state(ManagerStates.waiting_for_manager)
        await message.answer(
            "Выберите способ связи с менеджером:",
            reply_markup=get_manager_contact_keyboard()
        )
        # Логируем действие
        await db.save_user_log(
            message.from_user.id,
            "start_manager_contact",
            "Начало процесса связи с менеджером"
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
        # Логируем действие
        await db.save_user_log(
            message.from_user.id,
            "start_chat",
            f"Создан новый чат с ID: {chat_id}"
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
async def end_chat(message: Message, state: FSMContext):
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
            # Логируем действие менеджера
            await db.save_user_log(
                MANAGER_ID,
                "end_chat_manager",
                f"Завершен чат с пользователем {chat['user_id']}"
            )
        else:
            # Уведомляем менеджера
            await bot.send_message(
                MANAGER_ID,
                "Пользователь завершил чат.",
                reply_markup=get_main_keyboard()
            )
            
            # Сохраняем ID чата в состоянии для оценки
            await state.set_state(ManagerStates.rating_chat)
            await state.update_data(chat_id=chat['id'])
            
            # Запрашиваем оценку у пользователя
            await message.answer(
                "Пожалуйста, оцените качество обслуживания:",
                reply_markup=get_rating_keyboard()
            )
            # Логируем действие пользователя
            await db.save_user_log(
                message.from_user.id,
                "end_chat_user",
                "Завершен чат с менеджером"
            )
    except Exception as e:
        logger.error(f"Ошибка при завершении чата: {e}")
        await message.answer("Ошибка при обработке запроса")

@router.message(ManagerStates.rating_chat)
async def handle_rating(message: Message, state: FSMContext):
    """Обработка оценки чата"""
    try:
        # Получаем количество звезд из сообщения
        rating = len(message.text)
        
        # Получаем данные из состояния
        data = await state.get_data()
        chat_id = data.get('chat_id')
        
        if not chat_id:
            await message.answer(
                "Произошла ошибка. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
            
        # Сохраняем оценку в базе данных
        if await db.save_chat_rating(chat_id, rating):
            await message.answer(
                f"Спасибо за вашу оценку! ({message.text})",
                reply_markup=get_main_keyboard()
            )
            # Логируем действие
            await db.save_user_log(
                message.from_user.id,
                "rate_chat",
                f"Оценка чата: {rating} звезд"
            )
        else:
            await message.answer(
                "Произошла ошибка при сохранении оценки. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
        
        # Очищаем состояние
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка при обработке оценки: {e}")
        await message.answer(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

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
        
        # Логируем действие
        await db.save_user_log(
            message.from_user.id,
            "send_message",
            f"Отправлено сообщение в чат {chat['id']}: {message.text[:50]}..."
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