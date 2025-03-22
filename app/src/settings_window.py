import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from .air_quality_profiles import AIR_QUALITY_PROFILES, update_custom_profile, get_arduino_command

class ToolTip:
    """Создает всплывающую подсказку для виджета"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        
    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#FFFFEA",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", "10", "normal"),
            padx=5,
            pady=2
        )
        label.pack()
        
    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class RoundedButton(ctk.CTkButton):
    """Кастомная кнопка с закругленными краями"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(
            corner_radius=10,
            border_width=0,
            hover=True,
            fg_color="#0078D7",
            hover_color="#005A9E",
            text_color="#FFFFFF",
            height=36
        )

class SettingsWindow(ctk.CTkToplevel):
    """Окно настроек профилей качества воздуха"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Настройка окна
        self.title("Настройки профилей качества воздуха")
        self.geometry("800x700")
        self.minsize(800, 700)
        
        # Создаем основной контейнер
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        header_label = ctk.CTkLabel(
            header_frame,
            text="Настройки профилей качества воздуха",
            font=("Arial", 20, "bold")
        )
        header_label.pack(side=tk.LEFT)
        
        # Создаем вкладки для разных профилей
        self.tab_view = ctk.CTkTabview(self.main_container)
        self.tab_view.pack(fill=tk.BOTH, expand=True)
        
        # Словарь для хранения виджетов ввода
        self.entries = {}
        self.sliders = {}
        
        # Добавляем вкладки для каждого профиля
        self.tabs = {}
        for profile_id, profile in AIR_QUALITY_PROFILES.items():
            tab = self.tab_view.add(profile["name"])
            self.tabs[profile_id] = tab
            self.create_profile_settings(tab, profile_id, profile)
        
        # Кнопки управления
        self.create_control_buttons()
        
    def create_profile_settings(self, tab, profile_id, profile):
        """Создание элементов управления для профиля"""
        # Основной контейнер для настроек
        settings_container = ctk.CTkScrollableFrame(tab)
        settings_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок с описанием
        description = self.get_profile_description(profile_id)
        header = ctk.CTkLabel(
            settings_container,
            text=description,
            font=("Arial", 12),
            wraplength=600
        )
        header.pack(pady=(0, 20))
        
        # Создаем секции настроек
        self.entries[profile_id] = {}
        self.sliders[profile_id] = {}
        
        # Создаем фрейм для значений
        values_frame = ctk.CTkFrame(settings_container, fg_color="#F5F5F5", corner_radius=15)
        values_frame.pack(fill=tk.X, pady=10, padx=20)
        
        # Создаем сетку для значений 2x3
        grid_frame = ctk.CTkFrame(values_frame, fg_color="transparent")
        grid_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Пороговые значения
        self.create_value_display(grid_frame, 0, 0, "Порог пыли", f"{profile['dust_threshold']} мкг/м³", "#2196F3")
        self.create_value_display(grid_frame, 0, 1, "Порог газа", f"{profile['gas_threshold']} ppm", "#FF9800")
        self.create_value_display(grid_frame, 0, 2, "Порог CO", f"{profile['co_threshold']} ppm", "#F44336")
        self.create_value_display(grid_frame, 1, 0, "Порог метана", f"{profile['methane_threshold']} ppm", "#9C27B0")
        self.create_value_display(grid_frame, 1, 1, "Влажность", f"{profile['humidity_range'][0]}-{profile['humidity_range'][1]}%", "#4CAF50")
        self.create_value_display(grid_frame, 1, 2, "Температура", f"{profile['temperature_range'][0]}-{profile['temperature_range'][1]}°C", "#FF5722")
        
        # Кнопки действий
        actions_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        actions_frame.pack(fill=tk.X, pady=20)
        
        # Кнопка применения профиля
        apply_profile_button = RoundedButton(
            actions_frame,
            text="Применить этот профиль",
            command=lambda p_id=profile_id: self.apply_profile(p_id)
        )
        apply_profile_button.pack(side=tk.LEFT, padx=5)
        
        # Для пользовательского профиля добавляем кнопку изменения
        if profile_id == "custom":
            edit_button = RoundedButton(
                actions_frame,
                text="Изменить настройки",
                command=self.show_edit_dialog
            )
            edit_button.pack(side=tk.LEFT, padx=5)
    
    def create_section_frame(self, parent, title):
        """Создание секции с заголовком"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill=tk.X, pady=10)
        
        label = ctk.CTkLabel(
            frame,
            text=title,
            font=("Arial", 14, "bold")
        )
        label.pack(pady=(10, 5), padx=10, anchor="w")
        
        return frame
    
    def create_slider_setting(self, parent, profile_id, key, label, unit, min_val, max_val, default, tooltip):
        """Создание настройки со слайдером"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Метка
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(fill=tk.X)
        
        label_text = ctk.CTkLabel(
            label_frame,
            text=f"{label} ({unit}):",
            font=("Arial", 12)
        )
        label_text.pack(side=tk.LEFT)
        
        # Создаем подсказку
        ToolTip(label_text, tooltip)
        
        # Значение
        value_var = tk.StringVar()
        value_label = ctk.CTkLabel(
            label_frame,
            textvariable=value_var,
            font=("Arial", 12, "bold")
        )
        value_label.pack(side=tk.RIGHT)
        
        # Слайдер
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=int(max_val - min_val),
            command=lambda v: value_var.set(f"{v:.1f} {unit}")
        )
        slider.pack(fill=tk.X, pady=(5, 0))
        slider.set(default)
        value_var.set(f"{default:.1f} {unit}")
        
        self.sliders[profile_id][key] = slider
    
    def create_range_setting(self, parent, profile_id, key, label, unit, min_val, max_val, default_range, tooltip):
        """Создание настройки с двумя слайдерами для диапазона"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Метка
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(fill=tk.X)
        
        label_text = ctk.CTkLabel(
            label_frame,
            text=f"{label} ({unit}):",
            font=("Arial", 12)
        )
        label_text.pack(side=tk.LEFT)
        
        # Создаем подсказку
        ToolTip(label_text, tooltip)
        
        # Значения
        value_var = tk.StringVar()
        value_label = ctk.CTkLabel(
            label_frame,
            textvariable=value_var,
            font=("Arial", 12, "bold")
        )
        value_label.pack(side=tk.RIGHT)
        
        # Слайдеры
        slider_frame = ctk.CTkFrame(frame, fg_color="transparent")
        slider_frame.pack(fill=tk.X, pady=(5, 0))
        
        def update_value(*args):
            min_v = min_slider.get()
            max_v = max_slider.get()
            if min_v > max_v:
                if args[0] == min_slider:
                    max_slider.set(min_v)
                else:
                    min_slider.set(max_v)
            min_v = min(min_slider.get(), max_slider.get())
            max_v = max(min_slider.get(), max_slider.get())
            value_var.set(f"{min_v:.1f} - {max_v:.1f} {unit}")
        
        min_slider = ctk.CTkSlider(
            slider_frame,
            from_=min_val,
            to=max_val,
            number_of_steps=int(max_val - min_val),
            command=update_value
        )
        min_slider.pack(fill=tk.X)
        min_slider.set(default_range[0])
        
        max_slider = ctk.CTkSlider(
            slider_frame,
            from_=min_val,
            to=max_val,
            number_of_steps=int(max_val - min_val),
            command=update_value
        )
        max_slider.pack(fill=tk.X)
        max_slider.set(default_range[1])
        
        update_value(min_slider)
        
        self.sliders[profile_id][key] = (min_slider, max_slider)
    
    def create_control_buttons(self):
        """Создание кнопок управления"""
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Кнопка применения
        apply_button = RoundedButton(
            button_frame,
            text="Применить все настройки",
            command=self.apply_settings
        )
        apply_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка отмены
        cancel_button = RoundedButton(
            button_frame,
            text="Отмена",
            command=self.destroy,
            fg_color="#E0E0E0",
            hover_color="#BDBDBD",
            text_color="#000000"
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def get_profile_description(self, profile_id):
        """Получение описания профиля"""
        descriptions = {
            "street": "Профиль для мониторинга качества воздуха на улице. Имеет повышенные пороговые значения для учета естественных колебаний параметров в уличных условиях.",
            "home": "Стандартный профиль для жилых помещений. Оптимизирован для обеспечения комфортных и безопасных условий проживания.",
            "event": "Профиль для помещений с массовым пребыванием людей. Имеет более строгие требования к качеству воздуха.",
            "custom": "Пользовательский профиль с настраиваемыми параметрами. Позволяет установить собственные пороговые значения для всех параметров."
        }
        return descriptions.get(profile_id, "")
    
    def apply_settings(self):
        """Применение настроек всех профилей"""
        try:
            for profile_id in self.sliders:
                profile = {}
                
                # Получаем значения слайдеров
                for key, slider in self.sliders[profile_id].items():
                    if isinstance(slider, tuple):  # Диапазон
                        value = (slider[0].get(), slider[1].get())
                    else:  # Одиночное значение
                        value = slider.get()
                    
                    if key == "humidity_range":
                        profile["humidity_range"] = value
                    elif key == "temperature_range":
                        profile["temperature_range"] = value
                    else:
                        profile[key] = value
                
                # Обновляем профиль
                AIR_QUALITY_PROFILES[profile_id].update(profile)
            
            messagebox.showinfo(
                "Успех",
                "Настройки профилей успешно обновлены"
            )
            self.destroy()
            
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось применить настройки:\n{str(e)}"
            )
    
    def show_edit_dialog(self):
        """Показывает диалог редактирования настроек"""
        dialog = EditSettingsDialog(self)
        if dialog.exec():
            # Обновляем отображение значений
            profile = AIR_QUALITY_PROFILES["custom"]
            self.update_value_display("Порог пыли", f"{profile['dust_threshold']} мкг/м³")
            self.update_value_display("Порог газа", f"{profile['gas_threshold']} ppm")
            self.update_value_display("Порог CO", f"{profile['co_threshold']} ppm")
            self.update_value_display("Порог метана", f"{profile['methane_threshold']} ppm")
            self.update_value_display("Влажность", f"{profile['humidity_range'][0]}-{profile['humidity_range'][1]}%")
            self.update_value_display("Температура", f"{profile['temperature_range'][0]}-{profile['temperature_range'][1]}°C")

    def apply_profile(self, profile_id):
        """Применение выбранного профиля"""
        if not self.parent.running or not self.parent.serial_connection:
            messagebox.showwarning(
                "Предупреждение",
                "Нет подключения к устройству!"
            )
            return
            
        try:
            # Формируем и отправляем команду на Arduino
            command = get_arduino_command(profile_id)
            self.parent.serial_connection.write(command)
            self.parent.log(f"Применен профиль: {AIR_QUALITY_PROFILES[profile_id]['name']}")
            messagebox.showinfo(
                "Успех",
                f"Профиль {AIR_QUALITY_PROFILES[profile_id]['name']} успешно применен"
            )
            
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось применить профиль:\n{str(e)}"
            )

    def create_value_display(self, parent, row, col, label, value, color):
        """Создание красивого отображения значения"""
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Настраиваем веса для равномерного распределения
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)
        
        # Метка
        label_widget = ctk.CTkLabel(
            frame,
            text=label,
            font=("Arial", 12),
            text_color="#666666"
        )
        label_widget.pack(pady=(10, 5))
        
        # Значение
        value_widget = ctk.CTkLabel(
            frame,
            text=value,
            font=("Arial", 14, "bold"),
            text_color=color
        )
        value_widget.pack(pady=(0, 10))

class EditSettingsDialog(ctk.CTkToplevel):
    """Диалог редактирования настроек"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Настройка окна
        self.title("Редактирование настроек")
        self.geometry("600x800")
        self.minsize(600, 800)
        
        # Создаем основной контейнер
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок
        header_label = ctk.CTkLabel(
            self.main_container,
            text="Редактирование настроек профиля",
            font=("Arial", 20, "bold")
        )
        header_label.pack(pady=(0, 20))
        
        # Словарь для хранения слайдеров
        self.sliders = {}
        
        # Секция пороговых значений
        threshold_frame = self.create_section_frame("Пороговые значения")
        
        # Пыль
        self.create_slider_setting(
            threshold_frame,
            "dust_threshold",
            "Порог пыли",
            "мкг/м³",
            0, 100,
            AIR_QUALITY_PROFILES["custom"]["dust_threshold"],
            "Максимально допустимый уровень пыли в воздухе"
        )
        
        # Газ
        self.create_slider_setting(
            threshold_frame,
            "gas_threshold",
            "Порог газа",
            "ppm",
            0, 1000,
            AIR_QUALITY_PROFILES["custom"]["gas_threshold"],
            "Максимально допустимый уровень газа в воздухе"
        )
        
        # CO
        self.create_slider_setting(
            threshold_frame,
            "co_threshold",
            "Порог CO",
            "ppm",
            0, 800,
            AIR_QUALITY_PROFILES["custom"]["co_threshold"],
            "Максимально допустимый уровень угарного газа"
        )
        
        # Метан
        self.create_slider_setting(
            threshold_frame,
            "methane_threshold",
            "Порог метана",
            "ppm",
            0, 1000,
            AIR_QUALITY_PROFILES["custom"]["methane_threshold"],
            "Максимально допустимый уровень метана"
        )
        
        # Секция диапазонов
        range_frame = self.create_section_frame("Диапазоны значений")
        
        # Влажность
        self.create_range_setting(
            range_frame,
            "humidity_range",
            "Диапазон влажности",
            "%",
            0, 100,
            AIR_QUALITY_PROFILES["custom"]["humidity_range"],
            "Допустимый диапазон влажности воздуха"
        )
        
        # Температура
        self.create_range_setting(
            range_frame,
            "temperature_range",
            "Диапазон температуры",
            "°C",
            -20, 50,
            AIR_QUALITY_PROFILES["custom"]["temperature_range"],
            "Допустимый диапазон температуры"
        )
        
        # Кнопки управления
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.pack(fill=tk.X, pady=20)
        
        # Кнопка сохранения
        save_button = RoundedButton(
            button_frame,
            text="Сохранить",
            command=self.save_settings
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка отмены
        cancel_button = RoundedButton(
            button_frame,
            text="Отмена",
            command=self.destroy,
            fg_color="#E0E0E0",
            hover_color="#BDBDBD",
            text_color="#000000"
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def create_section_frame(self, title):
        """Создание секции с заголовком"""
        frame = ctk.CTkFrame(self.main_container)
        frame.pack(fill=tk.X, pady=10)
        
        label = ctk.CTkLabel(
            frame,
            text=title,
            font=("Arial", 14, "bold")
        )
        label.pack(pady=(10, 5), padx=10, anchor="w")
        
        return frame
    
    def create_slider_setting(self, parent, key, label, unit, min_val, max_val, default, tooltip):
        """Создание настройки со слайдером"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Метка
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(fill=tk.X)
        
        label_text = ctk.CTkLabel(
            label_frame,
            text=f"{label} ({unit}):",
            font=("Arial", 12)
        )
        label_text.pack(side=tk.LEFT)
        
        # Создаем подсказку
        ToolTip(label_text, tooltip)
        
        # Значение
        value_var = tk.StringVar()
        value_label = ctk.CTkLabel(
            label_frame,
            textvariable=value_var,
            font=("Arial", 12, "bold")
        )
        value_label.pack(side=tk.RIGHT)
        
        # Слайдер
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=int(max_val - min_val),
            command=lambda v: value_var.set(f"{v:.1f} {unit}")
        )
        slider.pack(fill=tk.X, pady=(5, 0))
        slider.set(default)
        value_var.set(f"{default:.1f} {unit}")
        
        self.sliders[key] = slider
    
    def create_range_setting(self, parent, key, label, unit, min_val, max_val, default_range, tooltip):
        """Создание настройки с двумя слайдерами для диапазона"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Метка
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(fill=tk.X)
        
        label_text = ctk.CTkLabel(
            label_frame,
            text=f"{label} ({unit}):",
            font=("Arial", 12)
        )
        label_text.pack(side=tk.LEFT)
        
        # Создаем подсказку
        ToolTip(label_text, tooltip)
        
        # Значения
        value_var = tk.StringVar()
        value_label = ctk.CTkLabel(
            label_frame,
            textvariable=value_var,
            font=("Arial", 12, "bold")
        )
        value_label.pack(side=tk.RIGHT)
        
        # Слайдеры
        slider_frame = ctk.CTkFrame(frame, fg_color="transparent")
        slider_frame.pack(fill=tk.X, pady=(5, 0))
        
        def update_value(*args):
            min_v = min_slider.get()
            max_v = max_slider.get()
            if min_v > max_v:
                if args[0] == min_slider:
                    max_slider.set(min_v)
                else:
                    min_slider.set(max_v)
            min_v = min(min_slider.get(), max_slider.get())
            max_v = max(min_slider.get(), max_slider.get())
            value_var.set(f"{min_v:.1f} - {max_v:.1f} {unit}")
        
        min_slider = ctk.CTkSlider(
            slider_frame,
            from_=min_val,
            to=max_val,
            number_of_steps=int(max_val - min_val),
            command=update_value
        )
        min_slider.pack(fill=tk.X)
        min_slider.set(default_range[0])
        
        max_slider = ctk.CTkSlider(
            slider_frame,
            from_=min_val,
            to=max_val,
            number_of_steps=int(max_val - min_val),
            command=update_value
        )
        max_slider.pack(fill=tk.X)
        max_slider.set(default_range[1])
        
        update_value(min_slider)
        
        self.sliders[key] = (min_slider, max_slider)
    
    def save_settings(self):
        """Сохранение настроек"""
        try:
            profile = {}
            
            # Получаем значения слайдеров
            for key, slider in self.sliders.items():
                if isinstance(slider, tuple):  # Диапазон
                    value = (slider[0].get(), slider[1].get())
                else:  # Одиночное значение
                    value = slider.get()
                
                if key == "humidity_range":
                    profile["humidity_range"] = value
                elif key == "temperature_range":
                    profile["temperature_range"] = value
                else:
                    profile[key] = value
            
            # Обновляем пользовательский профиль
            AIR_QUALITY_PROFILES["custom"].update(profile)
            update_custom_profile(profile)
            
            messagebox.showinfo(
                "Успех",
                "Настройки успешно сохранены"
            )
            self.destroy()
            
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось сохранить настройки:\n{str(e)}"
            ) 