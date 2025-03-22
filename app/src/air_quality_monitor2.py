import tkinter as tk
from tkinter import messagebox, scrolledtext
import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import queue
import numpy as np
import requests
import json
from collections import deque
import os
import sys
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
from matplotlib.figure import Figure
from matplotlib import rcParams
import webbrowser
import pandas as pd
from .export_to_excel import add_export_button
from .air_quality_profiles import AIR_QUALITY_PROFILES, get_profile, update_custom_profile, get_arduino_command
from .settings_window import SettingsWindow
from .thingspeak_integration import ThingSpeakIntegration
from .config.api_keys import (
    THINGSPEAK_CHANNEL_ID,
    THINGSPEAK_READ_API_KEY,
    THINGSPEAK_WRITE_API_KEY
)

# Настройка глобального вида для matplotlib
plt.style.use('ggplot')
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']

# Константы
MAX_DATA_POINTS = 100  # Максимальное количество точек на графике
MAX_DATA_POINTS = 100  # Максимальное количество точек на графике
TELEGRAM_BOT_TOKEN = "7577951456:AAHpZoN_3WW6fmi_In2fdxMBZU_YHN-nwrc"  # Вставьте свой токен бота
OPENROUTER_API_KEY = "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"  # Вставьте свой ключ OpenRouter

# Настройка темы для CustomTkinter
ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ToolTip:
    """
    Создает всплывающую подсказку для виджета
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
    
    def on_enter(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        
        # Создаем окно подсказки
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                         background="#ffffff", relief=tk.SOLID, borderwidth=1,
                         font=("Arial", "10", "normal"), padx=5, pady=2)
        label.pack(side=tk.TOP, fill=tk.BOTH)
    
    def on_leave(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class RoundedButton(ctk.CTkButton):
    """
    Кастомная кнопка с закругленными краями
    """
    def __init__(self, *args, **kwargs):
        # Устанавливаем фиксированные размеры для всех кнопок
        kwargs["width"] = 200  # Фиксированная ширина
        kwargs["height"] = 36  # Фиксированная высота
        super().__init__(*args, **kwargs)
        self.configure(
            corner_radius=10,
            border_width=0,
            hover=True,
            fg_color="#0078D7",
            hover_color="#005A9E",
            text_color="#FFFFFF"
        )

class CircularProgressBar(ctk.CTkFrame):
    """
    Кругловой индикатор прогресса
    """
    def __init__(self, master, value=0, maximum=100, radius=50, bg_color="#F0F0F0", 
                 fg_color="#0078D7", text_color="#000000", **kwargs):
        super().__init__(master, **kwargs)
        
        self.value = value
        self.maximum = maximum
        self.radius = radius
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text_color = text_color
        
        self.canvas = tk.Canvas(
            self, 
            width=self.radius*2, 
            height=self.radius*2,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.TOP, padx=5, pady=5)
        
        # Фоновый круг (серый)
        self.canvas.create_arc(
            4, 4, 
            2*self.radius-4, 2*self.radius-4, 
            start=90, 
            extent=359.9,
            fill=self.bg_color, 
            outline="#D0D0D0", 
            width=8,
            style="pieslice",
            tags="bg_circle"
        )
        
        # Прогресс круг (цветной)
        self.canvas.create_arc(
            4, 4, 
            2*self.radius-4, 2*self.radius-4, 
            start=90, 
            extent=-self.value/self.maximum*360, 
            fill=self.fg_color, 
            outline=self.fg_color, 
            width=8, 
            style="pieslice",
            tags="progress"
        )
        
        # Текст значения
        self.canvas.create_text(
            self.radius,
            self.radius,
            text=f"{int(self.value)}",
            font=("Arial", 18, "bold"),
            fill=self.text_color,
            tags="text"
        )
        
        # Метка единиц измерения
        self.label = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.label.pack(side=tk.BOTTOM)
    
    def set_value(self, value, unit="", color=None):
        """Обновление значения прогресса"""
        # Ограничиваем значение максимумом
        self.value = min(value, self.maximum)
        
        # Обновляем фоновый круг с цветовой обводкой
        self.canvas.delete("bg_circle")
        self.canvas.create_arc(
            4, 4, 
            2*self.radius-4, 2*self.radius-4, 
            start=90, 
            extent=359.9,
            fill=self.bg_color, 
            outline=color if color else "#D0D0D0", 
            width=8,
            style="pieslice",
            tags="bg_circle"
        )
        
        # Обновляем дугу прогресса
        self.canvas.delete("progress")
        self.canvas.create_arc(
            4, 4, 
            2*self.radius-4, 2*self.radius-4, 
            start=90, 
            extent=-self.value/self.maximum*360, 
            fill=color if color else self.fg_color, 
            outline=color if color else self.fg_color, 
            width=8, 
            style="pieslice",
            tags="progress"
        )
        
        # Обновляем текст
        self.canvas.delete("text")
        self.canvas.create_text(
            self.radius,
            self.radius,
            text=f"{int(self.value)}",
            font=("Arial", 18, "bold"),
            fill=self.text_color,
            tags="text"
        )
        
        # Обновляем единицы измерения
        self.label.configure(text=unit)

class AirQualityMonitor(ctk.CTk):
    def __init__(self, port=None):
        super().__init__()
        
        self.title("Мониторинг качества воздуха")
        self.geometry("1200x900")  # Увеличиваем высоту окна
        self.minsize(1000, 800)    # Увеличиваем минимальную высоту
        
        # Переменные для данных датчиков
        self.dust_level = 0.0
        self.gas_level = 0
        self.co_level = 0
        self.methane_level = 0
        self.humidity = 0.0
        self.temperature = 0.0
        self.silent_mode = False
        self.alerts = []
        self.last_alert_status = False
        self.last_ai_update_time = 0
        self.significant_change = False
        self.auto_update_active = False  # Добавляем переменную для отслеживания состояния автообновления
        
        # Данные для графиков
        self.timestamps = deque(maxlen=MAX_DATA_POINTS)
        self.dust_data = deque(maxlen=MAX_DATA_POINTS)
        self.gas_data = deque(maxlen=MAX_DATA_POINTS)
        self.co_data = deque(maxlen=MAX_DATA_POINTS)
        self.methane_data = deque(maxlen=MAX_DATA_POINTS)
        self.humidity_data = deque(maxlen=MAX_DATA_POINTS)
        self.temp_data = deque(maxlen=MAX_DATA_POINTS)
        
        # Для взаимодействия с потоками
        self.data_queue = queue.Queue()
        self.running = False
        self.serial_connection = None
        self.ai_recommendation = "Для получения рекомендаций нажмите кнопку 'Запросить рекомендации ИИ'"
        
        # Загрузка изображений для иконок (позже)
        self.load_icons()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Инициализация ThingSpeak
        self.thingspeak = ThingSpeakIntegration(self)
        
        # Если порт передан, подключаемся к нему
        if port:
            self.connect_to_port(port)
        
        # Список доступных COM портов
        self.refresh_ports()
        
        # Подсказка о необходимости подключения
        self.connection_reminder()

    def load_icons(self):
        """Загрузка иконок для интерфейса"""
        def create_material_icon(main_color, icon_type, size=(24, 24)):
            # Создаем изображение с прозрачным фоном
            img = Image.new('RGBA', size, color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Конвертируем hex в RGB
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            main_rgb = hex_to_rgb(main_color)
            
            # Создаем градиент (более темный оттенок для нижней части)
            darker_rgb = tuple(max(0, c - 40) for c in main_rgb)
            
            # Рисуем основной круг с градиентом
            padding = 2
            for y in range(size[1]):
                progress = y / size[1]
                current_color = tuple(
                    int(main_rgb[i] * (1 - progress) + darker_rgb[i] * progress)
                    for i in range(3)
                )
                draw.ellipse(
                    [padding, y, size[0]-padding, y+1],
                    fill=current_color + (255,)
                )
            
            # Добавляем блик (верхний полукруг)
            highlight = Image.new('RGBA', size, color=(0, 0, 0, 0))
            highlight_draw = ImageDraw.Draw(highlight)
            highlight_draw.ellipse(
                [padding+2, padding+2, size[0]-padding-2, size[1]//2],
                fill=(255, 255, 255, 40)
            )
            img = Image.alpha_composite(img, highlight)
            
            # Рисуем иконку
            icon_color = (255, 255, 255, 255)  # Белый цвет для иконки
            icon_size = size[0] - 2 * padding - 4
            icon_box = [(size[0] - icon_size) // 2, (size[1] - icon_size) // 2,
                       (size[0] + icon_size) // 2, (size[1] + icon_size) // 2]
            
            if icon_type == "connect":
                # Рисуем символ подключения (стилизованная вилка)
                points = [
                    (icon_box[0] + icon_size//3, icon_box[1]),
                    (icon_box[2] - icon_size//3, icon_box[1]),
                    (icon_box[2], icon_box[1] + icon_size//2),
                    (icon_box[2] - icon_size//3, icon_box[3]),
                    (icon_box[0] + icon_size//3, icon_box[3]),
                    (icon_box[0], icon_box[1] + icon_size//2),
                ]
                draw.polygon(points, fill=icon_color)
            
            elif icon_type == "disconnect":
                # Рисуем символ отключения (крестик)
                line_width = 2
                draw.line([icon_box[0], icon_box[1], icon_box[2], icon_box[3]], fill=icon_color, width=line_width)
                draw.line([icon_box[2], icon_box[1], icon_box[0], icon_box[3]], fill=icon_color, width=line_width)
            
            elif icon_type == "refresh":
                # Рисуем символ обновления (круговая стрелка)
                arrow_points = [
                    (icon_box[0] + icon_size//4, icon_box[1] + icon_size//4),
                    (icon_box[2] - icon_size//4, icon_box[1] + icon_size//4),
                    (icon_box[2] - icon_size//4, icon_box[3] - icon_size//4),
                    (icon_box[0] + icon_size//4, icon_box[3] - icon_size//4)
                ]
                draw.arc(icon_box, 0, 270, fill=icon_color, width=2)
                draw.polygon([
                    arrow_points[2],
                    (arrow_points[2][0] + 4, arrow_points[2][1] - 4),
                    (arrow_points[2][0] - 4, arrow_points[2][1] - 4)
                ], fill=icon_color)
            
            elif icon_type == "settings":
                # Рисуем символ настроек (шестеренка)
                center = ((icon_box[0] + icon_box[2])//2, (icon_box[1] + icon_box[3])//2)
                r1 = icon_size//3  # внешний радиус
                r2 = icon_size//4  # внутренний радиус
                points = []
                for i in range(8):
                    angle = i * (360/8) * (3.14159/180)
                    points.append((
                        center[0] + int(r1 * np.cos(angle)),
                        center[1] + int(r1 * np.sin(angle))
                    ))
                    points.append((
                        center[0] + int(r2 * np.cos(angle + 360/16 * (3.14159/180))),
                        center[1] + int(r2 * np.sin(angle + 360/16 * (3.14159/180)))
                    ))
                draw.polygon(points, fill=icon_color)
                draw.ellipse([center[0]-3, center[1]-3, center[0]+3, center[1]+3], fill=main_rgb)
            
            elif icon_type == "alert":
                # Рисуем символ тревоги (восклицательный знак в треугольнике)
                points = [
                    (icon_box[0] + icon_size//2, icon_box[1]),
                    (icon_box[2], icon_box[3]),
                    (icon_box[0], icon_box[3])
                ]
                draw.polygon(points, fill=icon_color)
                draw.line([
                    (icon_box[0] + icon_size//2, icon_box[1] + icon_size//4),
                    (icon_box[0] + icon_size//2, icon_box[1] + icon_size//1.5)
                ], fill=main_rgb, width=2)
                draw.ellipse([
                    icon_box[0] + icon_size//2 - 1,
                    icon_box[1] + icon_size//1.3,
                    icon_box[0] + icon_size//2 + 1,
                    icon_box[1] + icon_size//1.3 + 2
                ], fill=main_rgb)
            
            elif icon_type == "silent":
                # Рисуем символ без звука (перечеркнутый динамик)
                speaker = [
                    (icon_box[0], icon_box[1] + icon_size//3),
                    (icon_box[0] + icon_size//3, icon_box[1] + icon_size//3),
                    (icon_box[2] - icon_size//4, icon_box[1]),
                    (icon_box[2] - icon_size//4, icon_box[3]),
                    (icon_box[0] + icon_size//3, icon_box[3] - icon_size//3),
                    (icon_box[0], icon_box[3] - icon_size//3)
                ]
                draw.polygon(speaker, fill=icon_color)
                draw.line([
                    (icon_box[0], icon_box[1]),
                    (icon_box[2], icon_box[3])
                ], fill=icon_color, width=2)
            
            return ImageTk.PhotoImage(img)
        
        # Создаем иконки с разными цветами
        self.icon_connect = create_material_icon("#4CAF50", "connect")      # Зеленый для подключения
        self.icon_disconnect = create_material_icon("#F44336", "disconnect") # Красный для отключения
        self.icon_refresh = create_material_icon("#2196F3", "refresh")      # Синий для обновления
        self.icon_settings = create_material_icon("#757575", "settings")    # Серый для настроек
        self.icon_alert = create_material_icon("#FF9800", "alert")         # Оранжевый для тревоги
        self.icon_silent = create_material_icon("#9C27B0", "silent")       # Фиолетовый для беззвучного режима

    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        # Основной контейнер
        self.main_container = ctk.CTkFrame(self, corner_radius=0)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель управления
        self.create_top_panel()
        
        # Основное содержимое
        content_frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Добавляем три колонки
        self.create_left_panel(content_frame)
        self.create_center_panel(content_frame)
        self.create_right_panel(content_frame)
        
        # Нижняя панель с логами
        self.create_log_panel()
        
        # Статусная строка
        self.create_status_bar()

    def create_top_panel(self):
        """Создание верхней панели с элементами управления подключением"""
        top_frame = ctk.CTkFrame(self.main_container, corner_radius=10, height=60)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Не растягивать frame по вертикали
        top_frame.pack_propagate(False)
        
        # Заголовок с иконкой
        title_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_frame.pack(side=tk.LEFT, padx=(15, 0))
        
        label = ctk.CTkLabel(
            title_frame, 
            text="Мониторинг качества воздуха", 
            font=("Arial", 18, "bold")
        )
        label.pack(side=tk.LEFT, padx=5)
        
        # Разделитель
        separator = ctk.CTkFrame(top_frame, width=2, fg_color="#E0E0E0")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=10)
        
        # Выбор COM-порта
        port_label = ctk.CTkLabel(top_frame, text="COM порт:")
        port_label.pack(side=tk.LEFT, padx=5)
        
        self.port_combo = ctk.CTkComboBox(top_frame, width=120)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        
        # Кнопка автообновления данных с сервером
        self.auto_update_button = RoundedButton(
            top_frame, 
            text="Автообновление выкл.",
            width=200,
            image=self.icon_refresh,
            command=self.toggle_auto_update
        )
        self.auto_update_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопки подключения/отключения
        self.connect_button = RoundedButton(
            top_frame, 
            text="Подключиться",
            width=120,
            image=self.icon_connect,
            command=self.connect_serial
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_button = RoundedButton(
            top_frame, 
            text="Отключиться",
            width=120,
            image=self.icon_disconnect,
            command=self.disconnect_serial
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка настроек (справа)
        settings_button = ctk.CTkButton(
            top_frame,
            text="Настройки",
            image=self.icon_settings,
            width=120,
            height=36,
            corner_radius=10,
            command=self.show_settings
        )
        settings_button.pack(side=tk.RIGHT, padx=10)
        
        # Добавляем подсказку для кнопки настроек
        ToolTip(settings_button, "Настройки приложения")

    def create_left_panel(self, parent):
        """Создание левой панели с индикаторами датчиков"""
        left_frame = ctk.CTkFrame(parent, corner_radius=10, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5), pady=5)
        
        # Заголовок
        header = ctk.CTkLabel(
            left_frame, 
            text="Текущие показания", 
            font=("Arial", 16, "bold"),
            anchor="center"
        )
        header.pack(pady=(15, 20), padx=10)
        
        # Контейнер для индикаторов
        gauges_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        gauges_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=0)
        
        # Создаем фреймы для каждой пары индикаторов
        for i in range(3):
            row_frame = ctk.CTkFrame(gauges_frame, fg_color="transparent")
            row_frame.pack(fill=tk.X, pady=5)
            
            # Левая колонка
            left_col = ctk.CTkFrame(row_frame, fg_color="transparent")
            left_col.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            
            # Правая колонка
            right_col = ctk.CTkFrame(row_frame, fg_color="transparent")
            right_col.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            
            if i == 0:  # Первый ряд: Пыль и Газ
                # Пыль
                dust_label = ctk.CTkLabel(left_col, text="Уровень пыли", font=("Arial", 14, "bold"))
                dust_label.pack(anchor="center")
                
                self.dust_gauge = CircularProgressBar(
                    left_col, value=0, maximum=150,  # Увеличиваем максимум для пыли
                    radius=50, fg_color="#0000FF"  # Синий
                )
                self.dust_gauge.pack(pady=0)
                self.dust_gauge.set_value(0, "мкг/м³")
                
                # Газ
                gas_label = ctk.CTkLabel(right_col, text="Уровень газа", font=("Arial", 14, "bold"))
                gas_label.pack(anchor="center")
                
                self.gas_gauge = CircularProgressBar(
                    right_col, value=0, maximum=1000,  # Увеличиваем максимум для газа
                    radius=50, fg_color="#FF9800"  # Оранжевый
                )
                self.gas_gauge.pack(pady=0)
                self.gas_gauge.set_value(0, "ppm")
                
            elif i == 1:  # Второй ряд: Влажность и Температура
                # Влажность
                humidity_label = ctk.CTkLabel(left_col, text="Влажность", font=("Arial", 14, "bold"))
                humidity_label.pack(anchor="center")
                
                self.humidity_gauge = CircularProgressBar(
                    left_col, value=0, maximum=100,
                    radius=50, fg_color="#2196F3"  # Синий
                )
                self.humidity_gauge.pack(pady=0)
                self.humidity_gauge.set_value(0, "%")
                
                # Температура
                temp_label = ctk.CTkLabel(right_col, text="Температура", font=("Arial", 14, "bold"))
                temp_label.pack(anchor="center")
                
                self.temp_gauge = CircularProgressBar(
                    right_col, value=0, maximum=40,
                    radius=50, fg_color="#4CAF50"  # Зеленый
                )
                self.temp_gauge.pack(pady=0)
                self.temp_gauge.set_value(0, "°C")
                
            else:  # Третий ряд: CO и Метан
                # CO
                co_label = ctk.CTkLabel(left_col, text="Уровень CO", font=("Arial", 14, "bold"))
                co_label.pack(anchor="center")
                
                self.co_gauge = CircularProgressBar(
                    left_col, value=0, maximum=650,  # Увеличиваем максимум для CO на 200
                    radius=50, fg_color="#E91E63"  # Розовый
                )
                self.co_gauge.pack(pady=0)
                self.co_gauge.set_value(0, "ppm")
                
                # Метан
                methane_label = ctk.CTkLabel(right_col, text="Уровень метана", font=("Arial", 14, "bold"))
                methane_label.pack(anchor="center")
                
                self.methane_gauge = CircularProgressBar(
                    right_col, value=0, maximum=900,  # Увеличиваем максимум для метана на 200
                    radius=50, fg_color="#9C27B0"  # Фиолетовый
                )
                self.methane_gauge.pack(pady=0)
                self.methane_gauge.set_value(0, "ppm")
        
        # Статус беззвучного режима
        silent_frame = ctk.CTkFrame(left_frame, height=40, fg_color="#F5F5F5", corner_radius=10)
        silent_frame.pack(fill=tk.X, pady=10, padx=10)
        
        silent_label = ctk.CTkLabel(silent_frame, text="Беззвучный режим:")
        silent_label.pack(side=tk.LEFT, padx=10)
        
        self.silent_var = tk.StringVar(value="ВЫКЛ")
        silent_status = ctk.CTkLabel(
            silent_frame, 
            textvariable=self.silent_var, 
            font=("Arial", 12, "bold"),
            text_color="#F44336"  # По умолчанию красный (ВЫКЛ)
        )
        silent_status.pack(side=tk.RIGHT, padx=10)
        

    def create_center_panel(self, parent):
        """Создание центральной панели с графиками"""
        center_frame = ctk.CTkFrame(parent, corner_radius=10)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Заголовок
        header = ctk.CTkLabel(
            center_frame, 
            text="Графики мониторинга", 
            font=("Arial", 16, "bold"),
            anchor="center"
        )
        header.pack(pady=(15, 5), padx=10)
        
        # Контейнер для графиков
        charts_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Создание графиков с использованием matplotlib
        self.create_plots(charts_frame)

    def create_right_panel(self, parent):
        """Создание правой панели с тревогами и рекомендациями"""
        right_frame = ctk.CTkFrame(parent, corner_radius=10, width=300)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0), pady=5)
        
        # Заголовок для тревог
        alerts_header = ctk.CTkLabel(
            right_frame, 
            text="Активные тревоги", 
            font=("Arial", 16, "bold"),
            anchor="center"
        )
        alerts_header.pack(pady=(15, 5), padx=10)
        
        # Список тревог
        alerts_container = ctk.CTkFrame(right_frame, fg_color="#F9F9F9", corner_radius=10)
        alerts_container.pack(fill=tk.X, padx=10, pady=5)
        
        self.alerts_text = scrolledtext.ScrolledText(
            alerts_container, 
            width=30, 
            height=10, 
            wrap=tk.WORD,
            font=("Arial", 11),
            background="#F9F9F9",
            borderwidth=0
        )
        self.alerts_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Заголовок для рекомендаций ИИ
        ai_header = ctk.CTkLabel(
            right_frame, 
            text="Рекомендации ИИ", 
            font=("Arial", 16, "bold"),
            anchor="center"
        )
        ai_header.pack(pady=(15, 5), padx=10)
        
        # Контейнер для рекомендаций
        ai_container = ctk.CTkFrame(right_frame, fg_color="#F9F9F9", corner_radius=10)
        ai_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.ai_text = scrolledtext.ScrolledText(
            ai_container, 
            width=30, 
            height=10, 
            wrap=tk.WORD,
            font=("Arial", 11),
            background="#F9F9F9",
            borderwidth=0
        )
        self.ai_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ai_text.insert(tk.END, self.ai_recommendation)
        self.ai_text.config(state=tk.DISABLED)
        
        # Кнопки управления
        self.buttons_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Кнопка переключения беззвучного режима
        self.toggle_silent_button = RoundedButton(
            self.buttons_frame,
            text="🔊 Звук включен",
            command=self.toggle_silent_mode,
            width=200
        )
        self.toggle_silent_button.pack(fill=tk.X, pady=(0, 5))
        
        # Кнопка запроса рекомендаций
        ai_button = RoundedButton(
            self.buttons_frame,
            text="Запросить рекомендации ИИ",
            command=self.request_ai_recommendation,
            width=200
        )
        ai_button.pack(fill=tk.X, pady=5)
        
        # Добавляем кнопку экспорта в Excel
        add_export_button(self)

    def create_log_panel(self):
        """Создание нижней панели с логами"""
        log_frame = ctk.CTkFrame(self, corner_radius=10)
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Заголовок с кнопкой показа/скрытия
        header_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        log_header = ctk.CTkLabel(
            header_frame, 
            text="Журнал событий", 
            font=("Arial", 14, "bold")
        )
        log_header.pack(side=tk.LEFT)
        
        # Кнопка показа/скрытия логов
        self.show_logs_var = tk.BooleanVar(value=True)
        self.toggle_logs_button = ctk.CTkButton(
            header_frame,
            text="Скрыть логи",
            width=100,
            command=self.toggle_logs_visibility
        )
        self.toggle_logs_button.pack(side=tk.RIGHT)
        
        # Текстовое поле для логов
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=3,  # Уменьшаем высоту поля логов
            font=("Consolas", 10),
            background="#F9F9F9",
            borderwidth=0
        )
        self.log_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
    def toggle_logs_visibility(self):
        """Переключение видимости панели логов"""
        if self.show_logs_var.get():
            self.log_text.pack_forget()
            self.toggle_logs_button.configure(text="Показать логи")
            self.show_logs_var.set(False)
        else:
            self.log_text.pack(fill=tk.X, padx=10, pady=(0, 10))
            self.toggle_logs_button.configure(text="Скрыть логи")
            self.show_logs_var.set(True)

    def create_status_bar(self):
        """Создание статусной строки"""
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Индикатор статуса
        self.status_var = tk.StringVar()
        self.status_var.set("Статус: не подключен")
        
        status_label = ctk.CTkLabel(
            status_frame, 
            textvariable=self.status_var,
            font=("Arial", 11),
            text_color="#666666"
        )
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Информация о версии справа
        version_label = ctk.CTkLabel(
            status_frame, 
            text="v1.0.0",
            font=("Arial", 11),
            text_color="#666666"
        )
        version_label.pack(side=tk.RIGHT, padx=10)

    def create_plots(self, parent):
        """Создание графиков с использованием matplotlib"""
        # Создаем фигуру с шестью графиками (3x2)
        self.fig = Figure(figsize=(8, 9), dpi=100)
        self.fig.subplots_adjust(bottom=0.1, hspace=0.4, wspace=0.3)
        
        # Создаем 6 отдельных графиков
        self.ax1 = self.fig.add_subplot(321)  # Пыль
        self.ax2 = self.fig.add_subplot(322)  # Газ
        self.ax3 = self.fig.add_subplot(323)  # CO
        self.ax4 = self.fig.add_subplot(324)  # Метан
        self.ax5 = self.fig.add_subplot(325)  # Влажность
        self.ax6 = self.fig.add_subplot(326)  # Температура
        
        # График для пыли
        self.dust_line, = self.ax1.plot([], [], 'b-', linewidth=2)
        self.ax1.set_ylabel('мкг/м³')
        self.ax1.set_title('Пыль')
        self.ax1.grid(True, linestyle='--', alpha=0.7)
        
        # График для газа
        self.gas_line, = self.ax2.plot([], [], 'r-', linewidth=2)
        self.ax2.set_ylabel('ppm')
        self.ax2.set_title('Газ')
        self.ax2.grid(True, linestyle='--', alpha=0.7)
        
        # График для CO
        self.co_line, = self.ax3.plot([], [], 'y-', linewidth=2)
        self.ax3.set_ylabel('ppm')
        self.ax3.set_title('CO')
        self.ax3.grid(True, linestyle='--', alpha=0.7)
        
        # График для метана
        self.methane_line, = self.ax4.plot([], [], 'c-', linewidth=2)
        self.ax4.set_ylabel('ppm')
        self.ax4.set_title('Метан')
        self.ax4.grid(True, linestyle='--', alpha=0.7)
        
        # График для влажности
        self.humidity_line, = self.ax5.plot([], [], 'g-', linewidth=2)
        self.ax5.set_ylabel('%')
        self.ax5.set_title('Влажность')
        self.ax5.set_xlabel('Время')
        self.ax5.grid(True, linestyle='--', alpha=0.7)
        
        # График для температуры
        self.temp_line, = self.ax6.plot([], [], 'm-', linewidth=2)
        self.ax6.set_ylabel('°C')
        self.ax6.set_title('Температура')
        self.ax6.set_xlabel('Время')
        self.ax6.grid(True, linestyle='--', alpha=0.7)
        
        # Встраивание графика в Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

    def refresh_ports(self):
        """Обновление списка доступных портов"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.configure(values=ports)
        if ports:
            self.port_combo.set(ports[0])
        self.log("Обновлен список доступных портов")

    def connection_reminder(self):
        """Напоминание о необходимости подключения (если нет активного соединения)"""
        if not self.running:
            self.log("Подсказка: Выберите COM-порт и нажмите 'Подключиться' для начала работы")

    def show_settings(self):
        """Показать окно настроек приложения"""
        settings_window = SettingsWindow(self)
        settings_window.grab_set()  # Делаем окно модальным

    def connect_to_port(self, port):
        """Подключается к указанному порту"""
        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=1
            )
            self.running = True
            self.start_auto_update()
            self.log(f"Подключено к порту {port}")
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к порту {port}:\n{str(e)}")
            self.log(f"Ошибка подключения к порту {port}: {str(e)}")

    def connect_serial(self):
        """Подключение к выбранному COM-порту"""
        if self.running:
            messagebox.showwarning("Предупреждение", "Уже подключено!")
            return

        port = self.port_combo.get()
        if not port:
            messagebox.showerror("Ошибка", "Выберите COM порт!")
            return

        try:
            self.serial_connection = serial.Serial(port, 9600, timeout=1)
            self.running = True
            
            # Запуск потока чтения данных
            self.read_thread = threading.Thread(target=self.read_serial)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            # Запуск потока обработки данных
            self.process_thread = threading.Thread(target=self.process_data)
            self.process_thread.daemon = True
            self.process_thread.start()
            
            self.status_var.set(f"Статус: подключено к {port}")
            self.log(f"Подключено к {port}")
            
            # Запускаем автоматическое обновление данных
            self.start_auto_update()
            self.auto_update_button.configure(text="Автообновление вкл.")
            
            # Запускаем отправку данных на ThingSpeak
            self.thingspeak.start()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {str(e)}")
            self.log(f"Ошибка подключения: {str(e)}")

    def disconnect_serial(self):
        """Отключение от COM-порта"""
        if not self.running:
            messagebox.showwarning("Предупреждение", "Соединение не установлено!")
            return
        
        # Останавливаем автоматическое обновление
        self.stop_auto_update()
        self.auto_update_button.configure(text="Автообновление выкл.")
            
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
            
        self.status_var.set("Статус: отключено")
        self.log("Отключено от устройства")

        # Останавливаем отправку данных на ThingSpeak
        self.thingspeak.stop()

    def read_serial(self):
        """Поток для чтения данных с последовательного порта"""
        while self.running:
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    if self.serial_connection.in_waiting > 0:
                        data = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                        if data:
                            self.data_queue.put(data)
                    else:
                        # Небольшая пауза, если данных нет
                        time.sleep(0.1)
                else:
                    # Если соединение потеряно, пауза перед следующей попыткой
                    time.sleep(0.5)
            except serial.SerialException as e:
                self.log(f"Ошибка последовательного порта: {str(e)}")
                # Попробуем восстановить соединение
                try:
                    if self.serial_connection:
                        self.serial_connection.close()
                        time.sleep(1)
                        self.serial_connection.open()
                except:
                    pass
                time.sleep(1)
            except Exception as e:
                self.log(f"Ошибка чтения данных: {str(e)}")
                time.sleep(1)

    def process_data(self):
        """Поток для обработки данных из очереди"""
        while self.running:
            try:
                if not self.data_queue.empty():
                    data = self.data_queue.get()
                    self.after(0, lambda d=data: self._parse_data_internal(d))
                time.sleep(0.1)
            except Exception as e:
                self.log(f"Ошибка обработки данных: {str(e)}")
                time.sleep(0.1)

    def _parse_data_internal(self, data):
        """Внутренний метод для разбора данных, полученных с устройства"""
        try:
            if "DATA:" in data:
                # Формат: DATA:пыль,газ,метан,CO,влажность,температура,статус_тревог
                data_parts = data.split('DATA:')[1].split(',')
                
                if len(data_parts) >= 6:
                    try:
                        old_dust = self.dust_level
                        old_gas = self.gas_level
                        old_co = self.co_level
                        old_methane = self.methane_level
                        old_humidity = self.humidity
                        old_temperature = self.temperature
                        
                        self.dust_level = float(data_parts[0])
                        self.gas_level = int(data_parts[1])
                        self.methane_level = float(data_parts[2])
                        self.co_level = float(data_parts[3])
                        self.humidity = float(data_parts[4])
                        self.temperature = float(data_parts[5])
                        
                        # Проверка на значительные изменения для обновления рекомендаций ИИ
                        dust_change = abs(self.dust_level - old_dust) / max(1, old_dust) > 0.2
                        gas_change = abs(self.gas_level - old_gas) / max(1, old_gas) > 0.2
                        co_change = abs(self.co_level - old_co) / max(1, old_co) > 0.2
                        methane_change = abs(self.methane_level - old_methane) / max(1, old_methane) > 0.2
                        humidity_change = abs(self.humidity - old_humidity) / max(1, old_humidity) > 0.1
                        temp_change = abs(self.temperature - old_temperature) / max(1, old_temperature) > 0.1
                        
                        self.significant_change = dust_change or gas_change or co_change or methane_change or humidity_change or temp_change
                        
                        # Добавление данных для графиков
                        current_time = datetime.datetime.now().strftime('%H:%M:%S')
                        self.timestamps.append(current_time)
                        self.dust_data.append(self.dust_level)
                        self.gas_data.append(self.gas_level)
                        self.co_data.append(self.co_level)
                        self.methane_data.append(self.methane_level)
                        self.humidity_data.append(self.humidity)
                        self.temp_data.append(self.temperature)
                        
                        # Обновление UI
                        self.update_gauges()
                        self.update_plots()
                        
                        # Проверка тревог
                        self.alerts = []
                        for i in range(4, len(data_parts)):
                            if ":" in data_parts[i]:
                                self.alerts.append(data_parts[i])
                        
                        # Проверка изменения статуса тревоги
                        current_alert_status = len(self.alerts) > 0 and not ("NORMAL" in str(self.alerts))
                        if current_alert_status != self.last_alert_status:
                            # Статус тревоги изменился
                            self.last_alert_status = current_alert_status
                            # Здесь будет отправка уведомлений в Telegram (в следующей части)
                        
                        self.update_alerts()
                        
                        # Автоматическое обновление рекомендаций при значительных изменениях
                        if self.significant_change and time.time() - self.last_ai_update_time > 60:
                            self.request_ai_recommendation()
                            self.last_ai_update_time = time.time()
                            
                    except ValueError as ve:
                        self.log(f"Ошибка преобразования данных: {str(ve)}")
                    
            elif "SILENT_MODE:" in data:
                mode = data.split('SILENT_MODE:')[1]
                self.silent_mode = (mode == "ON")
                self.silent_var.set("ВКЛ" if self.silent_mode else "ВЫКЛ")
                
                # Обновляем цвет индикатора и кнопку
                if self.silent_mode:
                    self.silent_var._label.configure(text_color="#4CAF50")  # Зеленый для ВКЛ
                    self.toggle_silent_button.configure(
                        text="🔇 Звук выключен",
                        fg_color="#F44336",  # Красный для выключенного звука
                        hover_color="#D32F2F"
                    )
                else:
                    self.silent_var._label.configure(text_color="#F44336")  # Красный для ВЫКЛ
                    self.toggle_silent_button.configure(
                        text="🔊 Звук включен",
                        fg_color="#0078D7",  # Синий для включенного звука
                        hover_color="#005A9E"
                    )
                
                self.log("Беззвучный режим " + ("включен" if self.silent_mode else "выключен"))
            elif "SYSTEM_READY" in data:
                self.log("Устройство готово к работе")
                
            elif "ERROR:" in data:
                error_msg = data.split('ERROR:')[1]
                self.log(f"Ошибка: {error_msg}")
                
            else:
                self.log(f"Получено: {data}")
                
        except Exception as e:
            self.log(f"Ошибка обработки данных: {str(e)}")

    def update_gauges(self):
        """Обновление круговых индикаторов"""
        # Пыль
        dust_color = self.get_color_for_value(self.dust_level, 30, 80)
        self.dust_gauge.set_value(self.dust_level, "мкг/м³", color=dust_color)
        
        # Газ
        gas_color = self.get_color_for_value(self.gas_level, 250, 320)
        self.gas_gauge.set_value(self.gas_level, "ppm", color=gas_color)
        
        # CO
        co_color = self.get_color_for_value(self.co_level, 200, 300)
        self.co_gauge.set_value(self.co_level, "ppm", color=co_color)
        
        # Метан
        methane_color = self.get_color_for_value(self.methane_level, 350, 500)
        self.methane_gauge.set_value(self.methane_level, "ppm", color=methane_color)
        
        # Влажность
        if 30 <= self.humidity <= 70:
            humidity_color = "#4CAF50"  # Зеленый для нормы
        else:
            humidity_color = "#F44336"  # Красный для выхода за границы
        self.humidity_gauge.set_value(self.humidity, "%", color=humidity_color)
        
        # Температура
        if 18 <= self.temperature <= 28:
            temp_color = "#4CAF50"  # Зеленый для нормы
        elif self.temperature < 18:
            temp_color = "#2196F3"  # Синий для низкой температуры
        else:
            temp_color = "#F44336"  # Красный для высокой температуры
        self.temp_gauge.set_value(self.temperature, "°C", color=temp_color)

    def get_color_for_value(self, value, low_threshold, high_threshold):
        """Определение цвета в зависимости от значения"""
        if value < low_threshold:
            return "#4CAF50"  # Зеленый
        elif value < high_threshold:
            return "#FF9800"  # Оранжевый
        else:
            return "#F44336"  # Красный

    def update_plots(self):
        """Обновление графиков с данными"""
        # Обновление данных на графиках
        x_data = list(range(len(self.timestamps)))
        
        self.dust_line.set_data(x_data, list(self.dust_data))
        self.gas_line.set_data(x_data, list(self.gas_data))
        self.co_line.set_data(x_data, list(self.co_data))
        self.methane_line.set_data(x_data, list(self.methane_data))
        self.humidity_line.set_data(x_data, list(self.humidity_data))
        self.temp_line.set_data(x_data, list(self.temp_data))
        
        # Автомасштабирование
        if len(x_data) > 1:
            # Устанавливаем одинаковые пределы по оси X для всех графиков
            for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]:
                ax.set_xlim(0, max(x_data))
            
            # Устанавливаем индивидуальные пределы по оси Y для каждого графика
            dust_max = max(1, max(self.dust_data)) * 1.1
            self.ax1.set_ylim(0, dust_max)
            
            gas_max = max(1, max(self.gas_data)) * 1.1
            self.ax2.set_ylim(0, gas_max)
            
            co_max = max(1, max(self.co_data)) * 1.1
            self.ax3.set_ylim(0, co_max)
            
            methane_max = max(1, max(self.methane_data)) * 1.1
            self.ax4.set_ylim(0, methane_max)
            
            humid_max = max(100, max(self.humidity_data) * 1.1)
            self.ax5.set_ylim(0, humid_max)
            
            temp_max = max(35, max(self.temp_data) * 1.1)
            self.ax6.set_ylim(0, temp_max)
            
            # Установка меток по оси X для нижних графиков
            if len(self.timestamps) > 1:
                tick_indices = np.linspace(0, len(self.timestamps) - 1, min(5, len(self.timestamps))).astype(int)
                tick_labels = [self.timestamps[i] for i in tick_indices]
                
                for ax in [self.ax5, self.ax6]:
                    ax.set_xticks(tick_indices)
                    ax.set_xticklabels(tick_labels, rotation=45)
        
        self.canvas.draw()

    def update_alerts(self):
        """Обновление списка тревог"""
        self.alerts_text.config(state=tk.NORMAL)
        self.alerts_text.delete(1.0, tk.END)
        
        if not self.alerts or (len(self.alerts) == 1 and "NORMAL" in self.alerts[0]):
            self.alerts_text.insert(tk.END, "✅ Нет активных тревог\n")
            self.alerts_text.tag_configure("normal", foreground="green")
            self.alerts_text.tag_add("normal", "1.0", "end")
        else:
            for alert in self.alerts:
                if "DUST" in alert:
                    percentage = alert.split(':')[1].split('%')[0]
                    self.alerts_text.insert(tk.END, f"⚠️ Превышение пыли: {percentage}% сверх нормы\n")
                elif "GAS" in alert:
                    percentage = alert.split(':')[1].split('%')[0]
                    self.alerts_text.insert(tk.END, f"⚠️ Превышение газа: {percentage}% сверх нормы\n")
                elif "CO" in alert:
                    percentage = alert.split(':')[1].split('%')[0]
                    self.alerts_text.insert(tk.END, f"⚠️ Превышение CO: {percentage}% сверх нормы\n")
                elif "METHANE" in alert:
                    percentage = alert.split(':')[1].split('%')[0]
                    self.alerts_text.insert(tk.END, f"⚠️ Превышение метана: {percentage}% сверх нормы\n")
                elif "HUMIDITY" in alert:
                    percentage = alert.split(':')[1].split('%')[0]
                    self.alerts_text.insert(tk.END, f"⚠️ Проблема с влажностью: {percentage}% отклонения\n")
                elif "TEMP" in alert:
                    percentage = alert.split(':')[1].split('%')[0]
                    self.alerts_text.insert(tk.END, f"⚠️ Проблема с температурой: {percentage}% отклонения\n")
                elif "NORMAL" not in alert:
                    self.alerts_text.insert(tk.END, f"⚠️ {alert}\n")
            
            # Добавляем красный цвет для всех тревог
            self.alerts_text.tag_configure("alert", foreground="red")
            self.alerts_text.tag_add("alert", "1.0", "end")
        
        self.alerts_text.config(state=tk.DISABLED)

    def request_data(self):
        """Запрос данных от устройства"""
        if not self.running or not self.serial_connection:
            messagebox.showwarning("Предупреждение", "Нет подключения к устройству!")
            return
            
        try:
            # Очистим буфер перед отправкой команды
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Отправляем команду и ждем подтверждение
            self.serial_connection.write(b"REQUEST_DATA\n")
            self.serial_connection.flush()  # Убедимся, что данные отправлены
            self.log("Запрос данных отправлен")
        except Exception as e:
            self.log(f"Ошибка отправки запроса: {str(e)}")

    def request_data_immediate(self):
        """Немедленный запрос данных, даже если включено автообновление"""
        self.request_data()
    
    def toggle_auto_update(self):
        """Переключение режима автообновления"""
        if self.auto_update_active:
            self.stop_auto_update()
            self.auto_update_button.configure(text="Автообновление выкл.")
        else:
            self.start_auto_update()
            self.auto_update_button.configure(text="Автообновление вкл.")
    
    def start_auto_update(self):
        """Запускает автоматическое обновление данных каждые 5 секунд"""
        if self.running and self.serial_connection:
            self.auto_update_active = True
            self.request_data()
            # Планируем следующее обновление
            self.auto_update_job = self.after(5000, self.start_auto_update)
        
    def stop_auto_update(self):
        """Останавливает автоматическое обновление"""
        self.auto_update_active = False
        if hasattr(self, 'auto_update_job'):
            self.after_cancel(self.auto_update_job)
            delattr(self, 'auto_update_job')

    def toggle_silent_mode(self):
        """Переключение беззвучного режима на устройстве"""
        if not self.running or not self.serial_connection:
            messagebox.showwarning("Предупреждение", "Нет подключения к устройству!")
            return
            
        try:
            self.serial_connection.write(b"TOGGLE_SILENT\n")
            self.silent_mode = not self.silent_mode
            
            # Обновляем текст и цвет кнопки
            if self.silent_mode:
                self.toggle_silent_button.configure(
                    text="🔇 Звук выключен",
                    fg_color="#F44336",  # Красный для выключенного звука
                    hover_color="#D32F2F"
                )
            else:
                self.toggle_silent_button.configure(
                    text="🔊 Звук включен",
                    fg_color="#0078D7",  # Синий для включенного звука
                    hover_color="#005A9E"
                )
            
            self.log("Беззвучный режим " + ("включен" if self.silent_mode else "выключен"))
        except Exception as e:
            self.log(f"Ошибка отправки запроса: {str(e)}")

    def request_ai_recommendation(self):
        """Запрос рекомендаций от ИИ на основе текущих данных"""
        # Если нет данных, запросим их сначала
        if self.dust_level == 0 and self.gas_level == 0 and self.humidity == 0:
            messagebox.showwarning("Предупреждение", "Нет данных для анализа!")
            return
            
        try:
            self.log("Запрос рекомендаций от ИИ...")
            
            # Подготовка данных для запроса к ИИ
            context = {
                "dust": self.dust_level,
                "gas": self.gas_level,
                "co": self.co_level,
                "methane": self.methane_level,
                "humidity": self.humidity,
                "temperature": self.temperature,
                "alerts": self.alerts
            }
            
            # Показываем окно загрузки
            self.show_loading_popup()
            
            # Асинхронный запрос рекомендаций
            threading.Thread(target=self.fetch_ai_recommendation, args=(context,)).start()
            
        except Exception as e:
            self.log(f"Ошибка запроса к ИИ: {str(e)}")
            self.close_loading_popup()

    def show_loading_popup(self):
        """Показать всплывающее окно загрузки"""
        self.loading_window = tk.Toplevel(self)
        self.loading_window.title("Загрузка")
        self.loading_window.geometry("300x100")
        self.loading_window.transient(self)
        self.loading_window.grab_set()
        
        # Центрируем окно
        x = self.winfo_x() + (self.winfo_width() // 2) - (300 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (100 // 2)
        self.loading_window.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(self.loading_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        label = ctk.CTkLabel(frame, text="Генерация рекомендаций...", font=("Arial", 14))
        label.pack(pady=10)
        
        # Добавляем индикатор загрузки
        self.loading_progress = ctk.CTkProgressBar(frame)
        self.loading_progress.pack(pady=5)
        self.loading_progress.start()

    def close_loading_popup(self):
        """Закрыть всплывающее окно загрузки"""
        if hasattr(self, 'loading_window'):
            self.loading_progress.stop()
            self.loading_window.destroy()
            delattr(self, 'loading_window')

    def fetch_ai_recommendation(self, context):
        """Получение рекомендаций от ИИ (в отдельном потоке)"""
        try:
            # Формирование запроса к ИИ
            prompt = self.generate_ai_prompt(context)
            
            # Вызов OpenRouter API
            recommendation = self.call_openrouter_api(prompt)
            
            # Обновление UI из основного потока
            self.after(0, lambda: self.update_ai_recommendation(recommendation))
            
        except Exception as e:
            self.after(0, lambda: self.log(f"Ошибка получения рекомендаций: {str(e)}"))
        finally:
            # Закрываем окно загрузки
            self.after(0, self.close_loading_popup)

    def call_openrouter_api(self, prompt):
        """Вызов OpenRouter API для получения рекомендаций от ИИ"""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer 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",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Air Quality Monitor"
            }
            
            data = {
                "model": "google/gemini-pro",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()  # Проверка на ошибки HTTP
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return "Не удалось получить рекомендации от ИИ. Попробуйте позже."
                
        except requests.exceptions.RequestException as e:
            return f"Ошибка при обращении к ИИ: {str(e)}"

    def generate_ai_prompt(self, context):
        """Генерация запроса к ИИ"""
        # Формируем текст с тревогами
        alerts_text = ""
        for alert in context["alerts"]:
            if "DUST" in alert:
                percentage = alert.split(':')[1].split('%')[0]
                alerts_text += f"Превышение пыли: {percentage}% сверх нормы. "
            elif "GAS" in alert:
                percentage = alert.split(':')[1].split('%')[0]
                alerts_text += f"Превышение газа: {percentage}% сверх нормы. "
            elif "CO" in alert:
                percentage = alert.split(':')[1].split('%')[0]
                alerts_text += f"Превышение CO: {percentage}% сверх нормы. "
            elif "METHANE" in alert:
                percentage = alert.split(':')[1].split('%')[0]
                alerts_text += f"Превышение метана: {percentage}% сверх нормы. "
            elif "HUMIDITY" in alert:
                percentage = alert.split(':')[1].split('%')[0]
                alerts_text += f"Проблема с влажностью: {percentage}% отклонения. "
            elif "TEMP" in alert:
                percentage = alert.split(':')[1].split('%')[0]
                alerts_text += f"Проблема с температурой: {percentage}% отклонения. "
        
        if not alerts_text:
            alerts_text = "Нет тревог. "
        
        prompt = f"""Ты - эксперт по качеству воздуха. Проанализируй следующие данные и дай рекомендации:

Текущие показатели:
- Уровень пыли: {context['dust']:.1f} мкг/м³ (норма до 30 мкг/м³)
- Уровень газа: {context['gas']} ppm (норма до 270 ppm)
- Уровень CO: {context['co']:.1f} ppm (норма до 20 ppm)
- Уровень метана: {context['methane']:.1f} ppm (норма до 100 ppm)
- Влажность: {context['humidity']:.1f}% (норма 30-70%)
- Температура: {context['temperature']:.1f}°C (комфортно 18-28°C)

Статус тревог: {alerts_text}

Дай краткие, четкие рекомендации для улучшения качества воздуха:
1. Используй эмодзи в начале каждой рекомендации
2. Укажи только конкретные действия, которые помогут решить проблемы
3. Расставь приоритеты - сначала самые важные действия
4. Будь лаконичен - не более 5-7 пунктов
5. Если все показатели в норме, дай рекомендации по профилактике

Формат ответа:
Рекомендации по улучшению качества воздуха:

[список рекомендаций с эмодзи]"""
        return prompt

    def format_ai_text(self, text):
        """Форматирование текста от ИИ: замена ** на жирный шрифт"""
        # Создаем виджет Text для форматированного текста
        formatted_text = tk.Text(self)
        
        # Создаем тег для жирного шрифта
        formatted_text.tag_configure("bold", font=("Arial", 11, "bold"))
        
        # Находим все вхождения текста между **
        import re
        parts = re.split(r'(\*\*.*?\*\*)', text)
        
        # Вставляем текст с форматированием
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                # Убираем звездочки и вставляем текст с тегом bold
                bold_text = part[2:-2]
                formatted_text.insert(tk.END, bold_text, "bold")
            else:
                formatted_text.insert(tk.END, part)
        
        # Получаем отформатированный текст
        result = formatted_text.get("1.0", tk.END)
        formatted_text.destroy()
        return result

    def update_ai_recommendation(self, recommendation):
        """Обновление текста рекомендаций в интерфейсе"""
        self.ai_text.config(state=tk.NORMAL)
        self.ai_text.delete(1.0, tk.END)
        
        # Форматируем текст и создаем тег для жирного шрифта
        self.ai_text.tag_configure("bold", font=("Arial", 11, "bold"))
        
        # Находим все вхождения текста между **
        import re
        parts = re.split(r'(\*\*.*?\*\*)', recommendation)
        
        # Вставляем текст с форматированием
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                # Убираем звездочки и вставляем текст с тегом bold
                bold_text = part[2:-2]
                self.ai_text.insert(tk.END, bold_text, "bold")
            else:
                self.ai_text.insert(tk.END, part)
        
        self.ai_text.config(state=tk.DISABLED)
        self.log("Получены рекомендации от ИИ")

    def log(self, message):
        """Добавление записи в журнал событий"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)  # Прокрутка до последней строки
        self.log_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = AirQualityMonitor()
    app.mainloop()
