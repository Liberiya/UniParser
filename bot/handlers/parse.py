"""
Обработчики парсинга
"""

import asyncio
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from loguru import logger
import re

from bot.states import ParseStates
from bot.keyboards import get_parse_keyboard, get_staff_item_keyboard, get_confirmation_keyboard
from parser.main import UniversityParser
from database.operations import save_parsing_result, get_user_settings


async def parse_handler(message: Message, state: FSMContext):
    """Обработчик команды /parse"""
    user = message.from_user
    
    # Проверяем, есть ли URL в команде
    command_parts = message.text.split()
    if len(command_parts) > 1:
        url = command_parts[1]
        await parse_url_handler(message, state, url)
    else:
        await message.answer(
            "🔍 <b>Парсинг URL</b>\n\n"
            "Отправьте ссылку на страницу вуза для парсинга.\n\n"
            "<b>Примеры:</b>\n"
            "• Страница кафедры\n"
            "• Список сотрудников\n"
            "• Поисковая страница\n\n"
            "Просто отправьте URL в следующем сообщении:",
            reply_markup=get_parse_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(ParseStates.waiting_for_url)


async def parse_url_handler(message: Message, state: FSMContext, url: str = None):
    """Обработчик URL для парсинга"""
    if not url:
        url = message.text.strip()
    
    user = message.from_user
    
    # Валидация URL
    if not is_valid_url(url):
        await message.answer(
            "❌ <b>Неверный URL</b>\n\n"
            "Пожалуйста, отправьте корректную ссылку на сайт вуза.\n"
            "URL должен начинаться с http:// или https://",
            parse_mode="HTML"
        )
        return
    
    # Проверяем robots.txt
    if not await check_robots_txt(url):
        await message.answer(
            "⚠️ <b>Предупреждение</b>\n\n"
            "Сайт запрещает автоматический парсинг в robots.txt.\n"
            "Продолжить парсинг?",
            reply_markup=get_confirmation_keyboard("parse_anyway"),
            parse_mode="HTML"
        )
        await state.update_data(url=url)
        await state.set_state(ParseStates.waiting_for_confirmation)
        return
    
    # Начинаем парсинг
    await start_parsing(message, state, url)


async def start_parsing(message: Message, state: FSMContext, url: str):
    """Запуск процесса парсинга"""
    user = message.from_user
    
    # Получаем настройки пользователя
    settings = await get_user_settings(user.id)
    
    # Отправляем сообщение о начале парсинга
    parsing_msg = await message.answer(
        f"🚀 <b>Начинаю парсинг...</b>\n\n"
        f"URL: {url}\n"
        f"⏱ Ожидаемое время: {settings.get('parsing_timeout', 120)} сек\n"
        f"🔍 Глубина: {settings.get('max_depth', 2)} уровней\n"
        f"🌐 JS рендеринг: {'Включен' if settings.get('js_render', True) else 'Отключен'}\n\n"
        f"⏳ Пожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    try:
        # Создаем парсер
        parser = UniversityParser(
            rate_limit_delay=settings.get('rate_limit_delay', 2),
            max_depth=settings.get('max_depth', 2),
            js_render_timeout=settings.get('js_render_timeout', 30),
            parsing_timeout=settings.get('parsing_timeout', 120),
            confidence_threshold=settings.get('confidence_threshold', 0.6)
        )
        
        # Запускаем парсинг
        results = await parser.parse_url(url)
        
        # Сохраняем результаты
        parsing_id = await save_parsing_result(
            user_id=user.id,
            url=url,
            results=results,
            settings=settings
        )
        
        # Обновляем сообщение с результатами
        await show_parsing_results(parsing_msg, results, parsing_id)
        
    except Exception as e:
        logger.error(f"Ошибка парсинга для пользователя {user.id}: {e}")
        await parsing_msg.edit_text(
            f"❌ <b>Ошибка парсинга</b>\n\n"
            f"Произошла ошибка при парсинге URL: {url}\n\n"
            f"<b>Ошибка:</b> {str(e)}\n\n"
            f"Попробуйте другой URL или обратитесь к администратору.",
            parse_mode="HTML"
        )
    
    finally:
        await state.clear()


async def show_parsing_results(message: Message, results: list, parsing_id: int):
    """Показ результатов парсинга"""
    if not results:
        await message.edit_text(
            "🔍 <b>Результаты парсинга</b>\n\n"
            "К сожалению, не удалось найти данные о сотрудниках.\n\n"
            "Возможные причины:\n"
            "• Страница не содержит информации о сотрудниках\n"
            "• Необходим JS рендеринг (попробуйте включить в настройках)\n"
            "• Сайт использует нестандартную структуру\n\n"
            "Попробуйте другой URL или измените настройки парсинга.",
            parse_mode="HTML"
        )
        return
    
    # Группируем результаты по confidence
    high_confidence = [r for r in results if r.get('confidence', 0) >= 0.7]
    medium_confidence = [r for r in results if 0.5 <= r.get('confidence', 0) < 0.7]
    low_confidence = [r for r in results if r.get('confidence', 0) < 0.5]
    
    text = f"✅ <b>Парсинг завершен!</b>\n\n"
    text += f"📊 <b>Найдено записей:</b> {len(results)}\n"
    text += f"• Высокая достоверность: {len(high_confidence)}\n"
    text += f"• Средняя достоверность: {len(medium_confidence)}\n"
    text += f"• Низкая достоверность: {len(low_confidence)}\n\n"
    
    # Показываем первые несколько результатов
    for i, result in enumerate(results[:5]):
        text += f"<b>{i+1}. {result.get('fio', 'Неизвестно')}</b>\n"
        text += f"Должность: {result.get('position', 'Не указана')}\n"
        text += f"Email: {result.get('email', 'Не указан')}\n"
        text += f"Достоверность: {result.get('confidence', 0):.2f}\n\n"
    
    if len(results) > 5:
        text += f"... и еще {len(results) - 5} записей\n\n"
    
    text += "Используйте кнопки ниже для работы с результатами:"
    
    await message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_results_keyboard(parsing_id)
    )


def is_valid_url(url: str) -> bool:
    """Проверка валидности URL"""
    pattern = re.compile(
        r'^https?://'  # http:// или https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # домен
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return pattern.match(url) is not None


async def check_robots_txt(url: str) -> bool:
    """Проверка robots.txt"""
    try:
        import requests
        from urllib.parse import urljoin, urlparse
        
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            robots_content = response.text.lower()
            # Простая проверка на запрет для всех ботов
            if "user-agent: *" in robots_content and "disallow: /" in robots_content:
                return False
        
        return True
    except Exception as e:
        logger.warning(f"Не удалось проверить robots.txt: {e}")
        return True  # Если не можем проверить, разрешаем


def get_results_keyboard(parsing_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для результатов парсинга"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📋 Показать все",
        callback_data=f"show_all_{parsing_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="📁 Экспорт CSV",
        callback_data=f"export_csv_{parsing_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="🔍 Проверить вручную",
        callback_data=f"manual_check_{parsing_id}"
    ))
    
    builder.adjust(1)
    return builder.as_markup()
