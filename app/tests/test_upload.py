import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.thingspeak_client import ThingSpeakClient
from config.api_keys import (
    THINGSPEAK_CHANNEL_ID,
    THINGSPEAK_READ_API_KEY,
    THINGSPEAK_WRITE_API_KEY
)
import time
import serial
import json

def read_serial_data(port='COM5', baudrate=9600):
    """Чтение данных с последовательного порта"""
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Подключено к порту {port}")
        
        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8', errors='ignore').strip()
                if data.startswith("DATA:"):
                    # Формат: DATA:пыль,газ,метан,CO,влажность,температура
                    values = data.split('DATA:')[1].split(',')
                    if len(values) >= 6:
                        return {
                            'dust': float(values[0]),
                            'gas': int(values[1]),
                            'methane': float(values[2]),
                            'co': float(values[3]),
                            'humidity': float(values[4]),
                            'temperature': float(values[5]),
                            'status': 'Normal',
                            'alerts': 'None'
                        }
    except Exception as e:
        print(f"Ошибка чтения с порта: {e}")
        return None

def test_upload():
    # Создаем клиент ThingSpeak с ключами из конфигурации
    client = ThingSpeakClient(
        channel_id=THINGSPEAK_CHANNEL_ID,
        read_api_key=THINGSPEAK_READ_API_KEY,
        write_api_key=THINGSPEAK_WRITE_API_KEY
    )

    print("Начинаем отправку данных на ThingSpeak...")
    
    while True:
        try:
            # Читаем данные с устройства
            data = read_serial_data()
            
            if data:
                # Отправляем данные
                success = client.upload_data(
                    dust=data['dust'],
                    gas=data['gas'],
                    co=data['co'],
                    methane=data['methane'],
                    humidity=data['humidity'],
                    temperature=data['temperature'],
                    status=data['status'],
                    alerts=data['alerts']
                )
                
                if success:
                    print("\nДанные успешно отправлены:")
                    print(f"Пыль: {data['dust']} мкг/м³")
                    print(f"Газ: {data['gas']} ppm")
                    print(f"CO: {data['co']} ppm")
                    print(f"Метан: {data['methane']} ppm")
                    print(f"Влажность: {data['humidity']}%")
                    print(f"Температура: {data['temperature']}°C")
                else:
                    print("Ошибка при отправке данных")
                    
            # Проверяем последние полученные данные
            latest = client.get_latest_data()
            if latest:
                print("\nПоследние данные на ThingSpeak:")
                print(f"Пыль: {latest.get('field1')} мкг/м³")
                print(f"Газ: {latest.get('field2')} ppm")
                print(f"CO: {latest.get('field3')} ppm")
                print(f"Метан: {latest.get('field4')} ppm")
                print(f"Влажность: {latest.get('field5')}%")
                print(f"Температура: {latest.get('field6')}°C")
                print(f"Статус: {latest.get('field7')}")
                print(f"Тревоги: {latest.get('field8')}")
            else:
                print("Не удалось получить последние данные")
                
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            
        # Ждем 10 секунд перед следующей отправкой
        print("\nОжидание 10 секунд до следующей отправки...")
        time.sleep(10)

if __name__ == "__main__":
    test_upload() 