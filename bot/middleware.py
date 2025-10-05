"""
Middleware для Telegram бота
"""

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

# from database.operations import get_or_create_user  # Удалено


class UserMiddleware:
    """Middleware для работы с пользователями"""
    
    async def __call__(self, handler, event, data):
        """Обработка события"""
        user = None
        
        # Получаем пользователя из события
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        
        if user:
            # Просто добавляем пользователя в данные (без БД)
            data['user'] = user
            
            logger.debug(f"Обработка сообщения от пользователя {user.id}")
        
        return await handler(event, data)


class LoggingMiddleware:
    """Middleware для логирования"""
    
    async def __call__(self, handler, event, data):
        """Логирование события"""
        if isinstance(event, Message):
            logger.info(
                f"Сообщение от {event.from_user.id} (@{event.from_user.username}): "
                f"{event.text[:50]}{'...' if len(event.text) > 50 else ''}"
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                f"Callback от {event.from_user.id} (@{event.from_user.username}): "
                f"{event.data}"
            )
        
        return await handler(event, data)


class RateLimitMiddleware:
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self):
        self.user_last_request = {}
        self.min_interval = 1.0  # Минимальный интервал между запросами (секунды)
    
    async def __call__(self, handler, event, data):
        """Проверка rate limit"""
        import time
        
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        
        if user_id:
            current_time = time.time()
            last_request_time = self.user_last_request.get(user_id, 0)
            
            if current_time - last_request_time < self.min_interval:
                # Слишком частые запросы
                logger.warning(f"Rate limit превышен для пользователя {user_id}")
                
                if isinstance(event, Message):
                    await event.answer(
                        "⏳ Слишком частые запросы! Подождите немного.",
                        parse_mode="HTML"
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "⏳ Слишком частые запросы! Подождите немного.",
                        show_alert=True
                    )
                
                return
            
            # Обновляем время последнего запроса
            self.user_last_request[user_id] = current_time
        
        return await handler(event, data)


def register_middleware(dp: Dispatcher):
    """Регистрация всех middleware"""
    # Порядок важен! Middleware выполняются в порядке регистрации
    
    # 1. Логирование (первым, чтобы логировать все события)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # 2. Rate limiting
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    
    # 3. Работа с пользователями (последним, чтобы иметь доступ к данным)
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    
    logger.info("All middleware registered")
