"""
Тестовые URL для проверки парсера
"""

# Тестовые URL российских вузов для проверки парсера
TEST_URLS = {
    "МГУ им. М.В. Ломоносова": {
        "url": "https://cs.msu.ru/ru/staff",
        "description": "Факультет вычислительной математики и кибернетики - список сотрудников",
        "expected_fields": ["fio", "position", "email"],
        "difficulty": "medium"
    },
    
    "СПбГУ": {
        "url": "https://math.spbu.ru/ru/staff",
        "description": "Математико-механический факультет - сотрудники",
        "expected_fields": ["fio", "position", "email"],
        "difficulty": "medium"
    },
    
    "МФТИ": {
        "url": "https://mipt.ru/education/chairs/fupm/staff/",
        "description": "Факультет управления и прикладной математики - преподаватели",
        "expected_fields": ["fio", "position", "email"],
        "difficulty": "hard"
    },
    
    "НИУ ВШЭ": {
        "url": "https://cs.hse.ru/staff",
        "description": "Факультет компьютерных наук - сотрудники",
        "expected_fields": ["fio", "position", "email"],
        "difficulty": "easy"
    },
    
    "ИТМО": {
        "url": "https://itmo.ru/ru/staff",
        "description": "Университет ИТМО - преподаватели",
        "expected_fields": ["fio", "position", "email"],
        "difficulty": "medium"
    },
    
    "МГТУ им. Н.Э. Баумана": {
        "url": "https://bmstu.ru/faculty/fakultet-informatiki-i-sistem-upravleniya/prepodavateli",
        "description": "Факультет информатики и систем управления - преподаватели",
        "expected_fields": ["fio", "position", "email"],
        "difficulty": "hard"
    },
    
    "РГУ им. А.Н. Косыгина": {
        "url": "https://kosygin-rgu.ru/faculty/informatika-i-sistemy-upravleniya/prepodavateli",
        "description": "Факультет информатики и систем управления - преподаватели",
        "expected_fields": ["fio", "position", "email"],
        "difficulty": "medium"
    },
    
    "МАИ": {
        "url": "https://mai.ru/education/faculties/fakultet-informatiki-i-sistem-upravleniya/prepodavateli",
        "description": "Факультет информатики и систем управления - преподаватели",
        "expected_fields": ["fio", "position", "email"],
        "difficulty": "hard"
    }
}

# URL для тестирования различных сценариев
TEST_SCENARIOS = {
    "simple_html": {
        "url": "https://example.edu/simple-staff",
        "description": "Простая HTML страница без JS",
        "expected_parser": "html_only"
    },
    
    "js_rendered": {
        "url": "https://example.edu/js-staff",
        "description": "Страница с динамическим контентом",
        "expected_parser": "js_required"
    },
    
    "table_format": {
        "url": "https://example.edu/table-staff",
        "description": "Данные в табличном формате",
        "expected_parser": "table_parser"
    },
    
    "list_format": {
        "url": "https://example.edu/list-staff",
        "description": "Данные в виде списка",
        "expected_parser": "list_parser"
    },
    
    "card_format": {
        "url": "https://example.edu/card-staff",
        "description": "Данные в виде карточек",
        "expected_parser": "card_parser"
    }
}

# Ожидаемые результаты для тестирования
EXPECTED_RESULTS = {
    "min_records": 5,  # Минимальное количество записей
    "min_confidence": 0.6,  # Минимальный confidence для валидных записей
    "required_fields": ["fio", "email"],  # Обязательные поля
    "optional_fields": ["position", "phone", "department"],  # Опциональные поля
    "max_processing_time": 120,  # Максимальное время обработки (секунды)
}

# Настройки для тестирования
TEST_SETTINGS = {
    "rate_limit_delay": 1.0,  # Быстрая обработка для тестов
    "max_depth": 2,
    "js_render_timeout": 30,
    "parsing_timeout": 60,
    "confidence_threshold": 0.5
}

def get_test_urls_by_difficulty(difficulty: str = None):
    """Получение тестовых URL по сложности"""
    if difficulty:
        return {name: data for name, data in TEST_URLS.items() if data["difficulty"] == difficulty}
    return TEST_URLS

def get_random_test_url():
    """Получение случайного тестового URL"""
    import random
    name, data = random.choice(list(TEST_URLS.items()))
    return name, data["url"]

def validate_test_results(results: list, url_info: dict) -> dict:
    """Валидация результатов тестирования"""
    validation = {
        "total_records": len(results),
        "valid_records": 0,
        "high_confidence_records": 0,
        "has_required_fields": 0,
        "avg_confidence": 0.0,
        "errors": []
    }
    
    if not results:
        validation["errors"].append("No records found")
        return validation
    
    total_confidence = 0
    for result in results:
        # Проверяем обязательные поля
        has_required = all(field in result and result[field] for field in EXPECTED_RESULTS["required_fields"])
        if has_required:
            validation["has_required_fields"] += 1
        
        # Проверяем confidence
        confidence = result.get("confidence", 0)
        total_confidence += confidence
        
        if confidence >= EXPECTED_RESULTS["min_confidence"]:
            validation["valid_records"] += 1
        
        if confidence >= 0.8:
            validation["high_confidence_records"] += 1
    
    validation["avg_confidence"] = total_confidence / len(results)
    
    # Проверяем критерии
    if validation["total_records"] < EXPECTED_RESULTS["min_records"]:
        validation["errors"].append(f"Too few records: {validation['total_records']} < {EXPECTED_RESULTS['min_records']}")
    
    if validation["avg_confidence"] < EXPECTED_RESULTS["min_confidence"]:
        validation["errors"].append(f"Low average confidence: {validation['avg_confidence']:.2f} < {EXPECTED_RESULTS['min_confidence']}")
    
    if validation["has_required_fields"] < len(results) * 0.8:
        validation["errors"].append(f"Too many records missing required fields: {validation['has_required_fields']}/{len(results)}")
    
    return validation