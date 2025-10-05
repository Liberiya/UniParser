#!/usr/bin/env python3
"""
Главный файл для запуска University Staff Parser Bot
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/bot.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Создаем директории для логов и данных
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

async def main():
    """Основная функция запуска бота"""
    try:
        from bot.main import start_bot
        await start_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    # Проверяем наличие токена
    if not os.getenv("TELEGRAM_TOKEN"):
        logger.error("TELEGRAM_TOKEN not found in environment variables!")
        logger.info("Create .env file and add TELEGRAM_TOKEN=your_bot_token")
        sys.exit(1)
    
    logger.info("Starting University Staff Parser Bot...")
    asyncio.run(main())
