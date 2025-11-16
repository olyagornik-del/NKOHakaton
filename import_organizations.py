import csv
import sqlite3
from geopy.geocoders import Nominatim
import time


# Функция для получения координат города
def get_city_coordinates(city_name):
    geolocator = Nominatim(user_agent="nko_map_app")
    try:
        location = geolocator.geocode(f"{city_name}, Россия")
        if location:
            return location.latitude, location.longitude
        else:
            print(f"Координаты для {city_name} не найдены")
            return None, None
    except Exception as e:
        print(f"Ошибка геокодирования для {city_name}: {e}")
        return None, None


# Подключаемся к базе данных
conn = sqlite3.connect('instance/nko.db')  # Путь к вашей БД
cursor = conn.cursor()

# Читаем CSV файл
with open('таблица_нко - Лист1.csv', 'r', encoding='utf-8') as file:
    csv_reader = csv.DictReader(file)

    for row in csv_reader:
        city = row['Город']
        name = row['Название']
        category = row['Деятельность']
        description = row['краткое описание деятельности']

        # Получаем координаты города (ставим метку в центр города)
        lat, lon = get_city_coordinates(city)

        # Вставляем данные в БД
        cursor.execute('''
            INSERT INTO organization 
            (name, category, description, city, latitude, longitude, is_approved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, description, city, lat, lon, True))

        # Пауза чтобы не превысить лимиты геокодера
        time.sleep(1)

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()

print("Импорт данных завершен!")