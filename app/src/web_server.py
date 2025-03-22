from flask import Flask, jsonify, send_from_directory
from .thingspeak_client import ThingSpeakClient
from ..config.api_keys import (
    THINGSPEAK_CHANNEL_ID,
    THINGSPEAK_READ_API_KEY,
    THINGSPEAK_WRITE_API_KEY
)
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)

# Создаем клиент ThingSpeak с ключами из конфигурации
client = ThingSpeakClient(
    channel_id=THINGSPEAK_CHANNEL_ID,
    read_api_key=THINGSPEAK_READ_API_KEY,
    write_api_key=THINGSPEAK_WRITE_API_KEY
)

@app.route('/')
def index():
    return send_from_directory('../website', 'index.html')

@app.route('/api/latest-data')
def get_latest_data():
    data = client.get_latest_data()
    if data:
        return jsonify(data)
    return jsonify({'error': 'Нет данных'}), 404

@app.route('/api/historical-data')
def get_historical_data():
    data = client.get_historical_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 