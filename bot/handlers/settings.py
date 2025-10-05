"""
Обработчики настроек
"""

from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.keyboards import get_settings_keyboard
from bot.states import SettingsStates
# from database.operations import get_user_settings, update_user_settings  # Удалено


async def settings_handler(message: Message, state: FSMContext):
    """Обработчик команды /settings"""
    user = message.from_user
    
    # Настройки по умолчанию (без БД)
    text = "⚙️ <b>Настройки парсера</b>\n\n"
    text += f"⏱ <b>Rate Limit:</b> 2.0 сек\n"
    text += f"🔍 <b>Глубина парсинга:</b> 2 уровней\n"
    text += f"🌐 <b>JS рендеринг:</b> Включен\n"
    text += f"⏰ <b>Таймаут JS:</b> 30 сек\n"
    text += f"🎯 <b>Confidence threshold:</b> 0.6\n"
    text += f"⏳ <b>Общий таймаут:</b> 120 сек\n\n"
    text += "Настройки временно недоступны (без БД)."
    
    await message.answer(
        text,
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML"
    )


async def update_settings_handler(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик обновления настроек"""
    await callback_query.answer("Настройки временно недоступны (без БД)", show_alert=True)


async def handle_rate_limit_input(message: Message, state: FSMContext):
    """Обработка ввода rate limit"""
    await message.answer("Настройки временно недоступны (без БД)")
    await state.clear()


async def handle_depth_input(message: Message, state: FSMContext):
    """Обработка ввода глубины парсинга"""
    await message.answer("Настройки временно недоступны (без БД)")
    await state.clear()


async def handle_confidence_input(message: Message, state: FSMContext):
    """Обработка ввода confidence threshold"""
    await message.answer("Настройки временно недоступны (без БД)")
    await state.clear()
