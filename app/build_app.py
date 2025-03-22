import PyInstaller.__main__
import os
import shutil

# Очистка папки dist если она существует
if os.path.exists('dist'):
    shutil.rmtree('dist')

# Конфигурация сборки
PyInstaller.__main__.run([
    'src/air_quality_monitor2.py',  # Основной файл приложения
    '--name=AirPro',  # Имя исполняемого файла
    '--windowed',  # Без консольного окна
    '--onefile',  # Один исполняемый файл
    '--icon=assets/icon.ico',  # Иконка приложения
    '--add-data=assets;assets',  # Добавление ресурсов
    '--hidden-import=pandas',  # Скрытые зависимости
    '--hidden-import=openpyxl',
    '--hidden-import=requests',
    '--clean',  # Очистка временных файлов
    '--noconfirm',  # Без подтверждения перезаписи
])

# Копирование собранного файла в папку assets для веб-сайта
if not os.path.exists('website/assets'):
    os.makedirs('website/assets')

shutil.copy2('dist/AirPro.exe', 'website/assets/AirPro.exe')
print("Сборка завершена. Исполняемый файл создан в website/assets/AirPro.exe") 