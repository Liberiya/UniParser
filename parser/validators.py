"""
Модуль валидации данных
"""

import re
from typing import Optional
from urllib.parse import urlparse
from email_validator import validate_email, EmailNotValidError
from loguru import logger


class DataValidator:
    """Класс для валидации извлеченных данных"""
    
    def __init__(self):
        # Ключевые слова для должностей
        self.position_keywords = [
            'профессор', 'доцент', 'преподаватель', 'ассистент',
            'заведующий', 'заведующая', 'декан', 'заместитель',
            'старший', 'младший', 'ведущий', 'главный',
            'научный сотрудник', 'исследователь', 'лаборант',
            'инженер', 'техник', 'администратор', 'секретарь',
            'методист', 'директор', 'начальник', 'специалист',
            'консультант', 'руководитель', 'координатор', 'менеджер',
            'professor', 'associate', 'assistant', 'lecturer',
            'head', 'dean', 'director', 'researcher', 'scientist',
            'engineer', 'technician', 'administrator', 'secretary',
            'manager', 'coordinator', 'specialist'
        ]
        
        # Общие email домены (снижают confidence)
        self.common_email_domains = [
            'gmail.com', 'yandex.ru', 'mail.ru', 'yahoo.com',
            'hotmail.com', 'outlook.com', 'rambler.ru', 'bk.ru',
            'list.ru', 'inbox.ru', 'yandex.by', 'mail.ua'
        ]
        
        # Образовательные домены (повышают confidence)
        self.education_domains = [
            '.edu', '.ac.', 'university', 'institute', 'college',
            'msu.ru', 'spbu.ru', 'mipt.ru', 'hse.ru', 'itmo.ru',
            'msu.su', 'spbu.su', 'mipt.su', 'hse.su', 'itmo.su'
        ]
    
    def calculate_confidence(
        self, 
        fio: Optional[str], 
        email: Optional[str], 
        position: Optional[str], 
        source_url: str
    ) -> float:
        """Расчет confidence score для записи"""
        confidence = 0.0
        
        # Проверка email (+0.4 если валидный)
        if email and self.validate_email(email):
            confidence += 0.4
            
            # Дополнительные бонусы/штрафы за домен
            domain = email.split('@')[1].lower()
            if any(ed in domain for ed in self.education_domains):
                confidence += 0.1  # Образовательный домен
            elif domain in self.common_email_domains:
                confidence -= 0.2  # Общий домен
        
        # Проверка ФИО (+0.3 если валидное)
        if fio and self.validate_fio(fio):
            confidence += 0.3
            
            # Проверка соответствия email и ФИО
            if email and self.check_email_fio_match(email, fio):
                confidence += 0.1
        
        # Проверка должности (+0.2 если найдена)
        if position and self.validate_position(position):
            confidence += 0.2
        
        # Проверка источника (-0.3 если сомнительный)
        if not self.validate_source(source_url):
            confidence -= 0.3
        
        # Ограничиваем результат [0, 1]
        return max(0.0, min(1.0, confidence))
    
    def validate_email(self, email: str) -> bool:
        """Валидация email адреса"""
        if not email:
            return False
        
        try:
            # Используем email-validator для строгой проверки
            validate_email(email)
            return True
        except EmailNotValidError:
            # Fallback на простую regex проверку
            pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
            return bool(re.match(pattern, email))
    
    def validate_fio(self, fio: str) -> bool:
        """Валидация ФИО"""
        if not fio:
            return False
        
        # Проверяем, что это русские имена
        pattern = r'^[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?$'
        if not re.match(pattern, fio):
            return False
        
        # Проверяем длину (не слишком короткое и не слишком длинное)
        words = fio.split()
        if len(words) < 2 or len(words) > 3:
            return False
        
        # Проверяем длину каждого слова
        for word in words:
            if len(word) < 2 or len(word) > 20:
                return False
        
        return True
    
    def validate_position(self, position: str) -> bool:
        """Валидация должности"""
        if not position:
            return False
        
        position_lower = position.lower()
        
        # Проверяем наличие ключевых слов
        return any(keyword in position_lower for keyword in self.position_keywords)
    
    def validate_source(self, url: str) -> bool:
        """Валидация источника"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # Проверяем схему
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Проверяем домен
            if not parsed.netloc:
                return False
            
            # Проверяем, что это не подозрительные домены
            suspicious_domains = [
                'facebook.com', 'vk.com', 'instagram.com', 'twitter.com',
                'linkedin.com', 'youtube.com', 'tiktok.com', 'telegram.org'
            ]
            
            domain_lower = parsed.netloc.lower()
            if any(sd in domain_lower for sd in suspicious_domains):
                return False
            
            return True
            
        except Exception:
            return False
    
    def check_email_fio_match(self, email: str, fio: str) -> bool:
        """Проверка соответствия email и ФИО"""
        if not email or not fio:
            return False
        
        try:
            local_part = email.split('@')[0].lower()
            fio_words = fio.lower().split()
            
            # Проверяем различные варианты соответствия
            for word in fio_words:
                if word in local_part or local_part in word:
                    return True
            
            # Проверяем инициалы
            initials = ''.join([word[0] for word in fio_words])
            if initials in local_part:
                return True
            
            # Проверяем обратный порядок инициалов
            reversed_initials = ''.join([word[0] for word in reversed(fio_words)])
            if reversed_initials in local_part:
                return True
            
            return False
            
        except Exception:
            return False
    
    def validate_phone(self, phone: str) -> bool:
        """Валидация телефонного номера"""
        if not phone:
            return False
        
        # Убираем все нецифровые символы кроме +
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Проверяем российские номера
        if clean_phone.startswith('+7') and len(clean_phone) == 12:
            return True
        elif clean_phone.startswith('8') and len(clean_phone) == 11:
            return True
        elif len(clean_phone) == 10:
            return True
        
        return False
    
    def normalize_data(self, data: dict) -> dict:
        """Нормализация данных"""
        normalized = data.copy()
        
        # Нормализуем ФИО
        if 'fio' in normalized and normalized['fio']:
            normalized['fio'] = self.normalize_fio(normalized['fio'])
        
        # Нормализуем email
        if 'email' in normalized and normalized['email']:
            normalized['email'] = normalized['email'].lower().strip()
        
        # Нормализуем должность
        if 'position' in normalized and normalized['position']:
            normalized['position'] = self.normalize_position(normalized['position'])
        
        return normalized
    
    def normalize_fio(self, fio: str) -> str:
        """Нормализация ФИО"""
        if not fio:
            return ""
        
        # Убираем лишние пробелы и символы
        fio = re.sub(r'\s+', ' ', fio.strip())
        fio = re.sub(r'[.,]', '', fio)
        
        # Приводим к правильному регистру
        words = fio.split()
        normalized_words = []
        
        for word in words:
            if word:
                normalized_word = word[0].upper() + word[1:].lower()
                normalized_words.append(normalized_word)
        
        return ' '.join(normalized_words)
    
    def normalize_position(self, position: str) -> str:
        """Нормализация должности"""
        if not position:
            return ""
        
        # Убираем лишние пробелы
        position = re.sub(r'\s+', ' ', position.strip())
        
        # Приводим к нижнему регистру для стандартизации
        position_lower = position.lower()
        
        # Стандартизируем некоторые должности
        replacements = {
            'зав. кафедрой': 'заведующий кафедрой',
            'зав. кафедры': 'заведующий кафедрой',
            'зав. каф.': 'заведующий кафедрой',
            'ст. преподаватель': 'старший преподаватель',
            'ст. преп.': 'старший преподаватель',
            'мл. преподаватель': 'младший преподаватель',
            'мл. преп.': 'младший преподаватель',
            'науч. сотр.': 'научный сотрудник',
            'н.с.': 'научный сотрудник',
            'ведущий н.с.': 'ведущий научный сотрудник',
            'ст. н.с.': 'старший научный сотрудник',
            'мл. н.с.': 'младший научный сотрудник',
            'гл. н.с.': 'главный научный сотрудник'
        }
        
        for old, new in replacements.items():
            if old in position_lower:
                position = position.replace(old, new)
        
        return position
