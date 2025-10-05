"""
Модуль для извлечения данных о сотрудниках
"""

import re
from typing import Optional, List
from bs4 import BeautifulSoup, Tag
from loguru import logger

try:
    import spacy
    from natasha import NamesExtractor
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spacy and natasha not installed. NER functions unavailable.")


class StaffDataExtractor:
    """Класс для извлечения данных о сотрудниках"""
    
    def __init__(self):
        self.names_extractor = None
        self.nlp = None
        
        # Инициализируем NER если доступен
        if SPACY_AVAILABLE:
            try:
                self.names_extractor = NamesExtractor()
                # Пробуем загрузить русскую модель spacy
                try:
                    self.nlp = spacy.load("ru_core_news_sm")
                except OSError:
                    logger.warning("Русская модель spacy не найдена. Используем только regex.")
            except Exception as e:
                logger.warning(f"Ошибка инициализации NER: {e}")
    
    def extract_fio(self, text: str) -> Optional[str]:
        """Извлечение ФИО из текста"""
        # Сначала пробуем NER
        if self.names_extractor:
            try:
                matches = self.names_extractor(text)
                if matches:
                    # Берем первое найденное имя
                    name = matches[0].fact
                    if hasattr(name, 'first') and hasattr(name, 'last'):
                        fio_parts = []
                        if name.last:
                            fio_parts.append(name.last)
                        if name.first:
                            fio_parts.append(name.first)
                        if hasattr(name, 'middle') and name.middle:
                            fio_parts.append(name.middle)
                        return ' '.join(fio_parts)
            except Exception as e:
                logger.debug(f"Ошибка NER извлечения ФИО: {e}")
        
        # Fallback на regex
        return self._extract_fio_regex(text)
    
    def _extract_fio_regex(self, text: str) -> Optional[str]:
        """Извлечение ФИО с помощью регулярных выражений"""
        # Паттерны для русских имен
        patterns = [
            # Фамилия Имя Отчество
            r'\b([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)\b',
            # Фамилия Имя
            r'\b([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)\b',
            # Имя Фамилия (менее надежно)
            r'\b([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Берем первое совпадение
                match = matches[0]
                if len(match) == 3:
                    return f"{match[0]} {match[1]} {match[2]}"
                elif len(match) == 2:
                    return f"{match[0]} {match[1]}"
        
        return None
    
    def extract_email(self, text: str, element: Tag = None) -> Optional[str]:
        """Извлечение email адреса"""
        emails = []
        
        # Ищем в тексте
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text_emails = re.findall(email_pattern, text)
        emails.extend(text_emails)
        
        # Ищем в HTML элементах (mailto ссылки)
        if element:
            mailto_links = element.find_all('a', href=re.compile(r'^mailto:'))
            for link in mailto_links:
                href = link.get('href', '')
                email = href.replace('mailto:', '').split('?')[0]
                if email:
                    emails.append(email)
        
        # Возвращаем первый найденный email
        return emails[0] if emails else None
    
    def extract_position(self, text: str) -> Optional[str]:
        """Извлечение должности"""
        # Словарь должностей в вузах
        positions = [
            'профессор', 'доцент', 'старший преподаватель', 'преподаватель',
            'ассистент', 'заведующий кафедрой', 'заведующая кафедрой',
            'заведующий', 'заведующая', 'декан', 'заместитель декана',
            'заместитель заведующего', 'заместитель заведующей',
            'научный сотрудник', 'ведущий научный сотрудник',
            'старший научный сотрудник', 'младший научный сотрудник',
            'главный научный сотрудник', 'лаборант', 'инженер',
            'техник', 'администратор', 'секретарь', 'методист',
            'заместитель директора', 'директор', 'начальник',
            'заместитель начальника', 'специалист', 'консультант',
            'руководитель', 'координатор', 'менеджер',
            
            # Английские эквиваленты
            'professor', 'associate professor', 'assistant professor',
            'lecturer', 'senior lecturer', 'head of department',
            'dean', 'vice dean', 'researcher', 'scientist',
            'engineer', 'technician', 'administrator', 'secretary',
            'director', 'manager', 'coordinator', 'specialist'
        ]
        
        text_lower = text.lower()
        
        # Ищем должности в тексте
        for position in positions:
            if position in text_lower:
                # Пытаемся найти полную фразу
                pattern = rf'\b{re.escape(position)}\b'
                match = re.search(pattern, text_lower)
                if match:
                    # Извлекаем контекст вокруг должности
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end].strip()
                    
                    # Очищаем контекст от лишних символов
                    context = re.sub(r'[^\w\s\-\.]', ' ', context)
                    context = re.sub(r'\s+', ' ', context)
                    
                    return context
        
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Извлечение телефонного номера"""
        phone_patterns = [
            r'\+7\s?\(?\d{3}\)?\s?\d{3}[- ]?\d{2}[- ]?\d{2}',
            r'8\s?\(?\d{3}\)?\s?\d{3}[- ]?\d{2}[- ]?\d{2}',
            r'\(\d{3}\)\s?\d{3}[- ]?\d{2}[- ]?\d{2}',
            r'\d{3}[- ]?\d{3}[- ]?\d{2}[- ]?\d{2}'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        
        return None
    
    def extract_department(self, text: str) -> Optional[str]:
        """Извлечение названия кафедры/факультета"""
        department_keywords = [
            'кафедра', 'факультет', 'институт', 'департамент',
            'отдел', 'лаборатория', 'центр', 'центр',
            'department', 'faculty', 'institute', 'laboratory',
            'center', 'centre'
        ]
        
        text_lower = text.lower()
        
        for keyword in department_keywords:
            pattern = rf'\b{keyword}\s+[^,\n\.]+'
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0).strip()
        
        return None
    
    def clean_text(self, text: str) -> str:
        """Очистка текста от лишних символов"""
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем специальные символы, но оставляем основные
        text = re.sub(r'[^\w\s\-\.\,\:\;\(\)]', '', text)
        
        return text.strip()
    
    def normalize_fio(self, fio: str) -> str:
        """Нормализация ФИО"""
        if not fio:
            return ""
        
        # Убираем лишние пробелы
        fio = re.sub(r'\s+', ' ', fio.strip())
        
        # Убираем точки и запятые
        fio = re.sub(r'[.,]', '', fio)
        
        # Приводим к правильному регистру
        words = fio.split()
        normalized_words = []
        
        for word in words:
            if word:
                # Первая буква заглавная, остальные строчные
                normalized_word = word[0].upper() + word[1:].lower()
                normalized_words.append(normalized_word)
        
        return ' '.join(normalized_words)
