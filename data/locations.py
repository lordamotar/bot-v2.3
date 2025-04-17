# Структура данных для хранения информации о торговых точках
LOCATIONS = {
    "Алматы": {
        "Mega Center": {
            "address": "ул. Розыбакиева 247",
            "phone": "+7 (727) 123-45-67",
            "service_phone": "+7 (727) 123-45-68",
            "workdays_hours": "10:00 - 20:00",
            "weekend_hours": "10:00 - 21:00",
            "service_workdays_hours": "09:00 - 18:00",
            "service_weekend_hours": "10:00 - 16:00",
            "service_manager": "Иван Иванов",
            "map_link": "https://yandex.kz/maps/org/mega_center/123456789"
        },
        "Алтын Орда": {
            "address": "ул. Толе би 55",
            "phone": "+7 (727) 234-56-78",
            "service_phone": "+7 (727) 234-56-79",
            "workdays_hours": "09:00 - 19:00",
            "weekend_hours": "09:00 - 20:00",
            "service_workdays_hours": "09:00 - 18:00",
            "service_weekend_hours": "10:00 - 16:00",
            "service_manager": "Петр Петров",
            "map_link": "https://yandex.kz/maps/org/altyn_orda/987654321"
        }
    },
    "Астана": {
        "Mega Silk Way": {
            "address": "ул. Туркестан 1",
            "phone": "+7 (7172) 123-45-67",
            "service_phone": "+7 (7172) 123-45-68",
            "workdays_hours": "10:00 - 20:00",
            "weekend_hours": "10:00 - 21:00",
            "service_workdays_hours": "09:00 - 18:00",
            "service_weekend_hours": "10:00 - 16:00",
            "service_manager": "Сергей Сергеев",
            "map_link": "https://yandex.kz/maps/org/mega_silk_way/456789123"
        }
    }
}

# Получение списка городов
def get_cities():
    return list(LOCATIONS.keys())

# Получение списка торговых точек в городе
def get_locations(city: str):
    return list(LOCATIONS.get(city, {}).keys())

# Получение информации о торговой точке
def get_location_info(city: str, location: str):
    return LOCATIONS.get(city, {}).get(location) 