"""
Обработчики настроек
"""

from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.keyboards import get_settings_keyboard
from bot.states import SettingsStates
from database.operations import get_user_settings, update_user_settings


async def settings_handler(message: Message, state: FSMContext):
    """Обработчик команды /settings"""
    user = message.from_user
    
    # Получаем текущие настройки
    settings = get_user_settings(user.id)
    
    text = "⚙️ <b>Настройки парсера</b>\n\n"
    text += f"⏱ <b>Rate Limit:</b> {settings.get('rate_limit_delay', 2.0)} сек\n"
    text += f"🔍 <b>Глубина парсинга:</b> {settings.get('max_depth', 2)} уровней\n"
    text += f"🌐 <b>JS рендеринг:</b> {'Включен' if settings.get('js_render_enabled', True) else 'Отключен'}\n"
    text += f"⏰ <b>Таймаут JS:</b> {settings.get('js_render_timeout', 30)} сек\n"
    text += f"🎯 <b>Confidence threshold:</b> {settings.get('confidence_threshold', 0.6)}\n"
    text += f"⏳ <b>Общий таймаут:</b> {settings.get('parsing_timeout', 120)} сек\n\n"
    text += "Выберите параметр для изменения:"
    
    await message.answer(
        text,
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML"
    )


async def update_settings_handler(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик обновления настроек"""
    user = callback_query.from_user
    action = callback_query.data.split('_')[1]
    
    if action == "rate_limit":
        await callback_query.message.edit_text(
            "⏱ <b>Настройка Rate Limit</b>\n\n"
            "Введите задержку между запросами в секундах (0.5 - 10.0):\n\n"
            "<b>Рекомендуемые значения:</b>\n"
            "• 1.0 - быстрый парсинг (может быть заблокирован)\n"
            "• 2.0 - стандартная скорость\n"
            "• 5.0 - медленный, но безопасный парсинг",
            parse_mode="HTML"
        )
        await state.set_state(SettingsStates.waiting_for_rate_limit)
        
    elif action == "depth":
        await callback_query.message.edit_text(
            "🔍 <b>Настройка глубины парсинга</b>\n\n"
            "Введите количество уровней для обхода (1 - 5):\n\n"
            "<b>Объяснение:</b>\n"
            "• 1 - только указанная страница\n"
            "• 2 - страница + найденные ссылки\n"
            "• 3+ - более глубокий обход\n\n"
            "<b>Внимание:</b> Большая глубина увеличивает время парсинга",
            parse_mode="HTML"
        )
        await state.set_state(SettingsStates.waiting_for_depth)
        
    elif action == "js_render":
        # Переключаем JS рендеринг
        current_settings = get_user_settings(user.id)
        new_value = not current_settings.get('js_render_enabled', True)
        
        update_user_settings(user.id, {'js_render_enabled': new_value})
        
        await callback_query.answer(
            f"JS рендеринг {'включен' if new_value else 'отключен'}",
            show_alert=True
        )
        
        # Обновляем сообщение
        await settings_handler(callback_query.message, state)
        
    elif action == "confidence":
        await callback_query.message.edit_text(
            "🎯 <b>Настройка Confidence Threshold</b>\n\n"
            "Введите минимальный порог достоверности (0.1 - 1.0):\n\n"
            "<b>Объяснение:</b>\n"
            "• 0.1 - показывать все найденные записи\n"
            "• 0.5 - показывать записи средней достоверности\n"
            "• 0.7 - показывать только высококачественные записи\n"
            "• 0.9 - показывать только очень надежные записи",
            parse_mode="HTML"
        )
        await state.set_state(SettingsStates.waiting_for_confidence)
    
    await callback_query.answer()


async def handle_rate_limit_input(message: Message, state: FSMContext):
    """Обработка ввода rate limit"""
    try:
        value = float(message.text.strip())
        
        if not (0.5 <= value <= 10.0):
            await message.answer(
                "❌ Неверное значение!\n\n"
                "Введите число от 0.5 до 10.0",
                parse_mode="HTML"
            )
            return
        
        # Обновляем настройки
        update_user_settings(message.from_user.id, {'rate_limit_delay': value})
        
        await message.answer(
            f"✅ Rate Limit установлен: {value} сек",
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите число (например: 2.0)",
            parse_mode="HTML"
        )


async def handle_depth_input(message: Message, state: FSMContext):
    """Обработка ввода глубины парсинга"""
    try:
        value = int(message.text.strip())
        
        if not (1 <= value <= 5):
            await message.answer(
                "❌ Неверное значение!\n\n"
                "Введите число от 1 до 5",
                parse_mode="HTML"
            )
            return
        
        # Обновляем настройки
        update_user_settings(message.from_user.id, {'max_depth': value})
        
        await message.answer(
            f"✅ Глубина парсинга установлена: {value} уровней",
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите целое число (например: 2)",
            parse_mode="HTML"
        )


async def handle_confidence_input(message: Message, state: FSMContext):
    """Обработка ввода confidence threshold"""
    try:
        value = float(message.text.strip())
        
        if not (0.1 <= value <= 1.0):
            await message.answer(
                "❌ Неверное значение!\n\n"
                "Введите число от 0.1 до 1.0",
                parse_mode="HTML"
            )
            return
        
        # Обновляем настройки
        update_user_settings(message.from_user.id, {'confidence_threshold': value})
        
        await message.answer(
            f"✅ Confidence threshold установлен: {value}",
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите число (например: 0.6)",
            parse_mode="HTML"
        )
