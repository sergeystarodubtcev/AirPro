import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QMessageBox, 
                           QFrame, QDialog, QTextEdit)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor, QPalette, QLinearGradient
from .air_quality_monitor2 import AirQualityMonitor
import webbrowser

class StyledButton(QPushButton):
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Arial", 12 if not primary else 14, QFont.Weight.Bold if primary else QFont.Weight.Normal))
        self.setMinimumHeight(50 if primary else 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Стилизация кнопки
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 10px 20px;
                    transition: background-color 0.3s;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                    transform: translateY(1px);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #E3F2FD;
                    color: #1976D2;
                    border: 2px solid #BBDEFB;
                    border-radius: 20px;
                    padding: 8px 16px;
                    transition: all 0.3s;
                }
                QPushButton:hover {
                    background-color: #BBDEFB;
                    border-color: #1976D2;
                    color: #0D47A1;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(33, 150, 243, 0.2);
                }
                QPushButton:pressed {
                    background-color: #90CAF9;
                    border-color: #0D47A1;
                    transform: translateY(1px);
                    box-shadow: 0 2px 4px rgba(33, 150, 243, 0.2);
                }
            """)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О проекте Air Pro")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333333;
            }
            QTextEdit {
                border: 1px solid #CCCCCC;
                border-radius: 10px;
                padding: 10px;
                background-color: #F8F8F8;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Заголовок
        title = QLabel("Air Pro - Система мониторинга качества воздуха")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Описание
        description = QTextEdit()
        description.setReadOnly(True)
        description.setFont(QFont("Arial", 12))
        description.setText("""
Air Pro - это инновационная система мониторинга качества воздуха с интегрированным искусственным интеллектом.

Основные возможности:
• Интеллектуальный анализ качества воздуха в реальном времени
• Прогнозирование изменений параметров воздуха с помощью ИИ
• Умные рекомендации по улучшению микроклимата
• Автоматическое определение опасных тенденций
• Персонализированные отчеты на основе анализа данных
• Экспорт данных в Excel с аналитикой
• Интеграция с облачными сервисами

Технические характеристики:
• Нейросетевой анализ данных
• Машинное обучение для адаптации к условиям
• Поддержка различных датчиков
• Автоматическое определение портов
• Многоязычный интерфейс
• Современный адаптивный дизайн

Для работы приложения требуется:
• Arduino с датчиками
• USB-соединение
• Windows 10/11
• Подключение к интернету для облачной аналитики
""")
        layout.addWidget(description)
        
        # Кнопка закрытия
        close_button = StyledButton("Закрыть", primary=True)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Air Pro")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QLabel {
                color: #333333;
            }
        """)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(50, 50, 50, 50)
        
        # Логотип
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'logo.png')
        logo_pixmap = QPixmap(logo_path)
        scaled_pixmap = logo_pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, 
                                         Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(logo_label)
        
        # Заголовок
        title_label = QLabel("Air Pro - Умный мониторинг с ИИ")
        title_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Описание
        description_label = QLabel(
            "Инновационная система мониторинга качества воздуха с искусственным интеллектом.\n"
            "Анализируйте качество воздуха, получайте умные рекомендации и прогнозы от ИИ."
        )
        description_label.setFont(QFont("Arial", 14))
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)
        
        # Кнопка подключения (центрированная и увеличенная)
        self.connect_button = StyledButton("Подключиться", primary=True)
        self.connect_button.setMinimumWidth(300)  # Увеличиваем ширину
        self.connect_button.setMinimumHeight(60)  # Увеличиваем высоту
        self.connect_button.setFont(QFont("Arial", 16, QFont.Weight.Bold))  # Увеличиваем шрифт
        self.connect_button.clicked.connect(self.connect_to_device)
        main_layout.addWidget(self.connect_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Добавляем растяжку (небольшой отступ)
        main_layout.addStretch(1)
        
        # Горизонтальный layout для остальных кнопок
        other_buttons_layout = QHBoxLayout()
        other_buttons_layout.setSpacing(20)
        
        # Кнопка перехода на сайт
        website_button = StyledButton("Перейти на сайт")
        website_button.clicked.connect(self.open_website)
        other_buttons_layout.addWidget(website_button)
        
        # Кнопка "О проекте"
        about_button = StyledButton("О проекте")
        about_button.clicked.connect(self.show_about)
        other_buttons_layout.addWidget(about_button)
        
        # Кнопка перехода на GitHub
        github_button = StyledButton("Код проекта")
        github_button.clicked.connect(self.open_github)
        other_buttons_layout.addWidget(github_button)
        
        main_layout.addLayout(other_buttons_layout)
        
    def connect_to_device(self):
        """Открывает окно мониторинга"""
        try:
            # Импортируем и создаем экземпляр AirQualityMonitor
            self.monitor_window = AirQualityMonitor()
            self.monitor_window.mainloop()  # Запускаем главный цикл
            self.close()  # Закрываем главное окно
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                               f"Не удалось открыть окно мониторинга:\n{str(e)}")
    
    def show_about(self):
        """Показывает диалог с информацией о проекте"""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def open_website(self):
        """Открывает сайт проекта"""
        webbrowser.open('http://q99525fe.beget.tech/')
        
    def open_github(self):
        """Открывает GitHub репозиторий проекта"""
        webbrowser.open('https://github.com/sergeystarodubtcev/AirPro')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 