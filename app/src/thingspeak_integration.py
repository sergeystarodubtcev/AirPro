from .thingspeak_client import ThingSpeakClient
from ..config.api_keys import (
    THINGSPEAK_CHANNEL_ID,
    THINGSPEAK_READ_API_KEY,
    THINGSPEAK_WRITE_API_KEY
)
import threading
import time

# Создаем клиент ThingSpeak с ключами из конфигурации
client = ThingSpeakClient(
    channel_id=THINGSPEAK_CHANNEL_ID,
    read_api_key=THINGSPEAK_READ_API_KEY,
    write_api_key=THINGSPEAK_WRITE_API_KEY
)

class ThingSpeakIntegration:
    def __init__(self, monitor):
        self.monitor = monitor
        self.running = False
        self.upload_thread = None
        
    def start(self):
        """Запуск отправки данных на ThingSpeak"""
        if not self.running:
            self.running = True
            self.upload_thread = threading.Thread(target=self._upload_loop)
            self.upload_thread.daemon = True
            self.upload_thread.start()
            self.monitor.log("ThingSpeak: Отправка данных активирована")
    
    def stop(self):
        """Остановка отправки данных"""
        self.running = False
        if self.upload_thread:
            self.upload_thread.join()
            self.monitor.log("ThingSpeak: Отправка данных остановлена")
    
    def _upload_loop(self):
        """Цикл отправки данных на ThingSpeak"""
        while self.running:
            try:
                # Получаем текущие значения с датчиков
                data = {
                    'dust': self.monitor.dust_level,
                    'gas': self.monitor.gas_level,
                    'co': self.monitor.co_level,
                    'methane': self.monitor.methane_level,
                    'humidity': self.monitor.humidity,
                    'temperature': self.monitor.temperature,
                    'status': "Normal" if not self.monitor.last_alert_status else "Alert",
                    'alerts': ", ".join(self.monitor.alerts) if self.monitor.alerts else "None"
                }
                
                # Проверяем, что все значения корректны
                if all(isinstance(v, (int, float)) and v >= 0 for v in [data['dust'], data['gas'], data['co'], 
                                                                      data['methane'], data['humidity'], data['temperature']]):
                    # Отправляем данные на ThingSpeak
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
                        self.monitor.log("\nThingSpeak: Данные успешно отправлены:")
                        self.monitor.log(f"Пыль: {data['dust']} мкг/м³")
                        self.monitor.log(f"Газ: {data['gas']} ppm")
                        self.monitor.log(f"CO: {data['co']} ppm")
                        self.monitor.log(f"Метан: {data['methane']} ppm")
                        self.monitor.log(f"Влажность: {data['humidity']}%")
                        self.monitor.log(f"Температура: {data['temperature']}°C")
                        
                        # Проверяем последние полученные данные
                        latest = client.get_latest_data()
                        if latest:
                            self.monitor.log("\nПоследние данные на ThingSpeak:")
                            self.monitor.log(f"Пыль: {latest.get('field1')} мкг/м³")
                            self.monitor.log(f"Газ: {latest.get('field2')} ppm")
                            self.monitor.log(f"CO: {latest.get('field3')} ppm")
                            self.monitor.log(f"Метан: {latest.get('field4')} ppm")
                            self.monitor.log(f"Влажность: {latest.get('field5')}%")
                            self.monitor.log(f"Температура: {latest.get('field6')}°C")
                            self.monitor.log(f"Статус: {latest.get('field7')}")
                            self.monitor.log(f"Тревоги: {latest.get('field8')}")
                        else:
                            self.monitor.log("Не удалось получить последние данные")
                    else:
                        self.monitor.log("ThingSpeak: Ошибка отправки данных")
                else:
                    self.monitor.log("ThingSpeak: Некорректные данные датчиков")
                    
            except Exception as e:
                self.monitor.log(f"ThingSpeak: Ошибка: {str(e)}")
            
            # Отправляем данные каждые 10 секунд
            self.monitor.log("\nОжидание 10 секунд до следующей отправки...")
            time.sleep(10) 