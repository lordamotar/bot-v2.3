import aiosqlite
from typing import List, Dict, Optional
from utils.logger import logger
import os


class Database:
    def __init__(self, db_path: str = "service_points.db"):
        self.db_path = db_path

    async def connect(self):
        """Установка соединения с базой данных"""
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            await self.connection.execute("PRAGMA foreign_keys = ON")
            await self.connection.commit()
            logger.info("Успешное подключение к базе данных")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise

    async def disconnect(self):
        """Закрытие соединения с базой данных"""
        if hasattr(self, 'connection'):
            await self.connection.close()
            logger.info("Соединение с базой данных закрыто")

    async def init_db(self):
        """Инициализация базы данных"""
        try:
            await self.connect()
            
            # Проверяем существование старой таблицы
            cursor = await self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND "
                "name='service_points'"
            )
            table_exists = await cursor.fetchone()
            await cursor.close()
            
            if table_exists:
                # Создаем временную таблицу с новой структурой
                await self.connection.execute("""
                    CREATE TABLE IF NOT EXISTS service_points_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        city TEXT NOT NULL,
                        address TEXT NOT NULL,
                        phone_store TEXT,
                        phone_service TEXT,
                        work_schedule_weekdays TEXT,
                        work_schedule_weekend TEXT,
                        service_schedule_weekdays TEXT,
                        service_schedule_weekend TEXT,
                        service_manager_name TEXT,
                        maps_2gis_link TEXT,
                        google_maps_link TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(city, address)
                    )
                """)
                
                # Переносим данные из старой таблицы в новую
                await self.connection.execute("""
                    INSERT INTO service_points_new (
                        id, city, address, phone_store, phone_service,
                        work_schedule_weekdays, work_schedule_weekend,
                        service_schedule_weekdays, service_schedule_weekend,
                        service_manager_name, maps_2gis_link, google_maps_link,
                        created_at, updated_at
                    )
                    SELECT 
                        id, city, address, phone_store, phone_service,
                        work_schedule_weekdays, work_schedule_weekend,
                        service_schedule_weekdays, service_schedule_weekend,
                        service_manager_name, maps_2gis_link, google_maps_link,
                        created_at, updated_at
                    FROM service_points
                """)

                # Удаляем старую таблицу
                await self.connection.execute("DROP TABLE service_points")

                # Переименовываем новую таблицу
                await self.connection.execute(
                    "ALTER TABLE service_points_new RENAME TO service_points"
                )
            else:
                # Создаем новую таблицу, если старая не существует
                await self.connection.execute("""
                    CREATE TABLE IF NOT EXISTS service_points (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        city TEXT NOT NULL,
                        address TEXT NOT NULL,
                        phone_store TEXT,
                        phone_service TEXT,
                        work_schedule_weekdays TEXT,
                        work_schedule_weekend TEXT,
                        service_schedule_weekdays TEXT,
                        service_schedule_weekend TEXT,
                        service_manager_name TEXT,
                        maps_2gis_link TEXT,
                        google_maps_link TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(city, address)
                    )
                """)
            
            # Создаем таблицу для продуктов
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    subtype TEXT,
                    size TEXT NOT NULL,
                    link TEXT NOT NULL
                )
            """)
            
            # Создаем таблицу пользователей
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    phone_number TEXT,
                    birth_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создаем таблицу запросов на связь
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS contact_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    request_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Создаем таблицу чатов
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    manager_id INTEGER,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )
            """)
            
            # Создаем таблицу сообщений
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    sender_id INTEGER,
                    message_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создаем таблицу логов
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS user_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            await self.connection.commit()
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise
        finally:
            await self.disconnect()

    async def get_all_cities(self) -> List[str]:
        """Получение списка всех городов"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                "SELECT DISTINCT city FROM service_points"
            )
            cities = [row[0] for row in await cursor.fetchall()]
            await cursor.close()
            return cities
        except Exception as e:
            logger.error(f"Ошибка при получении списка городов: {e}")
            return []
        finally:
            await self.disconnect()

    async def get_locations_by_city(
        self, city: str, contact_type: str
    ) -> List[str]:
        """Получение списка адресов в городе с учетом типа контакта"""
        try:
            await self.connect()
            
            if contact_type == "Магазин":
                query = """
                    SELECT DISTINCT address FROM service_points 
                    WHERE city = ? AND phone_store IS NOT NULL 
                    AND phone_store != ''
                """
            else:  # Сервис
                query = """
                    SELECT DISTINCT address FROM service_points 
                    WHERE city = ? 
                    AND (
                        (phone_service IS NOT NULL AND phone_service != '') OR
                        (service_schedule_weekdays IS NOT NULL AND service_schedule_weekdays != '') OR
                        (service_schedule_weekend IS NOT NULL AND service_schedule_weekend != '') OR
                        (service_manager_name IS NOT NULL AND service_manager_name != '')
                    )
                """
            
            cursor = await self.connection.execute(query, (city,))
            locations = [row[0] for row in await cursor.fetchall()]
            await cursor.close()
            return locations
        except Exception as e:
            logger.error(
                f"Ошибка при получении списка адресов в городе {city}: {e}"
            )
            return []
        finally:
            await self.disconnect()

    async def get_location_info(
        self, city: str, address: str
    ) -> Optional[Dict]:
        """Получение информации о торговой точке"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                """
                SELECT * FROM service_points 
                WHERE city = ? AND address = ?
                """,
                (city, address)
            )
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                columns = [
                    description[0] for description in cursor.description
                ]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(
                f"Ошибка при получении информации об адресе {address}: {e}"
            )
            return None
        finally:
            await self.disconnect()

    async def add_service_point(self, data: Dict) -> bool:
        """Добавление новой торговой точки"""
        try:
            await self.connect()
            await self.connection.execute(
                """
                INSERT OR REPLACE INTO service_points (
                    city, address, phone_store, phone_service,
                    work_schedule_weekdays, work_schedule_weekend,
                    service_schedule_weekdays, service_schedule_weekend,
                    service_manager_name, maps_2gis_link, google_maps_link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data['city'], data['address'],
                    data.get('phone_store'), data.get('phone_service'),
                    data.get('work_schedule_weekdays'),
                    data.get('work_schedule_weekend'),
                    data.get('service_schedule_weekdays'),
                    data.get('service_schedule_weekend'),
                    data.get('service_manager_name'),
                    data.get('maps_2gis_link'),
                    data.get('google_maps_link')
                )
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении торговой точки: {e}")
            return False
        finally:
            await self.disconnect()

    # Методы для работы с каталогом
    async def get_vehicle_types(self, category: str) -> List[str]:
        """Получение списка типов ТС для категории"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                """
                SELECT DISTINCT vehicle_type FROM products 
                WHERE category = ?
                """,
                (category,)
            )
            types = [row[0] for row in await cursor.fetchall()]
            await cursor.close()
            return types
        except Exception as e:
            logger.error(f"Ошибка при получении типов ТС: {e}")
            return []
        finally:
            await self.disconnect()

    async def get_subtypes(self, category: str, vehicle_type: str) -> List[str]:
        """Получение списка подтипов для категории и типа ТС"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                """
                SELECT DISTINCT subtype FROM products 
                WHERE category = ? AND vehicle_type = ? AND subtype IS NOT NULL
                """,
                (category, vehicle_type)
            )
            subtypes = [row[0] for row in await cursor.fetchall()]
            await cursor.close()
            return subtypes
        except Exception as e:
            logger.error(f"Ошибка при получении подтипов: {e}")
            return []
        finally:
            await self.disconnect()

    async def get_sizes(
        self, category: str, vehicle_type: str, subtype: Optional[str] = None
    ) -> List[str]:
        """Получение списка размеров"""
        try:
            await self.connect()
            if subtype:
                cursor = await self.connection.execute(
                    """
                    SELECT DISTINCT size FROM products 
                    WHERE category = ? AND vehicle_type = ? AND subtype = ?
                    """,
                    (category, vehicle_type, subtype)
                )
            else:
                cursor = await self.connection.execute(
                    """
                    SELECT DISTINCT size FROM products 
                    WHERE category = ? AND vehicle_type = ?
                    """,
                    (category, vehicle_type)
                )
            sizes = [row[0] for row in await cursor.fetchall()]
            await cursor.close()
            return sizes
        except Exception as e:
            logger.error(f"Ошибка при получении размеров: {e}")
            return []
        finally:
            await self.disconnect()

    async def get_product_link(
        self, category: str, vehicle_type: str, subtype: Optional[str],
        size: str
    ) -> Optional[str]:
        """Получение ссылки на товар"""
        try:
            await self.connect()
            if subtype:
                cursor = await self.connection.execute(
                    """
                    SELECT link FROM products 
                    WHERE category = ? AND vehicle_type = ? 
                    AND subtype = ? AND size = ?
                    """,
                    (category, vehicle_type, subtype, size)
                )
            else:
                cursor = await self.connection.execute(
                    """
                    SELECT link FROM products 
                    WHERE category = ? AND vehicle_type = ? AND size = ?
                    """,
                    (category, vehicle_type, size)
                )
            row = await cursor.fetchone()
            await cursor.close()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Ошибка при получении ссылки на товар: {e}")
            return None
        finally:
            await self.disconnect()

    async def add_product(self, data: Dict) -> bool:
        """Добавление нового товара"""
        try:
            await self.connect()
            await self.connection.execute(
                """
                INSERT INTO products (
                    category, vehicle_type, subtype, size, link
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data['category'], data['vehicle_type'],
                    data.get('subtype'), data['size'], data['link']
                )
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара: {e}")
            return False
        finally:
            await self.disconnect()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя: {e}")
            return None
        finally:
            await self.disconnect()

    async def save_user(self, user_data: Dict) -> bool:
        """Сохранение информации о пользователе"""
        try:
            await self.connect()
            await self.connection.execute(
                """
                INSERT OR REPLACE INTO users (
                    user_id, first_name, last_name, username,
                    phone_number, birth_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    user_data['user_id'],
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('username'),
                    user_data.get('phone_number'),
                    user_data.get('birth_date')
                )
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении пользователя: {e}")
            return False
        finally:
            await self.disconnect()

    async def create_contact_request(self, user_id: int, request_type: str) -> bool:
        """Создание запроса на связь с менеджером"""
        try:
            await self.connect()
            await self.connection.execute(
                """
                INSERT INTO contact_requests (user_id, request_type)
                VALUES (?, ?)
                """,
                (user_id, request_type)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании запроса: {e}")
            return False
        finally:
            await self.disconnect()

    async def update_user(self, user_id: int, data: dict) -> bool:
        """Обновление данных пользователя"""
        try:
            await self.connect()
            # Формируем SQL запрос на основе переданных данных
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            query = f"""
                UPDATE users 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """
            values = list(data.values()) + [user_id]
            
            await self.connection.execute(query, values)
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя: {e}")
            return False
        finally:
            await self.disconnect()

    async def create_chat(self, user_id: int, manager_id: int) -> int:
        """Создание чата между пользователем и менеджером"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                """
                INSERT INTO chats (user_id, manager_id, status)
                VALUES (?, ?, 'pending')
                """,
                (user_id, manager_id)
            )
            chat_id = cursor.lastrowid
            await self.connection.commit()
            return chat_id
        except Exception as e:
            logger.error(f"Ошибка при создании чата: {e}")
            return 0
        finally:
            await self.disconnect()

    async def get_chat(self, user_id: int) -> Optional[Dict]:
        """Получение информации о чате по ID пользователя"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                """
                SELECT * FROM chats 
                WHERE user_id = ? AND status != 'closed'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,)
            )
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении чата: {e}")
            return None
        finally:
            await self.disconnect()

    async def update_chat_status(self, chat_id: int, status: str) -> bool:
        """Обновление статуса чата"""
        try:
            await self.connect()
            await self.connection.execute(
                """
                UPDATE chats 
                SET status = ?
                WHERE id = ?
                """,
                (status, chat_id)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса чата: {e}")
            return False
        finally:
            await self.disconnect()

    async def accept_chat(self, chat_id: int) -> bool:
        """Принятие чата менеджером"""
        try:
            await self.connect()
            await self.connection.execute(
                """
                UPDATE chats 
                SET status = 'active', accepted_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (chat_id,)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при принятии чата: {e}")
            return False
        finally:
            await self.disconnect()

    async def get_pending_chats(self) -> List[Dict]:
        """Получение списка ожидающих чатов"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                """
                SELECT c.*, u.first_name, u.last_name, u.username
                FROM chats c
                JOIN users u ON c.user_id = u.user_id
                WHERE c.status = 'pending'
                """
            )
            rows = await cursor.fetchall()
            await cursor.close()
            
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении ожидающих чатов: {e}")
            return []
        finally:
            await self.disconnect()

    async def get_active_chat(self, user_id: int) -> Optional[Dict]:
        """Получение активного чата пользователя"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                """
                SELECT * FROM chats 
                WHERE user_id = ? AND status = 'active'
                """,
                (user_id,)
            )
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении чата: {e}")
            return None
        finally:
            await self.disconnect()

    async def save_message(self, chat_id: int, sender_id: int, message_text: str) -> bool:
        """Сохранение сообщения в чате"""
        try:
            await self.connect()
            await self.connection.execute(
                """
                INSERT INTO messages (chat_id, sender_id, message_text)
                VALUES (?, ?, ?)
                """,
                (chat_id, sender_id, message_text)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения: {e}")
            return False
        finally:
            await self.disconnect()

    async def close_chat(self, chat_id: int) -> bool:
        """Закрытие чата"""
        try:
            await self.connect()
            await self.connection.execute(
                """
                UPDATE chats 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (chat_id,)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при закрытии чата: {e}")
            return False
        finally:
            await self.disconnect()

    async def get_chat_by_id(self, chat_id: int) -> dict:
        """Получение информации о чате по ID чата"""
        try:
            await self.connect()
            query = """
                SELECT c.*, u.first_name, u.last_name, u.username
                FROM chats c
                LEFT JOIN users u ON c.user_id = u.user_id
                WHERE c.id = ?
            """
            cursor = await self.connection.execute(query, (chat_id,))
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении чата по ID: {e}")
            return None
        finally:
            await self.disconnect()

    async def get_active_chat_by_manager(self, manager_id: int) -> Optional[Dict]:
        """Получение активного чата по ID менеджера"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                """
                SELECT c.*, u.first_name, u.last_name, u.username
                FROM chats c
                LEFT JOIN users u ON c.user_id = u.user_id
                WHERE c.manager_id = ? AND c.status = 'active'
                ORDER BY c.created_at DESC
                LIMIT 1
                """,
                (manager_id,)
            )
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении активного чата менеджера: {e}")
            return None
        finally:
            await self.disconnect()

    async def save_user_log(self, user_id: int, action: str, details: str = None) -> bool:
        """Сохранение лога действия пользователя"""
        try:
            await self.connect()
            await self.connection.execute(
                '''
                INSERT INTO user_logs (user_id, action, details)
                VALUES (?, ?, ?)
                ''',
                (user_id, action, details)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении лога: {e}")
            return False
        finally:
            await self.disconnect()

    async def get_user_logs(self, user_id: int, limit: int = 100) -> list:
        """Получение логов пользователя"""
        try:
            await self.connect()
            cursor = await self.connection.execute(
                '''
                SELECT action, details, created_at
                FROM user_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                user_id, limit
            )
            rows = await cursor.fetchall()
            await cursor.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении логов: {e}")
            return []
        finally:
            await self.disconnect() 