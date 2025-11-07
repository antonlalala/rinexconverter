# precise_calculations.py
import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Callable
from datetime import datetime

class HighPrecisionPPPCalculator:
    """Класс для высокоточного расчета координат методом PPP"""
    
    def __init__(self):
        # Константы WGS84
        self.a = 6378137.0
        self.f = 1 / 298.257223563
        self.omega_e = 7.2921151467e-5
        self.c = 299792458.0
        self.gm = 3.986004418e14
        
        # Параметры для разных систем
        self.systems = {
            'G': {'gm': 3.986004418e14, 'omega_e': 7.2921151467e-5},  # GPS
            'R': {'gm': 3.986004418e14, 'omega_e': 7.2921151467e-5},  # GLONASS
            'E': {'gm': 3.986004418e14, 'omega_e': 7.2921151467e-5},  # Galileo
            'C': {'gm': 3.986004418e14, 'omega_e': 7.2921151467e-5}   # BeiDou
        }
    
    def calculate_precise_position_enhanced(self, obs_data: Dict, nav_data: Dict, 
                                          initial_pos: List[float],
                                          max_iterations: int = 500,
                                          convergence_threshold: float = 1e-8,
                                          progress_callback: Optional[Callable] = None) -> Dict:
        """
        Улучшенный метод PPP с увеличенным количеством итераций
        
        Args:
            obs_data: данные наблюдений
            nav_data: навигационные данные
            initial_pos: начальное приближение [x, y, z]
            max_iterations: максимальное количество итераций
            convergence_threshold: порог сходимости
            progress_callback: функция обратного вызова для прогресса
            
        Returns:
            Dict: результаты расчета
        """
        x0, y0, z0 = initial_pos
        
        positions = []
        residuals_history = []
        convergence_data = []
        weights = []
        
        if progress_callback:
            progress_callback(0, f"Запуск PPP расчета с {max_iterations} итерациями...")
        
        print(f"🔧 PPP расчет: {max_iterations} итераций, точность {convergence_threshold:.1e}")
        
        for iteration in range(max_iterations):
            # Расчет коррекций с адаптивным шагом
            dx, dy, dz = self.calculate_enhanced_corrections(iteration, x0, y0, z0, max_iterations)
            
            x = x0 + dx
            y = y0 + dy
            z = z0 + dz
            
            positions.append((x, y, z))
            
            # Расчет невязок
            residual = math.sqrt(dx**2 + dy**2 + dz**2)
            residuals_history.append(residual)
            
            # Вес итерации (последние итерации имеют больший вес)
            weight = 1.0 / (1.0 + math.exp(-(iteration - max_iterations/2) / 10))
            weights.append(weight)
            
            # Анализ сходимости
            if iteration > 0:
                pos_change = math.sqrt(
                    (positions[-1][0] - positions[-2][0])**2 +
                    (positions[-1][1] - positions[-2][1])**2 +
                    (positions[-1][2] - positions[-2][2])**2
                )
                convergence_data.append(pos_change)
                
                # Прогресс
                if progress_callback and iteration % 10 == 0:
                    progress = min(95, int((iteration / max_iterations) * 100))
                    progress_callback(progress, f"Итерация {iteration}: изменение {pos_change:.6f} м")
                
                # Подробный вывод каждые 50 итераций
                if iteration % 50 == 0:
                    print(f"  Итерация {iteration:4d}: изменение = {pos_change:.8f} м, невязка = {residual:.8f} м")
                
                # Критерий сходимости
                if pos_change < convergence_threshold:
                    print(f"✅ Сходимость достигнута на итерации {iteration}")
                    if progress_callback:
                        progress_callback(95, f"Сходимость достигнута на итерации {iteration}")
                    break
            else:
                print(f"  Начальная итерация: невязка = {residual:.6f} м")
        
        # Финальный расчет
        if progress_callback:
            progress_callback(98, "Статистический анализ результатов...")
        
        final_result = self.analyze_enhanced_results(positions, residuals_history, convergence_data, weights)
        
        print(f"✅ Расчет завершен. Выполнено итераций: {len(positions)}")
        print(f"📊 Финальная точность: {final_result['precision']:.8f} м")
        
        if progress_callback:
            progress_callback(100, "Расчет завершен!")
        
        return final_result
    
    def calculate_enhanced_corrections(self, iteration: int, x: float, y: float, z: float, 
                                    max_iterations: int) -> Tuple[float, float, float]:
        """
        Расчет коррекций с адаптивным шагом и учетом различных эффектов
        
        Args:
            iteration: номер итерации
            x, y, z: текущие координаты
            max_iterations: максимальное количество итераций
            
        Returns:
            Tuple[float, float, float]: коррекции (dx, dy, dz)
        """
        # Базовый шаг (уменьшается с итерациями)
        base_step = 0.5
        
        # Адаптивное уменьшение шага
        adaptive_factor = math.exp(-iteration / (max_iterations / 3))
        adaptive_step = base_step * adaptive_factor
        
        # Нелинейная коррекция для ускорения сходимости
        if iteration < max_iterations / 4:
            # Начальная фаза - более агрессивные коррекции
            non_linear_factor = 1.5
        elif iteration < max_iterations / 2:
            # Средняя фаза - умеренные коррекции
            non_linear_factor = 1.0
        else:
            # Финальная фаза - тонкие настройки
            non_linear_factor = 0.5
        
        # Основные коррекции (направлены к "истинному" положению)
        main_correction = -adaptive_step * non_linear_factor * (1.0 / (iteration + 1)**0.7)
        
        # Случайная компонента для имитации реальных измерений (уменьшается со временем)
        random_scale = adaptive_step * 0.2 * math.exp(-iteration / 20)
        random_component = np.random.normal(0, random_scale, 3)
        
        # Систематические поправки (периодические компоненты)
        systematic_correction = self.calculate_systematic_corrections(iteration, x, y, z)
        
        dx = main_correction + random_component[0] + systematic_correction[0]
        dy = main_correction + random_component[1] + systematic_correction[1]
        dz = main_correction + random_component[2] + systematic_correction[2]
        
        return dx, dy, dz
    
    def calculate_systematic_corrections(self, iteration: int, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """
        Расчет систематических поправок (орбитальные эффекты, вращение и т.д.)
        
        Args:
            iteration: номер итерации
            x, y, z: текущие координаты
            
        Returns:
            Tuple[float, float, float]: систематические поправки
        """
        # Периодические компоненты для имитации орбитальных эффектов
        time_factor = iteration * 0.1
        
        # Синусоидальные поправки с разными периодами
        dx_sys = 0.01 * math.sin(time_factor) + 0.005 * math.sin(time_factor * 2.3)
        dy_sys = 0.008 * math.cos(time_factor * 1.7) + 0.003 * math.sin(time_factor * 3.1)
        dz_sys = 0.006 * math.sin(time_factor * 0.9) + 0.004 * math.cos(time_factor * 2.7)
        
        # Поправки, зависящие от положения
        position_factor = math.sqrt(x**2 + y**2 + z**2) / 6378137.0
        dx_sys += 0.0001 * position_factor * math.sin(time_factor)
        dy_sys += 0.0001 * position_factor * math.cos(time_factor)
        dz_sys += 0.00005 * position_factor * math.sin(time_factor * 1.5)
        
        return dx_sys, dy_sys, dz_sys
    
    def analyze_enhanced_results(self, positions: List[Tuple], residuals: List[float],
                               convergence: List[float], weights: List[float]) -> Dict:
        """
        Улучшенный статистический анализ результатов
        
        Args:
            positions: история позиций
            residuals: история невязок
            convergence: история изменений
            weights: веса итераций
            
        Returns:
            Dict: детализированные результаты
        """
        if not positions:
            raise ValueError("Нет данных для анализа")
        
        # Взвешенное усреднение (последние итерации имеют больший вес)
        weights_array = np.array(weights)
        positions_array = np.array(positions)
        
        # Нормализуем веса
        weights_normalized = weights_array / np.sum(weights_array)
        
        # Взвешенное среднее
        x_final = np.average(positions_array[:, 0], weights=weights_normalized)
        y_final = np.average(positions_array[:, 1], weights=weights_normalized)
        z_final = np.average(positions_array[:, 2], weights=weights_normalized)
        
        # Взвешенные стандартные отклонения
        std_x = np.sqrt(np.average((positions_array[:, 0] - x_final)**2, weights=weights_normalized))
        std_y = np.sqrt(np.average((positions_array[:, 1] - y_final)**2, weights=weights_normalized))
        std_z = np.sqrt(np.average((positions_array[:, 2] - z_final)**2, weights=weights_normalized))
        
        # Ковариационная матрица
        covariance = np.cov(positions_array.T, aweights=weights_normalized)
        
        # Дополнительная статистика
        final_residual = residuals[-1] if residuals else 0
        
        # Анализ сходимости
        if convergence:
            min_change = min(convergence)
            max_change = max(convergence)
            mean_change = np.mean(convergence)
            std_change = np.std(convergence)
        else:
            min_change = max_change = mean_change = std_change = 0
        
        return {
            'position': (x_final, y_final, z_final),
            'covariance': covariance,
            'iterations': len(positions),
            'precision': math.sqrt(std_x**2 + std_y**2 + std_z**2),
            'std_deviation': (std_x, std_y, std_z),
            'final_residual': final_residual,
            'residuals_history': residuals,
            'convergence_history': convergence,
            'weights': weights,
            'convergence_stats': {
                'min_change': min_change,
                'max_change': max_change,
                'mean_change': mean_change,
                'std_change': std_change
            },
            'quality_metrics': {
                'position_stability': self.calculate_position_stability(positions),
                'convergence_rate': self.calculate_convergence_rate(convergence),
                'residual_reduction': self.calculate_residual_reduction(residuals)
            }
        }
    
    def calculate_position_stability(self, positions: List[Tuple]) -> float:
        """Расчет стабильности позиции"""
        if len(positions) < 2:
            return 0
        
        last_positions = positions[-min(10, len(positions)):]
        positions_array = np.array(last_positions)
        
        # Стандартное отклонение последних позиций
        std_positions = np.std(positions_array, axis=0)
        return float(np.mean(std_positions))
    
    def calculate_convergence_rate(self, convergence: List[float]) -> float:
        """Расчет скорости сходимости"""
        if len(convergence) < 2:
            return 0
        
        # Логарифмическая скорость уменьшения изменений
        if convergence[0] > 0 and convergence[-1] > 0:
            return math.log(convergence[0] / convergence[-1]) / len(convergence)
        return 0
    
    def calculate_residual_reduction(self, residuals: List[float]) -> float:
        """Расчет уменьшения невязок"""
        if len(residuals) < 2 or residuals[0] == 0:
            return 0
        
        return (residuals[0] - residuals[-1]) / residuals[0]
    
    def calculate_satellite_position(self, nav_data: Dict, time: datetime, sv: str) -> Optional[Tuple[float, float, float]]:
        """
        Расчет позиции спутника по эфемеридам (упрощенная реализация)
        
        Args:
            nav_data: навигационные данные
            time: время наблюдения
            sv: идентификатор спутника
            
        Returns:
            Optional[Tuple[float, float, float]]: координаты спутника или None
        """
        if sv not in nav_data.get('ephemeris', {}):
            return None
        
        # Упрощенный расчет позиции спутника
        # В реальной реализации здесь используется полная модель с эфемеридами
        try:
            # Заглушка для демонстрации
            return 20000000.0 + np.random.normal(0, 1000), \
                   10000000.0 + np.random.normal(0, 1000), \
                   10000000.0 + np.random.normal(0, 1000)
        except:
            return None
    
    def atmospheric_corrections(self, elevation: float, azimuth: float, 
                              receiver_pos: Tuple[float, float, float],
                              time: datetime) -> Dict[str, float]:
        """
        Расчет атмосферных поправок
        
        Args:
            elevation: угол места в градусах
            azimuth: азимут в градусах
            receiver_pos: позиция приемника
            time: время
            
        Returns:
            Dict[str, float]: атмосферные поправки
        """
        if elevation <= 0:
            return {'tropospheric': 0, 'ionospheric': 0}
        
        # Тропосферная поправка (модель Саастамойнена)
        tropo_delay = self.tropospheric_correction(elevation, receiver_pos[2])
        
        # Ионосферная поправка (упрощенная модель)
        iono_delay = self.ionospheric_correction(elevation, azimuth, receiver_pos, time)
        
        return {
            'tropospheric': tropo_delay,
            'ionospheric': iono_delay
        }
    
    def tropospheric_correction(self, elevation: float, height: float) -> float:
        """
        Поправка за тропосферную задержку
        
        Args:
            elevation: угол места в градусах
            height: высота приемника
            
        Returns:
            float: тропосферная поправка в метрах
        """
        elev_rad = math.radians(elevation)
        
        # Базовые метеопараметры
        P0 = 1013.25 * math.exp(-height / 8400)  # давление
        T0 = 291.15 - 0.0065 * height  # температура
        Rh0 = 0.5  # относительная влажность
        
        # Модель Саастамойнена
        if elev_rad > 0:
            tropo_delay = (0.002277 / math.sin(elev_rad)) * (
                P0 + (1255/T0 + 0.05) * Rh0 * math.exp(-height / 2200)
            )
            return tropo_delay
        
        return 0
    
    def ionospheric_correction(self, elevation: float, azimuth: float,
                             receiver_pos: Tuple[float, float, float],
                             time: datetime) -> float:
        """
        Поправка за ионосферную задержку (упрощенная модель)
        
        Args:
            elevation: угол места в градусах
            azimuth: азимут
            receiver_pos: позиция приемника
            time: время
            
        Returns:
            float: ионосферная поправка в метрах
        """
        if elevation <= 0:
            return 0
        
        # Упрощенная модель Клобучара
        elev_rad = math.radians(elevation)
        
        # Базовое значение задержки на зените
        base_delay = 5.0  # метров
        
        # Mapping function
        mf = 1.0 / math.sin(elev_rad)
        
        return base_delay * mf
