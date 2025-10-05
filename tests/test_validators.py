"""
Тесты для валидаторов
"""

import pytest
from parser.validators import DataValidator


class TestDataValidator:
    """Тесты для валидации данных"""
    
    def setup_method(self):
        self.validator = DataValidator()
    
    def test_email_validation(self):
        """Тест валидации email адресов"""
        valid_emails = [
            "ivanov@university.ru",
            "petrov@msu.ru",
            "sidorov@spbu.ru",
            "test@example.com",
            "user.name@domain.co.uk"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "",
            "user@domain.",
            "user..name@domain.com"
        ]
        
        for email in valid_emails:
            assert self.validator.validate_email(email), f"Email {email} should be valid"
        
        for email in invalid_emails:
            assert not self.validator.validate_email(email), f"Email {email} should be invalid"
    
    def test_fio_validation(self):
        """Тест валидации ФИО"""
        valid_fios = [
            "Иванов Иван Иванович",
            "Петров Петр",
            "Сидорова Анна Владимировна",
            "Козлов Алексей"
        ]
        
        invalid_fios = [
            "иванов иван",  # строчные буквы
            "Иванов",  # только фамилия
            "Иванов И.И.",  # сокращения
            "Очень длинное имя которое не должно проходить валидацию",
            "",
            "123 456 789"  # цифры
        ]
        
        for fio in valid_fios:
            assert self.validator.validate_fio(fio), f"FIO {fio} should be valid"
        
        for fio in invalid_fios:
            assert not self.validator.validate_fio(fio), f"FIO {fio} should be invalid"
    
    def test_position_validation(self):
        """Тест валидации должностей"""
        valid_positions = [
            "профессор",
            "доцент",
            "старший преподаватель",
            "заведующий кафедрой",
            "декан факультета",
            "научный сотрудник",
            "ассистент"
        ]
        
        invalid_positions = [
            "random text",
            "студент",
            "аспирант",
            "",
            "123456"
        ]
        
        for position in valid_positions:
            assert self.validator.validate_position(position), f"Position {position} should be valid"
        
        for position in invalid_positions:
            assert not self.validator.validate_position(position), f"Position {position} should be invalid"
    
    def test_source_validation(self):
        """Тест валидации источников"""
        valid_sources = [
            "https://university.ru/staff",
            "http://msu.ru/kafedra",
            "https://example.edu/faculty",
            "https://test.org/department"
        ]
        
        invalid_sources = [
            "ftp://example.com",
            "javascript:void(0)",
            "mailto:test@example.com",
            "https://facebook.com/profile",
            "https://vk.com/page",
            "",
            "not-a-url"
        ]
        
        for source in valid_sources:
            assert self.validator.validate_source(source), f"Source {source} should be valid"
        
        for source in invalid_sources:
            assert not self.validator.validate_source(source), f"Source {source} should be invalid"
    
    def test_confidence_calculation(self):
        """Тест расчета confidence score"""
        # Высокая достоверность
        high_confidence = self.validator.calculate_confidence(
            "Иванов Иван Иванович",
            "ivanov@university.ru",
            "профессор",
            "https://university.ru/staff"
        )
        assert high_confidence > 0.7, "High confidence case failed"
        
        # Средняя достоверность
        medium_confidence = self.validator.calculate_confidence(
            "Петров Петр",
            "petrov@university.ru",
            "доцент",
            "https://university.ru/staff"
        )
        assert 0.5 <= medium_confidence <= 0.8, "Medium confidence case failed"
        
        # Низкая достоверность
        low_confidence = self.validator.calculate_confidence(
            "Invalid Name",
            "invalid-email",
            "random text",
            "https://suspicious-site.com"
        )
        assert low_confidence < 0.3, "Low confidence case failed"
        
        # Проверяем границы
        assert 0.0 <= low_confidence <= 1.0, "Confidence out of bounds"
        assert 0.0 <= medium_confidence <= 1.0, "Confidence out of bounds"
        assert 0.0 <= high_confidence <= 1.0, "Confidence out of bounds"
    
    def test_email_fio_match(self):
        """Тест проверки соответствия email и ФИО"""
        # Соответствующие пары
        matching_cases = [
            ("ivanov@university.ru", "Иванов Иван"),
            ("petrov.p@msu.ru", "Петров Петр"),
            ("sidorov@spbu.ru", "Сидоров Алексей"),
            ("i.ivanov@university.ru", "Иванов Иван")
        ]
        
        # Несоответствующие пары
        non_matching_cases = [
            ("admin@university.ru", "Иванов Иван"),
            ("test@university.ru", "Петров Петр"),
            ("info@msu.ru", "Сидоров Алексей")
        ]
        
        for email, fio in matching_cases:
            assert self.validator.check_email_fio_match(email, fio), f"Email {email} should match FIO {fio}"
        
        for email, fio in non_matching_cases:
            assert not self.validator.check_email_fio_match(email, fio), f"Email {email} should not match FIO {fio}"
    
    def test_phone_validation(self):
        """Тест валидации телефонных номеров"""
        valid_phones = [
            "+7 (495) 123-45-67",
            "8-495-123-45-67",
            "+7 495 123 45 67",
            "495-123-45-67",
            "+7(495)1234567"
        ]
        
        invalid_phones = [
            "123-45-67",  # слишком короткий
            "+1-555-123-4567",  # не российский
            "abc-def-ghi",  # буквы
            "",  # пустой
            "123"  # слишком короткий
        ]
        
        for phone in valid_phones:
            assert self.validator.validate_phone(phone), f"Phone {phone} should be valid"
        
        for phone in invalid_phones:
            assert not self.validator.validate_phone(phone), f"Phone {phone} should be invalid"
    
    def test_normalize_fio(self):
        """Тест нормализации ФИО"""
        test_cases = [
            ("иванов иван иванович", "Иванов Иван Иванович"),
            ("ПЕТРОВ ПЕТР", "Петров Петр"),
            ("Сидоров а.в.", "Сидоров А.В."),
            ("  козлов   алексей  ", "Козлов Алексей"),
            ("", "")
        ]
        
        for input_fio, expected in test_cases:
            result = self.validator.normalize_fio(input_fio)
            assert result == expected, f"Failed for input: {input_fio}"
    
    def test_normalize_position(self):
        """Тест нормализации должностей"""
        test_cases = [
            ("зав. кафедрой", "заведующий кафедрой"),
            ("ст. преподаватель", "старший преподаватель"),
            ("мл. преп.", "младший преподаватель"),
            ("науч. сотр.", "научный сотрудник"),
            ("ведущий н.с.", "ведущий научный сотрудник"),
            ("профессор", "профессор")  # без изменений
        ]
        
        for input_position, expected in test_cases:
            result = self.validator.normalize_position(input_position)
            assert result == expected, f"Failed for input: {input_position}"
    
    def test_normalize_data(self):
        """Тест нормализации данных"""
        input_data = {
            'fio': 'иванов иван иванович',
            'email': 'IVANOV@UNIVERSITY.RU',
            'position': 'зав. кафедрой'
        }
        
        result = self.validator.normalize_data(input_data)
        
        assert result['fio'] == "Иванов Иван Иванович"
        assert result['email'] == "ivanov@university.ru"
        assert result['position'] == "заведующий кафедрой"
    
    def test_education_domains(self):
        """Тест определения образовательных доменов"""
        education_emails = [
            "ivanov@msu.ru",
            "petrov@spbu.ru",
            "sidorov@mipt.ru",
            "test@university.edu",
            "user@college.ac.uk"
        ]
        
        common_emails = [
            "ivanov@gmail.com",
            "petrov@yandex.ru",
            "sidorov@mail.ru",
            "test@yahoo.com"
        ]
        
        for email in education_emails:
            confidence = self.validator.calculate_confidence(
                "Иванов Иван",
                email,
                "профессор",
                "https://university.ru"
            )
            # Образовательные домены должны давать бонус к confidence
            assert confidence > 0.5, f"Education email {email} should have high confidence"
        
        for email in common_emails:
            confidence = self.validator.calculate_confidence(
                "Иванов Иван",
                email,
                "профессор",
                "https://university.ru"
            )
            # Общие домены должны снижать confidence
            assert confidence < 0.8, f"Common email {email} should have lower confidence"
