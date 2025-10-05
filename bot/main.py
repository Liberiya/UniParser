"""
Основной модуль Telegram бота
"""

import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from loguru import logger

from bot.handlers import register_handlers
from bot.middleware import register_middleware


async def start_bot():
    """Запуск бота"""
    # Получаем токен
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения")
    
    # Инициализируем базу данных
    # await init_database()  # Удалено
    
    # Создаем бота и диспетчер
    bot = Bot(token=token)
    
    # Настройка хранилища состояний
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            from redis.asyncio import Redis
            from aiogram.fsm.storage.redis import RedisStorage
            redis = Redis.from_url(redis_url)
            storage = RedisStorage(redis)
            logger.info("Using Redis for state storage")
        except ImportError:
            logger.warning("Redis not installed. Using MemoryStorage")
            storage = MemoryStorage()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using MemoryStorage")
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()
        logger.info("Using MemoryStorage for state storage")
    
    dp = Dispatcher(storage=storage)
    
    # Регистрируем middleware
    register_middleware(dp)
    
    # Регистрируем обработчики
    register_handlers(dp)
    
    # Проверяем, используется ли webhook
    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
    
    if webhook_url:
        # Настройка webhook
        await bot.set_webhook(
            url=f"{webhook_url}{webhook_path}",
            drop_pending_updates=True
        )
        
        # Создаем веб-сервер для webhook
        app = web.Application()
        webhook_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_handler.register(app, path=webhook_path)
        setup_application(app, dp, bot=bot)
        
        # Запускаем веб-сервер
        port = int(os.getenv("PORT", 8080))
        logger.info(f"Запуск webhook сервера на порту {port}")
        
        await web._run_app(app, host="0.0.0.0", port=port)
    else:
        # Обычный polling режим
        logger.info("Starting bot in polling mode...")
        await dp.start_polling(bot)


async def stop_bot():
    """Остановка бота"""
    logger.info("Остановка бота...")
    # Здесь можно добавить логику очистки ресурсов
