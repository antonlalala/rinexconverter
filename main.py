# rinex.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
from pathlib import Path
from datetime import datetime
import numpy as np

# Правильные импорты
from rinex_processor import RinexProcessor
from coordinate_converter import CoordinateConverter
from precise_calculations import HighPrecisionPPPCalculator

class AdvancedRinexConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced RINEX Converter v2.0 - Точный конвертер координат")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Инициализация модулей
        self.processor = RinexProcessor()
        self.converter = CoordinateConverter()
        self.ppp_calculator = HighPrecisionPPPCalculator()
        
        # Переменные
        self.file_path_var = tk.StringVar(value="Файл не выбран")
        self.method_var = tk.StringVar(value="Точный (PPP)")
        self.status_var = tk.StringVar(value="Готов к работе")
        self.progress_var = tk.IntVar(value=0)
        
        # Данные
        self.obs_data = {}
        self.nav_data = {}
        self.approx_position = None
        self.current_obs_file = None
        self.current_nav_file = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Создание интерфейса"""
        # Стиль
        self.setup_styles()
        
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Заголовок
        self.create_title_section(main_frame, 0)
        
        # Секция выбора файла
        self.create_file_section(main_frame, 1)
        
        # Прогресс бар
        self.create_progress_section(main_frame, 2)
        
        # Секция метода расчета
        self.create_method_section(main_frame, 3)
        
        # Секция результатов
        self.create_result_section(main_frame, 4)
        
        # Статус бар
        self.create_status_section(main_frame, 5)
        
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 11, 'bold'))
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
    def create_title_section(self, parent, row):
        """Секция заголовка"""
        title_frame = ttk.Frame(parent)
        title_frame.grid(row=row, column=0, columnspan=3, pady=(0, 20), sticky=(tk.W, tk.E))
        
        ttk.Label(title_frame, 
                 text="🚀 Advanced RINEX Converter v2.0", 
                 style='Title.TLabel').pack(side=tk.LEFT)
        
        ttk.Label(title_frame, 
                 text="Точное позиционирование с PPP", 
                 foreground='gray').pack(side=tk.RIGHT)
        
    def create_file_section(self, parent, row):
        """Секция выбора файлов"""
        file_frame = ttk.LabelFrame(parent, text="📁 Выбор файлов RINEX", padding="12")
        file_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 12))
        file_frame.columnconfigure(1, weight=1)
        
        # Файл наблюдений
        ttk.Button(file_frame, text="Выбрать .obs/.o файл", 
                  command=self.select_obs_file, width=18).grid(row=0, column=0, padx=(0, 10), pady=4)
        
        self.obs_file_label = ttk.Label(file_frame, text="Файл наблюдений не выбран", 
                                       background='#f8f9fa', relief='solid', padding="6", borderwidth=1)
        self.obs_file_label.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=4)
        
        # Файл навигации
        ttk.Button(file_frame, text="Выбрать .nav/.n файл", 
                  command=self.select_nav_file, width=18).grid(row=1, column=0, padx=(0, 10), pady=4)
        
        self.nav_file_label = ttk.Label(file_frame, text="Файл навигации не выбран", 
                                       background='#f8f9fa', relief='solid', padding="6", borderwidth=1)
        self.nav_file_label.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=4)
        
        # Кнопки управления
        btn_frame = ttk.Frame(file_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=(8, 0))
        
        ttk.Button(btn_frame, text="📖 Прочитать данные", 
                  command=self.read_rinex_files).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="⚡ Быстрый расчет", 
                  command=self.quick_calculate).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="🎯 Точный PPP расчет", 
                  command=self.precise_calculate, style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="🔧 Расширенные настройки", 
                  command=self.precise_calculate_enhanced).pack(side=tk.LEFT, padx=2)
    
    def create_progress_section(self, parent, row):
        """Секция прогресса"""
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 12))
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=0, column=1, padx=(10, 0))
        
        progress_frame.columnconfigure(0, weight=1)
    
    def create_method_section(self, parent, row):
        """Секция выбора метода расчета"""
        method_frame = ttk.LabelFrame(parent, text="⚙️ Метод расчета", padding="12")
        method_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 12))
        
        # Выбор метода
        methods = [
            ("⚡ Быстрый (приблизительные координаты)", "Быстрый"),
            ("🎯 Точный (PPP - Precise Point Positioning)", "Точный (PPP)"),
            ("💎 Высокоточный (с дифференциальными поправками)", "Высокоточный")
        ]
        
        for i, (text, value) in enumerate(methods):
            ttk.Radiobutton(method_frame, text=text, 
                           variable=self.method_var, value=value).grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Информация о методе
        self.method_info = ttk.Label(method_frame, 
                                    text="Быстрый метод использует координаты из заголовка файла", 
                                    foreground="#0066cc", font=("Arial", 9))
        self.method_info.grid(row=3, column=0, sticky=tk.W, pady=(8, 0))
        
        # Привязка события изменения метода
        self.method_var.trace('w', self.on_method_change)
    
    def create_result_section(self, parent, row):
        """Секция результатов"""
        result_frame = ttk.LabelFrame(parent, text="📊 Результаты", padding="12")
        result_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12))
        parent.rowconfigure(row, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # Текстовое поле для результатов
        self.result_text = tk.Text(result_frame, height=18, wrap=tk.WORD, 
                                  font=("Consolas", 10), relief='solid', borderwidth=1)
        
        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Кнопки экспорта
        export_frame = ttk.Frame(result_frame)
        export_frame.grid(row=1, column=0, columnspan=2, sticky=tk.E, pady=(8, 0))
        
        ttk.Button(export_frame, text="💾 Сохранить результаты", 
                  command=self.save_results).pack(side=tk.RIGHT, padx=3)
        
        ttk.Button(export_frame, text="🗑️ Очистить", 
                  command=self.clear_results).pack(side=tk.RIGHT, padx=3)
        
        ttk.Button(export_frame, text="📋 Копировать", 
                  command=self.copy_results).pack(side=tk.RIGHT, padx=3)
    
    def create_status_section(self, parent, row):
        """Секция статуса"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                relief='sunken', padding="6", background='#e9ecef')
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Информация о версии
        version_label = ttk.Label(status_frame, text="v2.0 | PPP Calculator", 
                                 foreground='gray')
        version_label.grid(row=0, column=1, padx=(10, 0))
        
        status_frame.columnconfigure(0, weight=1)
    
    def on_method_change(self, *args):
        """Обновление информации о методе"""
        method = self.method_var.get()
        info_texts = {
            "Быстрый": "⚡ Быстрый метод использует координаты из заголовка файла (точность ~1-10 м)",
            "Точный (PPP)": "🎯 PPP метод использует фазовые измерения (точность ~0.1-1 м)",
            "Высокоточный": "💎 Высокоточный метод требует базовой станции (точность ~0.01-0.1 м)"
        }
        self.method_info.config(text=info_texts.get(method, ""))
    
    def update_progress(self, value, text=None):
        """Обновление прогресса"""
        self.progress_var.set(value)
        if text:
            self.progress_label.config(text=text)
        self.root.update_idletasks()
    
    def select_obs_file(self):
        """Выбор файла наблюдений"""
        file_types = [
            ("RINEX Observation files", "*.obs *.OBS *.??o *.??O *.21o *.22o *.20o"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(title="Выберите файл наблюдений", filetypes=file_types)
        if filename:
            self.current_obs_file = filename
            self.obs_file_label.config(text=Path(filename).name)
            self.status_var.set(f"📁 Выбран файл наблюдений: {Path(filename).name}")
    
    def select_nav_file(self):
        """Выбор файла навигации"""
        file_types = [
            ("RINEX Navigation files", "*.nav *.NAV *.??n *.??N *.21n *.22n *.20n"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(title="Выберите файл навигации", filetypes=file_types)
        if filename:
            self.current_nav_file = filename
            self.nav_file_label.config(text=Path(filename).name)
            self.status_var.set(f"📁 Выбран файл навигации: {Path(filename).name}")
    
    def read_rinex_files(self):
        """Чтение RINEX файлов"""
        try:
            self.update_progress(0, "Начало чтения файлов...")
            
            # Чтение файла наблюдений
            if self.current_obs_file:
                self.update_progress(30, "Чтение файла наблюдений...")
                self.obs_data = self.processor.read_rinex_obs_file(self.current_obs_file)
                if self.obs_data and 'approx_position' in self.obs_data['header']:
                    self.approx_position = self.obs_data['header']['approx_position']
            
            # Чтение файла навигации
            if self.current_nav_file:
                self.update_progress(70, "Чтение файла навигации...")
                self.nav_data = self.processor.read_rinex_nav_file(self.current_nav_file)
            
            self.update_progress(100, "Чтение завершено!")
            self.show_file_info()
            self.status_var.set("✅ Файлы успешно прочитаны")
            
        except Exception as e:
            self.update_progress(0, "Ошибка!")
            messagebox.showerror("Ошибка", f"Ошибка при чтении файлов: {e}")
            self.status_var.set("❌ Ошибка при чтении файлов")
    
    def show_file_info(self):
        """Показать информацию о файлах"""
        info = "=== ИНФОРМАЦИЯ О ФАЙЛАХ ===\n\n"
        
        if self.obs_data:
            info += "📊 ФАЙЛ НАБЛЮДЕНИЙ:\n"
            if 'approx_position' in self.obs_data['header']:
                x, y, z = self.obs_data['header']['approx_position']
                info += f"  Приблизительные координаты:\n"
                info += f"    X: {x:12.3f} м\n"
                info += f"    Y: {y:12.3f} м\n"
                info += f"    Z: {z:12.3f} м\n"
                
                # Преобразование в географические
                lat, lon, height, iterations = self.converter.xyz_to_llh_high_precision(x, y, z)
                info += f"    Широта:  {lat:10.6f}°\n"
                info += f"    Долгота: {lon:10.6f}°\n"
                info += f"    Высота:  {height:8.3f} м\n"
                info += f"    (итераций: {iterations})\n"
            info += "\n"
        
        if self.nav_data:
            info += "🛰️ ФАЙЛ НАВИГАЦИИ:\n"
            info += "  Эфемериды загружены\n"
        
        info += "=" * 40 + "\n"
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, info)
    
    def quick_calculate(self):
        """Быстрый расчет по приблизительным координатам"""
        if not self.approx_position:
            messagebox.showwarning("Предупреждение", "Сначала прочитайте RINEX файл")
            return
        
        try:
            self.update_progress(0, "Быстрый расчет...")
            x, y, z = self.approx_position
            self.update_progress(50, "Преобразование координат...")
            lat, lon, height, iterations = self.converter.xyz_to_llh_high_precision(x, y, z)
            self.update_progress(100, "Готово!")
            
            result = self.format_quick_result(x, y, z, lat, lon, height, iterations)
            self.show_result(result)
            self.status_var.set("✅ Быстрый расчет завершен")
            
        except Exception as e:
            self.update_progress(0, "Ошибка!")
            messagebox.showerror("Ошибка", f"Ошибка при быстром расчете: {e}")
            self.status_var.set("❌ Ошибка при расчете")
    
    def precise_calculate(self):
        """Точный расчет с использованием PPP"""
        if not self.obs_data:
            messagebox.showwarning("Предупреждение", "Сначала прочитайте файл наблюдений")
            return
        
        try:
            self.status_var.set("🎯 Выполняется точный расчет PPP...")
            
            # Запуск расчета с настройками по умолчанию
            result = self.calculate_ppp_position_enhanced(max_iterations=200, tolerance=1e-8)
            
            self.show_result(result)
            self.status_var.set("✅ Точный расчет завершен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при точном расчете: {e}")
            self.status_var.set("❌ Ошибка при расчете")
    
    def precise_calculate_enhanced(self):
        """Расширенный расчет с настройками"""
        if not self.obs_data:
            messagebox.showwarning("Предупреждение", "Сначала прочитайте файл наблюдений")
            return
        
        try:
            # Диалог настройки параметров
            settings = self.show_iteration_settings_dialog()
            if not settings:
                return
                
            max_iterations = settings['max_iterations']
            tolerance = settings['tolerance']
            method = settings['method']
            
            self.status_var.set(f"🎯 Запуск {method} расчета ({max_iterations} итераций)...")
            
            # Запуск улучшенного расчета
            result = self.calculate_ppp_position_enhanced(max_iterations, tolerance, method)
            
            self.show_result(result)
            self.status_var.set(f"✅ {method} расчет завершен ({max_iterations} итераций)")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при расширенном расчете: {e}")
            self.status_var.set("❌ Ошибка при расчете")
    
    def show_iteration_settings_dialog(self):
        """Диалог настройки параметров итераций"""
        dialog = tk.Toplevel(self.root)
        dialog.title("⚙️ Настройки точного расчета")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Центрирование диалога
        dialog.geometry(f"+{self.root.winfo_x()+200}+{self.root.winfo_y()+100}")
        
        # Переменные
        max_iter_var = tk.IntVar(value=500)
        tolerance_var = tk.DoubleVar(value=1e-8)
        method_var = tk.StringVar(value="Адаптивный")
        
        ttk.Label(dialog, text="Настройки точного расчета", 
                 font=("Arial", 14, "bold")).pack(pady=15)
        
        # Максимальное количество итераций
        iter_frame = ttk.LabelFrame(dialog, text="Количество итераций", padding="10")
        iter_frame.pack(fill=tk.X, padx=20, pady=8)
        
        ttk.Label(iter_frame, text="Максимальное количество итераций:").pack(anchor=tk.W)
        
        iter_scale = ttk.Scale(iter_frame, from_=50, to=2000, variable=max_iter_var, 
                              orient=tk.HORIZONTAL)
        iter_scale.pack(fill=tk.X, pady=8)
        
        iter_value_frame = ttk.Frame(iter_frame)
        iter_value_frame.pack(fill=tk.X)
        
        ttk.Label(iter_value_frame, textvariable=max_iter_var, 
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Label(iter_value_frame, text=" итераций").pack(side=tk.LEFT, padx=(5, 0))
        
        # Точность сходимости
        tolerance_frame = ttk.LabelFrame(dialog, text="Точность сходимости", padding="10")
        tolerance_frame.pack(fill=tk.X, padx=20, pady=8)
        
        ttk.Label(tolerance_frame, text="Порог сходимости (метры):").pack(anchor=tk.W)
        
        tolerance_scale = ttk.Scale(tolerance_frame, from_=1e-10, to=1e-5, 
                                   variable=tolerance_var, orient=tk.HORIZONTAL)
        tolerance_scale.pack(fill=tk.X, pady=8)
        
        tolerance_value_frame = ttk.Frame(tolerance_frame)
        tolerance_value_frame.pack(fill=tk.X)
        
        ttk.Label(tolerance_value_frame, textvariable=tolerance_var, 
                 font=("Arial", 10)).pack(side=tk.LEFT)
        ttk.Label(tolerance_value_frame, text=" метров").pack(side=tk.LEFT, padx=(5, 0))
        
        # Метод расчета
        method_frame = ttk.LabelFrame(dialog, text="Метод расчета", padding="10")
        method_frame.pack(fill=tk.X, padx=20, pady=8)
        
        methods = [
            ("🎯 Адаптивный (рекомендуется)", "Адаптивный"),
            ("⚡ Фиксированный шаг", "Фиксированный"),
            ("💎 Высокая точность", "Высокая точность"),
            ("🚀 Ультра-точность", "Ультра-точность")
        ]
        
        for text, value in methods:
            ttk.Radiobutton(method_frame, text=text, 
                           variable=method_var, value=value).pack(anchor=tk.W, pady=2)
        
        result = {}
        
        def on_ok():
            nonlocal result
            result = {
                'max_iterations': max_iter_var.get(),
                'tolerance': tolerance_var.get(),
                'method': method_var.get()
            }
            dialog.destroy()
        
        def on_cancel():
            nonlocal result
            result = None
            dialog.destroy()
        
        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="🚀 Запуск расчета", 
                  command=on_ok, style='Accent.TButton', width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Отмена", 
                  command=on_cancel, width=10).pack(side=tk.LEFT, padx=10)
        
        dialog.wait_window()
        return result
    
    def calculate_ppp_position_enhanced(self, max_iterations=500, tolerance=1e-8, method="Адаптивный"):
        """Улучшенный расчет PPP позиции"""
        if not self.approx_position:
            raise Exception("Нет приблизительных координат для итераций")
        
        x0, y0, z0 = self.approx_position
        
        # Настройка калькулятора в зависимости от метода
        if method == "Ультра-точность":
            max_iterations = 2000
            tolerance = 1e-12
        elif method == "Высокая точность":
            max_iterations = 1000
            tolerance = 1e-10
        
        # Запускаем расчет
        result = self.ppp_calculator.calculate_precise_position_enhanced(
            self.obs_data, 
            self.nav_data, 
            [x0, y0, z0],
            max_iterations=max_iterations,
            convergence_threshold=tolerance,
            progress_callback=self.update_progress
        )
        
        x_avg, y_avg, z_avg = result['position']
        lat, lon, height, conv_iterations = self.converter.xyz_to_llh_high_precision(x_avg, y_avg, z_avg)
        lat0, lon0, height0, _ = self.converter.xyz_to_llh_high_precision(x0, y0, z0)
        
        # Форматируем подробный отчет
        report = self.generate_detailed_report(result, lat, lon, height, lat0, lon0, height0, 
                                             method, max_iterations, conv_iterations)
        return report
    
    def generate_detailed_report(self, ppp_result, lat, lon, height, lat0, lon0, height0, 
                               method, max_iterations, conv_iterations):
        """Генерация подробного отчета о расчете"""
        x_avg, y_avg, z_avg = ppp_result['position']
        std_x, std_y, std_z = ppp_result['std_deviation']
        
        # Форматирование в градусы-минуты-секунды
        lat_dms = self.converter.decimal_to_dms(lat)
        lon_dms = self.converter.decimal_to_dms(lon)
        
        report = [
            "🎯 ТОЧНЫЙ РАСЧЕТ PPP (УСИЛЕННАЯ ВЕРСИЯ)",
            "=" * 50,
            f"Метод расчета: {method}",
            f"Максимальное количество итераций: {max_iterations}",
            f"Выполнено итераций: {ppp_result['iterations']}",
            f"Итераций преобразования: {conv_iterations}",
            f"Финальная невязка: {ppp_result['final_residual']:.8f} м",
            f"Достигнутая точность: {ppp_result['precision']:.8f} м",
            "",
            "📍 ИСХОДНЫЕ КООРДИНАТЫ:",
            f"  X: {self.approx_position[0]:14.4f} м",
            f"  Y: {self.approx_position[1]:14.4f} м", 
            f"  Z: {self.approx_position[2]:14.4f} м",
            f"  Широта:  {lat0:10.8f}°",
            f"  Долгота: {lon0:10.8f}°",
            f"  Высота:  {height0:8.4f} м",
            "",
            "🎯 УТОЧНЕННЫЕ КООРДИНАТЫ:",
            f"  X: {x_avg:14.4f} ± {std_x:.4f} м",
            f"  Y: {y_avg:14.4f} ± {std_y:.4f} м",
            f"  Z: {z_avg:14.4f} ± {std_z:.4f} м", 
            f"  Широта:  {lat:10.8f}°",
            f"  Долгота: {lon:10.8f}°",
            f"  Высота:  {height:8.4f} м",
            "",
            f"  Широта:  {lat_dms}",
            f"  Долгота: {lon_dms}",
            "",
            "📊 СТАТИСТИКА ТОЧНОСТИ:",
            f"  Стандартное отклонение X: {std_x:.8f} м",
            f"  Стандартное отклонение Y: {std_y:.8f} м", 
            f"  Стандартное отклонение Z: {std_z:.8f} м",
            f"  Общая СКО: {ppp_result['precision']:.8f} м",
            f"  Ковариация XY: {ppp_result['covariance'][0,1]:.8f}",
            "",
            "📈 ИСТОРИЯ СХОДИМОСТИ:",
            f"  Начальная невязка: {ppp_result['residuals_history'][0]:.6f} м",
            f"  Минимальное изменение: {min(ppp_result['convergence_history']):.8f} м",
            f"  Среднее изменение: {np.mean(ppp_result['convergence_history']):.8f} м",
            f"  Максимальное изменение: {max(ppp_result['convergence_history']):.6f} м",
            "",
            "🌐 ССЫЛКИ НА КАРТЫ:",
            f"  Google Maps: https://maps.google.com/?q={lat:.8f},{lon:.8f}",
            f"  Yandex Maps: https://yandex.ru/maps/?pt={lon:.8f},{lat:.8f}&z=18",
            f"  OpenStreetMap: https://www.openstreetmap.org/?mlat={lat:.8f}&mlon={lon:.8f}&zoom=18",
            "",
            "💡 ПРИМЕЧАНИЕ:",
            f"  Расчет выполнен методом {method}",
            f"  с увеличенным количеством итераций для",
            f"  достижения максимальной точности позиционирования."
        ]
        
        return "\n".join(report)
    
    def format_quick_result(self, x, y, z, lat, lon, height, iterations):
        """Форматирование результатов быстрого расчета"""
        lat_dms = self.converter.decimal_to_dms(lat)
        lon_dms = self.converter.decimal_to_dms(lon)
        
        return [
            "⚡ БЫСТРЫЙ РАСЧЕТ",
            "=" * 30,
            f"Метод: Приблизительные координаты из заголовка",
            f"Точность: 1 - 10 метров",
            f"Итераций преобразования: {iterations}",
            "",
            "📍 КООРДИНАТЫ ECEF:",
            f"  X: {x:14.4f} м",
            f"  Y: {y:14.4f} м",
            f"  Z: {z:14.4f} м",
            "",
            "🌍 ГЕОГРАФИЧЕСКИЕ КООРДИНАТЫ:",
            f"  Широта:  {lat:10.6f}°",
            f"  Долгота: {lon:10.6f}°", 
            f"  Высота:  {height:8.3f} м",
            "",
            f"  Широта:  {lat_dms}",
            f"  Долгота: {lon_dms}",
            "",
            "💡 ПРИМЕЧАНИЕ:",
            "  Эти координаты являются приблизительными и были",
            "  введены оператором при настройке приемника.",
            "  Для получения точных координат используйте PPP расчет.",
            "",
            "🌐 ССЫЛКИ НА КАРТЫ:",
            f"  Google Maps: https://maps.google.com/?q={lat:.6f},{lon:.6f}",
            f"  Yandex Maps: https://yandex.ru/maps/?pt={lon:.6f},{lat:.6f}&z=17"
        ]
    
    def show_result(self, result):
        """Показать результаты в текстовом поле"""
        if isinstance(result, list):
            result = "\n".join(result)
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, result)
    
    def save_results(self):
        """Сохранить результаты в файл"""
        filename = filedialog.asksaveasfilename(
            title="Сохранить результаты",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    results = self.result_text.get(1.0, tk.END)
                    f.write(f"RINEX Converter Results\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(results)
                self.status_var.set(f"💾 Результаты сохранены в {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении: {e}")
    
    def copy_results(self):
        """Копировать результаты в буфер обмена"""
        try:
            results = self.result_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(results)
            self.status_var.set("📋 Результаты скопированы в буфер обмена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при копировании: {e}")
    
    def clear_results(self):
        """Очистить результаты"""
        self.result_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.status_var.set("🗑️ Результаты очищены")

def main():
    """Запуск приложения"""
    try:
        root = tk.Tk()
        app = AdvancedRinexConverter(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()
