# Air Pro - Система мониторинга качества воздуха

## Описание проекта

Air Pro - это комплексное решение для мониторинга качества воздуха, состоящее из трех основных компонентов:

1. **Приложение для Windows** (`app/`)
   - Графический интерфейс для отображения данных
   - Настройка параметров мониторинга
   - Экспорт данных
   - Интеграция с ThingSpeak

2. **Веб-сайт** (`website/`)
   - Публичный доступ к данным
   - Визуализация показателей
   - История измерений

3. **Arduino-устройство** (`arduino/`)
   - Сбор данных с датчиков
   - Передача данных в приложение
   - Автономная работа

## Структура проекта

```
Air_Pro/
├── app/                # Приложение для Windows
│   ├── src/           # Исходный код
│   ├── tests/         # Тесты
│   ├── docs/          # Документация
│   ├── resources/     # Ресурсы
│   ├── config/        # Конфигурация
│   └── releases/      # Скомпилированные версии
├── website/           # Веб-интерфейс
└── arduino/           # Код для Arduino
```

## Установка

### Вариант 1: Готовая версия (рекомендуется)

1. Перейдите в директорию `app/releases/`
2. Скачайте последнюю версию `Air_Pro.exe`
3. Запустите установщик
4. Следуйте инструкциям установщика

### Вариант 2: Из исходного кода

1. Клонируйте репозиторий:
```bash
git clone https://github.com/sergey-fintech/air-pro.git
cd air-pro
```

2. Установите приложение:
```bash
cd app
pip install -r requirements.txt
python src/air_quality_monitor2.py
```

3. Настройте Arduino:
   - Откройте `arduino/air_quality_monitor.ino` в Arduino IDE
   - Загрузите код на Arduino
   - Подключите датчики

## Документация

Подробная документация доступна в директории `app/docs/`:

- [Общее описание](/app/docs/general/overview.md)
- [Установка и настройка](/app/docs/setup/installation.md)
- [Руководство пользователя](/app/docs/user_guide/usage.md)
- [Руководство разработчика](/app/docs/development/development.md)

## Требования

### Системные требования
- Windows 10 или выше
- Python 3.11+ (только для установки из исходного кода)
- Arduino IDE
- COM-порт для Arduino

### Оборудование
- Arduino (Uno или совместимая)
- Датчики качества воздуха
- USB-кабель

## Лицензия
MIT License

## Поддержка

При возникновении проблем:
1. Проверьте [FAQ](/app/docs/faq/faq.md)
2. Создайте issue в репозитории
3. Обратитесь к документации

## Авторы
- [sergeystarodubtcev] - Разработчик

## Конфигурация API ключей

Для работы с ThingSpeak и другими сервисами необходимо настроить API ключи:

1. Скопируйте файл `app/config/api_keys.py` в директорию `app/config/`
2. Замените значения в файле на ваши реальные ключи:
```python
THINGSPEAK_CHANNEL_ID = "YOUR_CHANNEL_ID"
THINGSPEAK_WRITE_API_KEY = "YOUR_WRITE_API_KEY"
THINGSPEAK_READ_API_KEY = "YOUR_READ_API_KEY"
```
3. Не коммитьте файл с реальными ключами в репозиторий

### Получение API ключей ThingSpeak
1. Зарегистрируйтесь на [ThingSpeak](https://thingspeak.com)
2. Создайте новый канал
3. В настройках канала найдите:
   - Channel ID
   - Write API Key
   - Read API Key
