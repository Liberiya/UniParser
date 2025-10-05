"""
Тесты для парсера
"""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from parser.extractors import StaffDataExtractor
from parser.validators import DataValidator
from parser.main import UniversityParser


class TestStaffDataExtractor:
    """Тесты для извлечения данных о сотрудниках"""
    
    def setup_method(self):
        self.extractor = StaffDataExtractor()
    
    def test_extract_fio_regex(self):
        """Тест извлечения ФИО с помощью regex"""
        test_cases = [
            ("Иванов Иван Иванович", "Иванов Иван Иванович"),
            ("Петров Петр", "Петров Петр"),
            ("Сидоров А.В.", "Сидоров А.В."),
            ("", None),
            ("Не имя", None),
        ]
        
        for input_text, expected in test_cases:
            result = self.extractor._extract_fio_regex(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_extract_email(self):
        """Тест извлечения email"""
        test_cases = [
            ("ivanov@university.ru", "ivanov@university.ru"),
            ("Contact: petrov@msu.ru", "petrov@msu.ru"),
            ("Email: sidorov@spbu.ru", "sidorov@spbu.ru"),
            ("No email here", None),
            ("", None),
        ]
        
        for input_text, expected in test_cases:
            result = self.extractor.extract_email(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_extract_position(self):
        """Тест извлечения должности"""
        test_cases = [
            ("Иванов Иван Иванович, профессор", "профессор"),
            ("Петров Петр - доцент", "доцент"),
            ("Сидоров А.В. (старший преподаватель)", "старший преподаватель"),
            ("No position here", None),
            ("", None),
        ]
        
        for input_text, expected in test_cases:
            result = self.extractor.extract_position(input_text)
            if expected:
                assert result is not None, f"Failed for input: {input_text}"
                assert expected in result.lower(), f"Failed for input: {input_text}"
            else:
                assert result is None, f"Failed for input: {input_text}"


class TestDataValidator:
    """Тесты для валидации данных"""
    
    def setup_method(self):
        self.validator = DataValidator()
    
    def test_validate_email(self):
        """Тест валидации email"""
        test_cases = [
            ("ivanov@university.ru", True),
            ("petrov@msu.ru", True),
            ("invalid-email", False),
            ("@domain.com", False),
            ("user@", False),
            ("", False),
        ]
        
        for email, expected in test_cases:
            result = self.validator.validate_email(email)
            assert result == expected, f"Failed for email: {email}"
    
    def test_validate_fio(self):
        """Тест валидации ФИО"""
        test_cases = [
            ("Иванов Иван Иванович", True),
            ("Петров Петр", True),
            ("Сидоров А.В.", False),  # Сокращения не проходят
            ("иванов иван", False),  # Строчные буквы
            ("", False),
            ("Очень длинное имя которое не должно проходить валидацию", False),
        ]
        
        for fio, expected in test_cases:
            result = self.validator.validate_fio(fio)
            assert result == expected, f"Failed for FIO: {fio}"
    
    def test_validate_position(self):
        """Тест валидации должности"""
        test_cases = [
            ("профессор", True),
            ("доцент", True),
            ("старший преподаватель", True),
            ("заведующий кафедрой", True),
            ("random text", False),
            ("", False),
        ]
        
        for position, expected in test_cases:
            result = self.validator.validate_position(position)
            assert result == expected, f"Failed for position: {position}"
    
    def test_calculate_confidence(self):
        """Тест расчета confidence score"""
        # Высокая достоверность
        confidence = self.validator.calculate_confidence(
            "Иванов Иван Иванович",
            "ivanov@university.ru",
            "профессор",
            "https://university.ru/staff"
        )
        assert confidence > 0.7, "High confidence case failed"
        
        # Низкая достоверность
        confidence = self.validator.calculate_confidence(
            "Invalid Name",
            "invalid-email",
            "random text",
            "https://suspicious-site.com"
        )
        assert confidence < 0.3, "Low confidence case failed"
        
        # Проверяем границы
        assert 0.0 <= confidence <= 1.0, "Confidence out of bounds"


class TestUniversityParser:
    """Тесты для основного парсера"""
    
    def setup_method(self):
        self.parser = UniversityParser()
    
    def test_is_valid_internal_url(self):
        """Тест проверки внутренних URL"""
        base_url = "https://university.ru"
        
        test_cases = [
            ("https://university.ru/staff", True),
            ("https://university.ru/kafedra", True),
            ("https://other-site.com/staff", False),
            ("https://university.ru/file.pdf", False),
            ("http://university.ru/staff", True),
        ]
        
        for url, expected in test_cases:
            result = self.parser._is_valid_internal_url(url, base_url)
            assert result == expected, f"Failed for URL: {url}"
    
    def test_is_staff_container(self):
        """Тест определения контейнера с данными о сотруднике"""
        # Создаем mock элементы
        mock_element_professor = Mock()
        mock_element_professor.get_text.return_value = "Иванов Иван Иванович профессор ivanov@university.ru"
        
        mock_element_random = Mock()
        mock_element_random.get_text.return_value = "Random text without staff info"
        
        test_cases = [
            (mock_element_professor, True),
            (mock_element_random, False),
        ]
        
        for element, expected in test_cases:
            result = self.parser._is_staff_container(element)
            assert result == expected, f"Failed for element: {element.get_text()}"
    
    @pytest.mark.asyncio
    async def test_extract_from_text(self):
        """Тест извлечения данных из текста"""
        test_text = """
        Иванов Иван Иванович - профессор - ivanov@university.ru
        Петров Петр Петрович, доцент, petrov@msu.ru
        Сидоров А.В. (старший преподаватель) sidorov@spbu.ru
        """
        
        soup = BeautifulSoup(test_text, 'html.parser')
        results = await self.parser._extract_from_text(soup, "https://test.ru")
        
        assert len(results) >= 2, "Should extract at least 2 records"
        
        # Проверяем первую запись
        first_record = results[0]
        assert "Иванов" in first_record['fio']
        assert "профессор" in first_record['position']
        assert "ivanov@university.ru" in first_record['email']


@pytest.mark.asyncio
async def test_parser_integration():
    """Интеграционный тест парсера"""
    # Создаем тестовый HTML
    test_html = """
    <html>
    <body>
        <div class="staff-list">
            <div class="staff-item">
                <h3>Иванов Иван Иванович</h3>
                <p>профессор</p>
                <a href="mailto:ivanov@university.ru">ivanov@university.ru</a>
            </div>
            <div class="staff-item">
                <h3>Петров Петр Петрович</h3>
                <p>доцент</p>
                <a href="mailto:petrov@university.ru">petrov@university.ru</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(test_html, 'html.parser')
    parser = UniversityParser()
    
    results = await parser._extract_staff_data(soup, "https://test.ru")
    
    assert len(results) == 2, "Should extract 2 staff records"
    
    # Проверяем качество данных
    for result in results:
        assert result['fio'], "FIO should be present"
        assert result['position'], "Position should be present"
        assert result['email'], "Email should be present"
        assert result['confidence'] > 0.5, "Confidence should be reasonable"
