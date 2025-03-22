import requests
import time
from datetime import datetime

class ThingSpeakClient:
    def __init__(self, channel_id, read_api_key, write_api_key=None):
        self.channel_id = channel_id
        self.read_api_key = read_api_key
        self.write_api_key = write_api_key
        self.base_url = "https://api.thingspeak.com"
        
    def upload_data(self, dust, gas, co, methane, humidity, temperature, status, alerts):
        """Загрузка данных на ThingSpeak"""
        if not self.write_api_key:
            raise ValueError("Write API key is required for uploading data")
            
        url = f"{self.base_url}/update"
        params = {
            'api_key': self.write_api_key,
            'field1': dust,
            'field2': gas,
            'field3': co,
            'field4': methane,
            'field5': humidity,
            'field6': temperature,
            'field7': status,
            'field8': alerts
        }
        
        try:
            print(f"\nОтправка данных на ThingSpeak:")
            print(f"URL: {url}")
            print(f"Параметры: {params}")
            
            response = requests.get(url, params=params)  # ThingSpeak использует GET для обновления
            print(f"Ответ сервера: {response.text}")
            
            response.raise_for_status()
            if response.text == '0':
                print("Ошибка при отправке данных: ThingSpeak вернул 0")
                return False
            return True
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return False
            
    def get_latest_data(self):
        """Получение последних данных с ThingSpeak"""
        url = f"{self.base_url}/channels/{self.channel_id}/feeds/last.json"
        params = {
            'api_key': self.read_api_key
        }
        
        try:
            print(f"\nПолучение последних данных с ThingSpeak:")
            print(f"URL: {url}")
            print(f"Параметры: {params}")
            
            response = requests.get(url, params=params)
            print(f"Ответ сервера: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при получении данных: {e}")
            return None
            
    def get_historical_data(self, results=100):
        """Получение исторических данных с ThingSpeak"""
        url = f"{self.base_url}/channels/{self.channel_id}/feeds.json"
        params = {
            'api_key': self.read_api_key,
            'results': results
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()['feeds']
        except Exception as e:
            print(f"Ошибка при получении исторических данных: {e}")
            return [] 