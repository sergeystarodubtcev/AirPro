import PyInstaller.__main__
import os

# Получаем путь к текущей директории
current_dir = os.path.dirname(os.path.abspath(__file__))

# Определяем путь к main.py
main_path = os.path.join(current_dir, 'main.py')

# Определяем путь к иконке
icon_path = os.path.join(current_dir, 'assets', 'icon.ico')

# Настройки компиляции
PyInstaller.__main__.run([
    main_path,
    '--name=AirPro',
    '--onefile',
    '--windowed',
    f'--icon={icon_path}',
    '--add-data=assets;assets',
    '--add-data=src;src',
    '--add-data=config;config',
    '--add-data=scripts;scripts',
    '--clean',
    '--noconfirm'
]) 