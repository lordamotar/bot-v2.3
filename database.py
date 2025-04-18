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