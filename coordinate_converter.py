import math
import numpy as np
from typing import Tuple

class CoordinateConverter:
    """Класс для высокоточного преобразования координат"""
    
    def __init__(self):
        # Параметры эллипсоида WGS84
        self.a = 6378137.0  # большая полуось, м
        self.f = 1 / 298.257223563  # сжатие
        self.e2 = 2 * self.f - self.f ** 2  # квадрат эксцентриситета
        self.b = self.a * (1 - self.f)  # малая полуось
        
        # Другие параметры
        self.omega_e = 7.2921151467e-5  # угловая скорость Земли (рад/с)
    
    def xyz_to_llh_high_precision(self, x: float, y: float, z: float, 
                                max_iterations: int = 100, 
                                tolerance: float = 1e-15) -> Tuple[float, float, float, int]:
        """
        Высокоточное преобразование ECEF в географические координаты
        
        Args:
            x, y, z: координаты ECEF в метрах
            max_iterations: максимальное количество итераций
            tolerance: точность сходимости
            
        Returns:
            tuple: (широта_градусы, долгота_градусы, высота_метры, количество_итераций)
        """
        # Расчет долготы (не требует итераций)
        longitude = math.atan2(y, x)
        
        # Расчет широты и высоты (итерационный метод)
        p = math.sqrt(x * x + y * y)
        lat_prev = math.atan2(z, p * (1 - self.e2))
        
        iteration_count = 0
        for i in range(max_iterations):
            iteration_count = i + 1
            
            # Радиус кривизны в первом вертикале
            N = self.a / math.sqrt(1 - self.e2 * math.sin(lat_prev) ** 2)
            
            # Высота
            h = p / math.cos(lat_prev) - N
            
            # Новая широта
            lat = math.atan2(z, p * (1 - self.e2 * N / (N + h)))
            
            # Проверка сходимости
            if abs(lat - lat_prev) < tolerance:
                break
                
            lat_prev = lat
        else:
            # Достигнут лимит итераций
            print(f"⚠️ Преобразование: не достигнута точность {tolerance} за {max_iterations} итераций")
        
        latitude = lat_prev
        
        # Перевод радиан в градусы
        latitude_deg = math.degrees(latitude)
        longitude_deg = math.degrees(longitude)
        
        return latitude_deg, longitude_deg, h, iteration_count
    
    def llh_to_xyz(self, lat: float, lon: float, h: float) -> Tuple[float, float, float]:
        """
        Преобразование географических координат в ECEF
        
        Args:
            lat, lon: широта и долгота в градусах
            h: высота в метрах
            
        Returns:
            tuple: (x, y, z) координаты ECEF
        """
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        N = self.a / math.sqrt(1 - self.e2 * math.sin(lat_rad) ** 2)
        
        x = (N + h) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + h) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - self.e2) + h) * math.sin(lat_rad)
        
        return x, y, z
    
    def decimal_to_dms(self, decimal_degrees: float) -> str:
        """
        Преобразование десятичных градусов в градусы-минуты-секунды
        
        Args:
            decimal_degrees: градусы в десятичном формате
            
        Returns:
            str: строка в формате ГГ° ММ' СС.ССС"
        """
        degrees = int(decimal_degrees)
        minutes_decimal = abs(decimal_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        return f"{degrees:02d}° {minutes:02d}' {seconds:06.3f}\""
    
    def calculate_distance(self, x1: float, y1: float, z1: float, 
                         x2: float, y2: float, z2: float) -> float:
        """
        Расчет расстояния между двумя точками в ECEF
        
        Args:
            x1, y1, z1: координаты первой точки
            x2, y2, z2: координаты второй точки
            
        Returns:
            float: расстояние в метрах
        """
        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        
        return math.sqrt(dx * dx + dy * dy + dz * dz)
    
    def calculate_accuracy_ellipsoid(self, covariance: np.ndarray) -> dict:
        """
        Расчет эллипсоида ошибок из ковариационной матрицы
        
        Args:
            covariance: ковариационная матрица 3x3
            
        Returns:
            dict: параметры эллипсоида ошибок
        """
        # Собственные значения и векторы
        eigenvalues, eigenvectors = np.linalg.eig(covariance)
        
        # Полуоси эллипсоида (стандартные отклонения)
        semi_axes = np.sqrt(eigenvalues)
        
        return {
            'semi_axes': semi_axes,
            'eigenvectors': eigenvectors,
            'volume': (4/3) * math.pi * np.prod(semi_axes),
            'max_error': np.max(semi_axes),
            'min_error': np.min(semi_axes)
        }
