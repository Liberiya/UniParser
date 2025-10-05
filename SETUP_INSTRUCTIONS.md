# Инструкция по настройке бота

## Проблема: Unauthorized Error

Ошибка "Telegram server says - Unauthorized" означает, что токен бота неверный или не установлен.

## Решение:

1. Создайте файл `.env` в корне проекта
2. Добавьте в него ваш токен бота:

```env
TELEGRAM_TOKEN=your_actual_bot_token_here
```

## Как получить токен бота:

1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте команду `/newbot`
4. Следуйте инструкциям для создания бота
5. Скопируйте полученный токен

## Пример .env файла:

```env
# Telegram Bot Token (получить у @BotFather)
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Настройки парсера
RATE_LIMIT_DELAY=2
MAX_PAGES_DEPTH=2
JS_RENDER_TIMEOUT=30
PARSING_TIMEOUT=120
CONFIDENCE_THRESHOLD=0.6

# База данных (SQLite по умолчанию)
DATABASE_URL=sqlite:///data/parser_bot.db

# Настройки логирования
LOG_LEVEL=INFO
DEVELOPER_MODE=false
```

## После настройки:

Запустите бота командой:
```bash
python main.py
```

Бот должен запуститься без ошибок и начать отвечать на команды в Telegram.
