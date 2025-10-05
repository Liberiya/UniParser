"""
Обработчики валидации данных
"""

from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.states import ValidationStates
# from database.operations import validate_staff_record, get_staff_records  # Удалено


async def validate_handler(message: Message, state: FSMContext):
    """Обработчик команды /validate"""
    await message.answer(
        "🔍 <b>Ручная валидация данных</b>\n\n"
        "Отправьте данные в формате:\n"
        "<code>ФИО|email|должность|URL</code>\n\n"
        "<b>Пример:</b>\n"
        "<code>Иванов Иван Иванович|ivanov@university.ru|профессор|https://example.edu</code>\n\n"
        "Или используйте кнопки для валидации найденных записей.",
        parse_mode="HTML"
    )
    await state.set_state(ValidationStates.waiting_for_manual_input)


async def manual_validation_handler(message: Message, state: FSMContext):
    """Обработчик ручной валидации"""
    try:
        # Парсим введенные данные
        parts = message.text.strip().split('|')
        
        if len(parts) != 4:
            await message.answer(
                "❌ <b>Неверный формат!</b>\n\n"
                "Используйте формат:\n"
                "<code>ФИО|email|должность|URL</code>\n\n"
                "<b>Пример:</b>\n"
                "<code>Иванов Иван Иванович|ivanov@university.ru|профессор|https://example.edu</code>",
                parse_mode="HTML"
            )
            return
        
        fio, email, position, url = [part.strip() for part in parts]
        
        # Валидируем данные
        validation_result = validate_manual_data(fio, email, position, url)
        
        if validation_result['is_valid']:
            await message.answer(
                f"✅ <b>Данные валидны!</b>\n\n"
                f"<b>ФИО:</b> {fio}\n"
                f"<b>Email:</b> {email}\n"
                f"<b>Должность:</b> {position}\n"
                f"<b>URL:</b> {url}\n"
                f"<b>Confidence:</b> {validation_result['confidence']:.2f}",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Данные не прошли валидацию</b>\n\n"
                f"<b>Проблемы:</b>\n" + "\n".join(validation_result['errors']),
                parse_mode="HTML"
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при ручной валидации: {e}")
        await message.answer(
            "❌ Произошла ошибка при валидации данных",
            parse_mode="HTML"
        )
        await state.clear()


def validate_manual_data(fio: str, email: str, position: str, url: str) -> dict:
    """Валидация вручную введенных данных"""
    errors = []
    confidence = 0.0
    
    # Валидация ФИО
    if not fio or len(fio.split()) < 2:
        errors.append("• ФИО должно содержать минимум 2 слова")
    else:
        confidence += 0.3
    
    # Валидация email
    import re
    email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    if not re.match(email_pattern, email):
        errors.append("• Неверный формат email")
    else:
        confidence += 0.4
    
    # Валидация должности
    if not position or len(position.strip()) < 3:
        errors.append("• Должность слишком короткая")
    else:
        confidence += 0.2
    
    # Валидация URL
    if not url.startswith(('http://', 'https://')):
        errors.append("• URL должен начинаться с http:// или https://")
    else:
        confidence += 0.1
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'confidence': min(confidence, 1.0)
    }


async def validate_correct_callback(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Корректно'"""
    await callback_query.answer("Валидация временно недоступна (без БД)", show_alert=True)


async def validate_incorrect_callback(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Неверно'"""
    await callback_query.answer("Валидация временно недоступна (без БД)", show_alert=True)


async def manual_check_handler(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Проверить вручную'"""
    await callback_query.answer("Валидация временно недоступна (без БД)", show_alert=True)


def get_validation_keyboard(record_id: int):
    """Клавиатура для валидации записи"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✅ Корректно",
        callback_data=f"validate_correct_{record_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Неверно",
        callback_data=f"validate_incorrect_{record_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="⏭ Пропустить",
        callback_data=f"skip_validation_{record_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_results"
    ))
    
    builder.adjust(2)
    return builder.as_markup()
