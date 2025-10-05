"""
Основной парсер для университетов
"""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag
from loguru import logger

from parser.base import BaseParser
from parser.extractors import StaffDataExtractor
from parser.validators import DataValidator


class UniversityParser(BaseParser):
    """Парсер для сайтов российских университетов"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.extractor = StaffDataExtractor()
        self.validator = DataValidator()
    
    async def _extract_staff_data(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Извлечение данных о сотрудниках"""
        results = []
        
        # Ищем различные структуры данных
        staff_containers = self._find_staff_containers(soup)
        
        for container in staff_containers:
            try:
                staff_data = await self._extract_from_container(container, url)
                if staff_data:
                    results.append(staff_data)
            except Exception as e:
                logger.warning(f"Ошибка при извлечении данных из контейнера: {e}")
                continue
        
        # Если не нашли структурированные данные, пробуем извлечь из текста
        if not results:
            results = await self._extract_from_text(soup, url)
        
        return results
    
    def _find_staff_containers(self, soup: BeautifulSoup) -> List[Tag]:
        """Поиск контейнеров с данными о сотрудниках"""
        containers = []
        
        # Ищем различные селекторы
        selectors = [
            # Таблицы
            'table tr',
            'tbody tr',
            
            # Списки
            'ul li',
            'ol li',
            
            # Карточки
            '.staff-item',
            '.employee',
            '.person',
            '.teacher',
            '.professor',
            '.staff',
            '.team-member',
            '.faculty-member',
            
            # Div контейнеры
            'div[class*="staff"]',
            'div[class*="employee"]',
            'div[class*="person"]',
            'div[class*="teacher"]',
            'div[class*="faculty"]',
            
            # Статьи
            'article',
            '.card',
            '.profile',
            
            # Специфичные для вузов
            '.kafedra',
            '.department',
            '.chair',
            '.prepodavatel',
            '.sotrudnik'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if self._is_staff_container(element):
                    containers.append(element)
        
        return containers
    
    def _is_staff_container(self, element: Tag) -> bool:
        """Проверка, является ли элемент контейнером с данными о сотруднике"""
        text = element.get_text().lower()
        
        # Проверяем наличие ключевых слов
        staff_keywords = [
            'профессор', 'доцент', 'преподаватель', 'ассистент',
            'заведующий', 'заведующая', 'декан', 'заместитель',
            'старший', 'младший', 'ведущий', 'главный',
            'научный сотрудник', 'исследователь', 'лаборант',
            'professor', 'associate', 'assistant', 'lecturer',
            'head', 'dean', 'director', 'researcher'
        ]
        
        # Проверяем наличие email
        has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        
        # Проверяем наличие ФИО (русские имена)
        has_russian_name = bool(re.search(r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b', text))
        
        return (
            any(keyword in text for keyword in staff_keywords) or
            (has_email and has_russian_name) or
            (has_russian_name and len(text.split()) >= 3)
        )
    
    async def _extract_from_container(self, container: Tag, url: str) -> Dict[str, Any]:
        """Извлечение данных из контейнера"""
        # Извлекаем текст контейнера
        text = container.get_text(strip=True)
        
        # Извлекаем HTML для raw_snippet
        raw_html = str(container)[:500]  # Ограничиваем размер
        
        # Извлекаем данные
        fio = self.extractor.extract_fio(text)
        email = self.extractor.extract_email(text, container)
        position = self.extractor.extract_position(text)
        
        # Валидируем данные
        confidence = self.validator.calculate_confidence(fio, email, position, url)
        
        # Проверяем, что данные достаточно качественные
        if confidence < 0.3:
            return None
        
        return {
            'fio': fio,
            'position': position,
            'email': email,
            'source': url,
            'confidence': confidence,
            'raw_html_snippet': raw_html
        }
    
    async def _extract_from_text(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Извлечение данных из текста страницы"""
        results = []
        
        # Получаем весь текст страницы
        text = soup.get_text()
        
        # Ищем паттерны ФИО + должность + email
        patterns = [
            # Паттерн: ФИО - должность - email
            r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)\s*[-–—]\s*([^-\n]+?)\s*[-–—]\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            
            # Паттерн: ФИО, должность, email
            r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)\s*,\s*([^,\n]+?)\s*,\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            
            # Паттерн: ФИО (должность) email
            r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)\s*\(([^)]+)\)\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                fio = match.group(1).strip()
                position = match.group(2).strip()
                email = match.group(3).strip()
                
                # Валидируем данные
                confidence = self.validator.calculate_confidence(fio, email, position, url)
                
                if confidence >= 0.3:
                    results.append({
                        'fio': fio,
                        'position': position,
                        'email': email,
                        'source': url,
                        'confidence': confidence,
                        'raw_html_snippet': match.group(0)[:500]
                    })
        
        return results
