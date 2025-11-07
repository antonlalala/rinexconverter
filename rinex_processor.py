import math
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class RinexProcessor:
    """Класс для обработки RINEX файлов"""
    
    def __init__(self):
        self.supported_versions = ['2.11', '3.02', '3.04', '3.05']
    
    def read_rinex_obs_file(self, filename: str) -> Dict:
        """
        Чтение RINEX файла наблюдений
        
        Args:
            filename: путь к файлу
            
        Returns:
            Dict: словарь с данными наблюдений
        """
        data = {
            'header': {},
            'observations': [],
            'satellites': set(),
            'time_range': None
        }
        
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            header_end = False
            header_lines = []
            observation_data = []
            
            for i, line in enumerate(lines):
                if not header_end:
                    header_lines.append(line)
                    if 'END OF HEADER' in line:
                        header_end = True
                        data['header'] = self.parse_rinex_header(header_lines)
                    continue
                
                # Парсинг данных наблюдений
                if line.strip():
                    observation_data.append(line)
            
            # Упрощенный парсинг данных наблюдений
            data['observations'] = self.parse_observation_data(observation_data, data['header'])
            
            return data
            
        except Exception as e:
            raise Exception(f"Ошибка чтения OBS файла {filename}: {e}")
    
    def read_rinex_nav_file(self, filename: str) -> Dict:
        """
        Чтение RINEX файла навигации
        
        Args:
            filename: путь к файлу
            
        Returns:
            Dict: словарь с навигационными данными
        """
        data = {
            'header': {},
            'ephemeris': {},
            'ionospheric_corr': {},
            'time_corr': {}
        }
        
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            header_end = False
            header_lines = []
            navigation_data = []
            
            for i, line in enumerate(lines):
                if not header_end:
                    header_lines.append(line)
                    if 'END OF HEADER' in line:
                        header_end = True
                        data['header'] = self.parse_rinex_header(header_lines)
                    continue
                
                # Сбор навигационных данных
                navigation_data.append(line)
            
            # Парсинг навигационных данных
            data['ephemeris'] = self.parse_navigation_data(navigation_data)
            
            return data
            
        except Exception as e:
            raise Exception(f"Ошибка чтения NAV файла {filename}: {e}")
    
    def parse_rinex_header(self, header_lines: List[str]) -> Dict:
        """
        Парсинг заголовка RINEX файла
        
        Args:
            header_lines: строки заголовка
            
        Returns:
            Dict: распарсенный заголовок
        """
        header = {}
        
        for line in header_lines:
            # Приблизительные координаты
            if 'APPROX POSITION XYZ' in line:
                coords = self.extract_coordinates(line)
                if coords:
                    header['approx_position'] = coords
            
            # Типы наблюдений
            elif '# / TYPES OF OBSERV' in line:
                obs_types = self.extract_observation_types(line)
                if obs_types:
                    header['observation_types'] = obs_types
            
            # Версия RINEX
            elif 'RINEX VERSION / TYPE' in line:
                header['version'] = line[0:9].strip()
                header['file_type'] = line[20:40].strip()
            
            # Название станции
            elif 'MARKER NAME' in line:
                header['marker_name'] = line[0:60].strip()
            
            # Номер станции
            elif 'MARKER NUMBER' in line:
                header['marker_number'] = line[0:60].strip()
            
            # Интервал наблюдений
            elif 'INTERVAL' in line:
                try:
                    header['interval'] = float(line[0:10].strip())
                except ValueError:
                    pass
        
        return header
    
    def extract_coordinates(self, line: str) -> Optional[List[float]]:
        """
        Извлечение координат из строки
        
        Args:
            line: строка с координатами
            
        Returns:
            Optional[List[float]]: список координат [x, y, z] или None
        """
        parts = line.split()
        coords = []
        
        for part in parts:
            try:
                coord = float(part)
                coords.append(coord)
            except ValueError:
                continue
        
        return coords[:3] if len(coords) >= 3 else None
    
    def extract_observation_types(self, line: str) -> List[str]:
        """
        Извлечение типов наблюдений
        
        Args:
            line: строка с типами наблюдений
            
        Returns:
            List[str]: список типов наблюдений
        """
        # Первое число - количество типов наблюдений
        try:
            num_types = int(line[0:6].strip())
        except ValueError:
            return []
        
        types = []
        current_line = line[6:].strip()
        
        # Извлекаем типы наблюдений (каждый по 2 символа)
        for i in range(0, len(current_line), 2):
            if len(types) >= num_types:
                break
            obs_type = current_line[i:i+2].strip()
            if obs_type:
                types.append(obs_type)
        
        return types
    
    def parse_observation_data(self, observation_lines: List[str], header: Dict) -> List[Dict]:
        """
        Упрощенный парсинг данных наблюдений
        
        Args:
            observation_lines: строки с наблюдениями
            header: заголовок файла
            
        Returns:
            List[Dict]: список наблюдений
        """
        observations = []
        
        # В реальной реализации здесь должен быть полный парсинг
        # Для демонстрации возвращаем упрощенные данные
        for i, line in enumerate(observation_lines[:100]):  # Ограничиваем для производительности
            if line.startswith('>'):
                # Строка с временной меткой
                epoch_data = self.parse_epoch_header(line)
                if epoch_data:
                    observations.append(epoch_data)
        
        return observations
    
    def parse_epoch_header(self, line: str) -> Optional[Dict]:
        """
        Парсинг заголовка эпохи
        
        Args:
            line: строка заголовка эпохи
            
        Returns:
            Optional[Dict]: данные эпохи или None
        """
        try:
            year = int(line[2:6])
            month = int(line[7:9])
            day = int(line[10:12])
            hour = int(line[13:15])
            minute = int(line[16:18])
            second = float(line[19:25])
            
            epoch_time = datetime(year, month, day, hour, minute, int(second))
            
            return {
                'time': epoch_time,
                'epoch_flag': int(line[26:29]),
                'num_satellites': int(line[29:32])
            }
        except ValueError:
            return None
    
    def parse_navigation_data(self, navigation_lines: List[str]) -> Dict:
        """
        Парсинг навигационных данных
        
        Args:
            navigation_lines: строки с навигационными данными
            
        Returns:
            Dict: эфемериды спутников
        """
        ephemeris = {}
        
        # Упрощенная реализация парсинга эфемерид
        i = 0
        while i < len(navigation_lines):
            line = navigation_lines[i]
            
            # Проверяем, является ли строка заголовком эфемерид
            if len(line) > 5 and line[0] in ['G', 'R', 'E', 'C']:  # GPS, GLONASS, Galileo, BeiDou
                try:
                    sv = line[0:3].strip()
                    
                    # Пропускаем оставшиеся строки эфемерид (7 строк для GPS)
                    i += 8
                    
                    # Сохраняем упрощенные данные
                    ephemeris[sv] = {
                        'satellite': sv,
                        'data_lines': navigation_lines[i-7:i+1]
                    }
                    
                except (ValueError, IndexError):
                    i += 1
            else:
                i += 1
        
        return ephemeris
    
    def validate_rinex_file(self, filename: str) -> Tuple[bool, str]:
        """
        Валидация RINEX файла
        
        Args:
            filename: путь к файлу
            
        Returns:
            Tuple[bool, str]: (валиден, сообщение)
        """
        try:
            with open(filename, 'r') as f:
                first_line = f.readline()
                
            if 'RINEX' not in first_line:
                return False, "Не RINEX файл"
                
            # Проверка версии
            version = first_line[0:9].strip()
            if version not in self.supported_versions:
                return False, f"Неподдерживаемая версия: {version}"
                
            return True, f"Версия {version} поддерживается"
            
        except Exception as e:
            return False, f"Ошибка валидации: {e}"
