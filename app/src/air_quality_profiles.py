"""
Профили настроек для различных условий мониторинга качества воздуха
"""

# Стандартные профили
AIR_QUALITY_PROFILES = {
    "street": {
        "name": "Улица",
        "dust_threshold": 50,  # мкг/м³ (PM2.5 + PM10)
        "gas_threshold": 500,   # ppm (общие летучие органические соединения)
        "co_threshold": 350,     # ppm (угарный газ, норма ВОЗ)
        "methane_threshold": 600,  # ppm (метан, нижний предел взрывоопасности 5000 ppm)
        "humidity_range": (20, 100),  # % (уличная влажность)
        "temperature_range": (-10, 30)  # °C (уличная температура)
    },
    "home": {
        "name": "Дом",
        "dust_threshold": 35,   # мкг/м³ (PM2.5 норма ВОЗ)
        "gas_threshold": 400,   # ppm (TVOC норма для жилых помещений)
        "co_threshold": 300,      # ppm (норма CO для жилых помещений)
        "methane_threshold": 550,  # ppm (бытовой газ, порог срабатывания)
        "humidity_range": (20, 60),  # % (комфортный диапазон)
        "temperature_range": (18, 26)  # °C (комфортный диапазон)
    },
    "event": {
        "name": "Рабочие помещения",
        "dust_threshold": 35,   # мкг/м³ (строгая норма для общественных мест)
        "gas_threshold": 450,   # ppm (строгая норма TVOC)
        "co_threshold": 450,      # ppm (строгая норма CO)
        "methane_threshold": 650,  # ppm (строгий контроль)
        "humidity_range": (20, 60),  # % (оптимальный диапазон)
        "temperature_range": (16, 24)  # °C (оптимальный диапазон)
    },
    "custom": {
        "name": "Пользовательский",
        "dust_threshold": 35,   # мкг/м³
        "gas_threshold": 400,   # ppm
        "co_threshold": 350,      # ppm
        "methane_threshold": 600,  # ppm
        "humidity_range": (20, 60),  # %
        "temperature_range": (18, 26)  # °C
    }
}

def get_profile(profile_name):
    """Получение профиля по имени"""
    return AIR_QUALITY_PROFILES.get(profile_name, AIR_QUALITY_PROFILES["home"])

def update_custom_profile(settings):
    """Обновление пользовательского профиля"""
    AIR_QUALITY_PROFILES["custom"].update(settings)

def get_arduino_command(profile_name):
    """Формирование команды для Arduino"""
    profile = get_profile(profile_name)
    command = f"SET_THRESHOLDS:"
    command += f"{profile['dust_threshold']},"
    command += f"{profile['gas_threshold']},"
    command += f"{profile['co_threshold']},"
    command += f"{profile['methane_threshold']},"
    command += f"{profile['humidity_range'][0]},{profile['humidity_range'][1]},"
    command += f"{profile['temperature_range'][0]},{profile['temperature_range'][1]}\n"
    return command.encode() 