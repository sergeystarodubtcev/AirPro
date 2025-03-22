// Подключение библиотеки для работы с DHT22
#include <DHT.h>

unsigned long lastDataSendTime = 0;     // Последнее время отправки данных
const long dataSendInterval = 3000;     // Интервал отправки данных (3 секунды)

// Пины для датчика пыли
const int measurePin = A1;   // Аналоговый выход датчика (Желтый - V0)
const int ledPower = 2;      // LED питание датчика (Красный - V-LED)

// Пины для RGB светодиода
const int redPin = 13;        // Красный канал RGB светодиода
const int greenPin = 11;     // Зеленый канал RGB светодиода
const int bluePin = 12;      // Синий канал RGB светодиода

// Новые компоненты
const int buzzerPin = 6;     // Пин для зуммера
const int silentModePin = 7; // Пин для кнопки беззвучного режима
const int gasPin = A0;       // Пин для датчика газов MQ135

// Новые датчики газа
const int methanePin = A2;   // Пин для датчика метана MQ-4
const int coPin = A3;        // Пин для датчика угарного газа MQ-7

// Настройка датчика DHT22
#define DHTPIN 4             // Пин подключения DHT22
#define DHTTYPE DHT22        // Тип датчика (DHT22)
DHT dht(DHTPIN, DHTTYPE);    // Инициализация датчика DHT

// Константы для калибровки датчика пыли
const float calibrationFactor = 0.5;    // Калибровочный коэффициент
const float nodustVoltage = 0.6;        // Напряжение при отсутствии пыли (может потребоваться настройка)

// Настраиваемые пороговые значения
float dustThreshold = 30.0;      // Порог пыли (мкг/м³)
int gasThreshold = 270;          // Порог газа (ppm)
int methaneThreshold = 100;      // Порог метана (ppm)
int coThreshold = 20;            // Порог CO (ppm)
float minHumidity = 30.0;        // Минимальная влажность (%)
float maxHumidity = 70.0;        // Максимальная влажность (%)
float minTemperature = 18.0;     // Минимальная температура (°C)
float maxTemperature = 28.0;     // Максимальная температура (°C)

// Переменные для отслеживания состояния
bool silentMode = false;                // Флаг беззвучного режима
int buttonState = HIGH;                 // Текущее состояние кнопки
int lastButtonState = HIGH;             // Предыдущее состояние кнопки
unsigned long lastButtonPressTime = 0;  // Время последнего нажатия кнопки

// Переменные для хранения данных DHT22
float humidity = 0;                    // Влажность с DHT22
float temperature = 0;                 // Температура с DHT22
unsigned long lastDHTReadTime = 0;     // Последнее время чтения DHT
const long dhtReadInterval = 2000;     // Интервал чтения DHT (2 секунды)

// Переменные для отслеживания тревог и их процентного отклонения
float dustPercentage = 0;
float gasPercentage = 0;
float methanePercentage = 0;   // Процент превышения порога метана
float coPercentage = 0;        // Процент превышения порога CO
float humidityPercentage = 0;
float temperaturePercentage = 0;
bool dustAlarm = false;
bool gasAlarm = false;
bool methaneAlarm = false;     // Флаг тревоги по метану
bool coAlarm = false;          // Флаг тревоги по CO
bool humidityAlarm = false;
bool temperatureAlarm = false;

void setup() {
  // Настройка пина LED датчика пыли как выход
  pinMode(ledPower, OUTPUT);
  digitalWrite(ledPower, LOW);  // Выключаем LED датчика

  // Настройка пинов RGB светодиода
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  
  // Настройка новых компонентов
  pinMode(buzzerPin, OUTPUT);
  pinMode(silentModePin, INPUT_PULLUP); // Используем внутренний подтягивающий резистор
  
  // Инициализация датчика DHT
  dht.begin();
  
  // Инициализация серийного порта для отладки и передачи данных
  Serial.begin(9600);
  Serial.println("STARTING_SENSOR_SYSTEM");
  
  // Задержка для инициализации и стабилизации датчиков
  delay(1000);
  
  // Установим начальный цвет на зеленый
  setColor(0, 255, 0);
  
  Serial.println("SYSTEM_READY");
  tone(buzzerPin, 200, 200);
  
  // Первое считывание с DHT
  readDHTSensor();
}

void loop() {
  
  // Проверка состояния кнопки
  int currentButtonState = digitalRead(silentModePin);
  
  // Если кнопка нажата (переход с HIGH на LOW)
  if (lastButtonState == HIGH && currentButtonState == LOW) {
    // Переключаем режим
    silentMode = !silentMode;
    tone(buzzerPin, 2000, 200);
    // Отправляем информацию о смене режима
    Serial.print("SILENT_MODE:");
    Serial.println(silentMode ? "ON" : "OFF");
  }
  
  // Сохраняем текущее состояние кнопки
  lastButtonState = currentButtonState;
  
 
  unsigned long currentTime = millis();
  if (currentTime - lastDataSendTime >= dataSendInterval) {
    
      // Периодическое чтение DHT22
    if (millis() - lastDHTReadTime > dhtReadInterval) {
      readDHTSensor();
      lastDHTReadTime = millis();
    }
  
    // Измерение уровня пыли
    float dustDensity = measureDust();
  
    // Измерение уровня газов
    int gasValue = measureGas();
    int methaneValue = measureMethane();   // Измерение метана
    int coValue = measureCO();             // Измерение угарного газа
  
    // Вычисление процентных отклонений
    calculatePercentages(dustDensity, gasValue, methaneValue, coValue, humidity, temperature);
  
    // Обновление RGB индикации и зуммера на основе всех показателей
    updateIndicators(dustDensity, gasValue, methaneValue, coValue, humidity, temperature);

    sendDataToComputer(dustDensity, gasValue, methaneValue, coValue, humidity, temperature);
    lastDataSendTime = currentTime;
  }
  
  // Проверка, есть ли данные для чтения от компьютера
  while (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
}

void readDHTSensor() {
  // Считывание данных с DHT22
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  
  // Проверка, успешно ли прошло считывание
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("ERROR:DHT_READ_FAILED");
    humidity = 0;
    temperature = 0;
  }
}

float measureDust() {
  // Переменные для измерения
  float voMeasured = 0;
  float calcVoltage = 0;
  float dustDensity = 0;
  
  // Включаем LED датчика на 0.28ms
  digitalWrite(ledPower, HIGH);
  delayMicroseconds(280);
  
  // Читаем аналоговое значение с датчика
  voMeasured = analogRead(measurePin);
  
  // Выключаем LED датчика
  digitalWrite(ledPower, LOW);
  
  // Конвертация аналогового значения (0-1023) в напряжение (0-5V)
  calcVoltage = voMeasured * (5.0 / 1024.0);
  
  // Расчет плотности пыли по формуле
  if (calcVoltage > nodustVoltage) {
    dustDensity = (calcVoltage - nodustVoltage) * calibrationFactor * 100.0;
  } else {
    dustDensity = 0;
  }
  
  return dustDensity;
}

int measureGas() {
  // Считывание аналогового значения с датчика MQ135
  int value = analogRead(gasPin);
  return value;
}

int measureMethane() {
  // Считывание аналогового значения с датчика MQ-4 (метан)
  int value = analogRead(methanePin);
  return value;
}

int measureCO() {
  // Считывание аналогового значения с датчика MQ-7 (угарный газ)
  int value = analogRead(coPin);
  return value;
}

void calculatePercentages(float dustLevel, int gasLevel, int methaneLevel, int coLevel, float humidity, float temperature) {
  // Расчет процентных отклонений для пыли
  if (dustLevel > dustThreshold) {
    dustPercentage = (dustLevel / dustThreshold) * 100.0 - 100.0;
    dustAlarm = true;
  } else {
    dustPercentage = 0;
    dustAlarm = false;
  }
  
  // Расчет процентных отклонений для газа
  if (gasLevel > gasThreshold) {
    gasPercentage = (float(gasLevel) / gasThreshold) * 100.0 - 100.0;
    gasAlarm = true;
  } else {
    gasPercentage = 0;
    gasAlarm = false;
  }
  
  // Расчет процентных отклонений для метана
  if (methaneLevel > methaneThreshold) {
    methanePercentage = (float(methaneLevel) / methaneThreshold) * 100.0 - 100.0;
    methaneAlarm = true;
  } else {
    methanePercentage = 0;
    methaneAlarm = false;
  }
  
  // Расчет процентных отклонений для CO
  if (coLevel > coThreshold) {
    coPercentage = (float(coLevel) / coThreshold) * 100.0 - 100.0;
    coAlarm = true;
  } else {
    coPercentage = 0;
    coAlarm = false;
  }
  
  // Расчет процентных отклонений для влажности
  if (humidity < minHumidity) {
    humidityPercentage = (minHumidity - humidity) / minHumidity * 100.0;
    humidityAlarm = true;
  } else if (humidity > maxHumidity) {
    humidityPercentage = (humidity - maxHumidity) / maxHumidity * 100.0;
    humidityAlarm = true;
  } else {
    humidityPercentage = 0;
    humidityAlarm = false;
  }
  
  // Расчет процентных отклонений для температуры
  if (temperature < minTemperature) {
    temperaturePercentage = (minTemperature - temperature) / minTemperature * 100.0;
    temperatureAlarm = true;
  } else if (temperature > maxTemperature) {
    temperaturePercentage = (temperature - maxTemperature) / maxTemperature * 100.0;
    temperatureAlarm = true;
  } else {
    temperaturePercentage = 0;
    temperatureAlarm = false;
  }
}

void updateIndicators(float dustLevel, int gasLevel, int methaneLevel, int coLevel, float humidity, float temperature) {
  bool alarmState = false;
  bool gasTypeAlarm = false;  // Флаг тревоги связанной с любым видом газа
  
  // Проверка всех параметров на тревогу
  if (dustAlarm || gasAlarm || methaneAlarm || coAlarm || humidityAlarm || temperatureAlarm) {
    alarmState = true;
  }
  
  // Проверка специально для газовых тревог (включая метан и CO)
  if (gasAlarm || methaneAlarm || coAlarm) {
    gasTypeAlarm = true;
  }
  
  // Определение цвета RGB в зависимости от всех показателей
  if (!alarmState && dustLevel < dustThreshold * 0.7 && 
      gasLevel < gasThreshold * 0.7 && 
      methaneLevel < methaneThreshold * 0.7 && 
      coLevel < coThreshold * 0.7) {
    // Хорошее качество воздуха и нормальные условия - зеленый
    setColor(0, 255, 0);
  } else if (!dustAlarm && !gasTypeAlarm && (humidityAlarm || temperatureAlarm)) {
    // Только проблемы с влажностью/температурой - синий
    setColor(155, 0, 255);
  } else if (dustLevel < dustThreshold && 
           gasLevel < gasThreshold &&
           methaneLevel < methaneThreshold &&
           coLevel < coThreshold) {
    // Среднее качество воздуха - желтый
    setColor(255, 155, 0);
  } else {
    // Плохое качество воздуха - красный
    setColor(255, 0, 0);
  }
  
  // Активация зуммера при тревоге, если не в беззвучном режиме
  if (alarmState && !silentMode) {
    // Опасность CO выше всего - наивысший приоритет сигнала
    if (coAlarm) {
      // Быстрый тройной звуковой сигнал для CO
      int currentMillis = millis() % 1500;
      if (currentMillis < 100) {
        tone(buzzerPin, 1500);
      } else if (currentMillis < 200) {
        noTone(buzzerPin);
      } else if (currentMillis < 300) {
        tone(buzzerPin, 1500);
      } else if (currentMillis < 400) {
        noTone(buzzerPin);
      } else if (currentMillis < 500) {
        tone(buzzerPin, 1500);
      } else {
        noTone(buzzerPin);
      }
    }
    // Затем метан - следующий по приоритету
    else if (methaneAlarm) {
      // Двойной звуковой сигнал для метана
      int currentMillis = millis() % 1200;
      if (currentMillis < 100) {
        tone(buzzerPin, 1200);
      } else if (currentMillis < 200) {
        noTone(buzzerPin);
      } else if (currentMillis < 300) {
        tone(buzzerPin, 1200);
      } else {
        noTone(buzzerPin);
      }
    }
    // Остальные газы и пыль
    else if (dustAlarm || gasAlarm) {
      // Быстрый прерывистый сигнал для газа/пыли
      int currentMillis = millis();
      if ((currentMillis % 1000) < 500) {
        tone(buzzerPin, 1000);
      } else {
        noTone(buzzerPin);
      }
    } 
    // Низший приоритет - влажность/температура
    else {
      // Медленный прерывистый сигнал для влажности/температуры
      int currentMillis = millis();
      if ((currentMillis % 2000) < 1000) {
        tone(buzzerPin, 800);
      } else {
        noTone(buzzerPin);
      }
    }
  } else {
    noTone(buzzerPin);     // Выключаем зуммер
  }
}

void setColor(int red, int green, int blue) {
  // Установка цвета RGB светодиода
  analogWrite(redPin, red);
  analogWrite(greenPin, green);
  analogWrite(bluePin, blue);
}

void sendDataToComputer(float dustLevel, int gasLevel, int methaneLevel, int coLevel, float humidity, float temperature) {
  // Формат: DATA:пыль,газ,метан,CO,влажность,температура,статус_тревог
  Serial.print("DATA:");
  Serial.print(dustLevel);
  Serial.print(",");
  Serial.print(gasLevel);
  Serial.print(",");
  Serial.print(methaneLevel);
  Serial.print(",");
  Serial.print(coLevel);
  Serial.print(",");
  Serial.print(humidity);
  Serial.print(",");
  Serial.print(temperature);
  Serial.print(",");
  
  // Добавляем информацию о тревогах и процентах отклонения
  if (dustAlarm) {
    Serial.print("DUST:");
    Serial.print(dustPercentage);
    Serial.print("%,");
  }
  
  if (gasAlarm) {
    Serial.print("GAS:");
    Serial.print(gasPercentage);
    Serial.print("%,");
  }
  
  if (methaneAlarm) {
    Serial.print("METHANE:");
    Serial.print(methanePercentage);
    Serial.print("%,");
  }
  
  if (coAlarm) {
    Serial.print("CO:");
    Serial.print(coPercentage);
    Serial.print("%,");
  }
  
  if (humidityAlarm) {
    Serial.print("HUMIDITY:");
    Serial.print(humidityPercentage);
    Serial.print("%,");
  }
  
  if (temperatureAlarm) {
    Serial.print("TEMP:");
    Serial.print(temperaturePercentage);
    Serial.print("%,");
  }
  
  if (!dustAlarm && !gasAlarm && !methaneAlarm && !coAlarm && !humidityAlarm && !temperatureAlarm) {
    Serial.print("NORMAL");
  }
  Serial.println();
}

void processCommand(String command) {
  // Обработка команд от компьютера
  if (command == "REQUEST_DATA") {
    // Запрос на получение текущих данных
    float dustDensity = measureDust();
    int gasValue = measureGas();
    int methaneValue = measureMethane();
    int coValue = measureCO();
    readDHTSensor();
    calculatePercentages(dustDensity, gasValue, methaneValue, coValue, humidity, temperature);
    sendDataToComputer(dustDensity, gasValue, methaneValue, coValue, humidity, temperature);
  }
  else if (command == "TOGGLE_SILENT") {
    // Переключение беззвучного режима
    silentMode = !silentMode;
    Serial.print("SILENT_MODE:");
    Serial.println(silentMode ? "ON" : "OFF");
  }
  else if (command.startsWith("SET_THRESHOLDS:")) {
    // Формат: SET_THRESHOLDS:dust,gas,co,methane,humidity_min,humidity_max,temp_min,temp_max
    String data = command.substring(14); // Пропускаем "SET_THRESHOLDS:"
    
    // Разбиваем строку на значения
    int index = 0;
    float values[8];
    
    // Временная переменная для хранения текущего значения
    String currentValue = "";
    
    // Проходим по всей строке
    for (int i = 0; i < data.length(); i++) {
      if (data[i] == ',' || i == data.length() - 1) {
        // Если последний символ, добавляем его
        if (i == data.length() - 1) {
          currentValue += data[i];
        }
        
        // Преобразуем строку в число
        values[index] = currentValue.toFloat();
        index++;
        currentValue = "";
      } else {
        currentValue += data[i];
      }
    }
    
    // Проверяем, что получили все 8 значений
    if (index == 8) {
      // Применяем новые пороги
      dustThreshold = values[0];
      gasThreshold = (int)values[1];
      coThreshold = (int)values[2];
      methaneThreshold = (int)values[3];
      minHumidity = values[4];
      maxHumidity = values[5];
      minTemperature = values[6];
      maxTemperature = values[7];
      
      // Отправляем подтверждение
      Serial.println("THRESHOLDS_UPDATED");
    } else {
      Serial.println("ERROR:INVALID_THRESHOLD_FORMAT");
    }
  }
}
