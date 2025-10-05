"""
Обработчики истории и экспорта
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.keyboards import get_history_keyboard, get_pagination_keyboard
# from database.operations import get_parsing_results, get_staff_records, log_export  # Удалено


async def history_handler(message: Message, state: FSMContext):
    """Обработчик команды /history"""
    user = message.from_user
    
    # Простое сообщение без БД
    await message.answer(
        "📋 <b>История парсинга</b>\n\n"
        "Функция истории временно недоступна.\n"
        "Результаты парсинга показываются сразу после обработки.\n\n"
        "Используйте команду /parse для парсинга новых URL.",
        reply_markup=get_history_keyboard(),
        parse_mode="HTML"
    )


async def export_csv_handler(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик экспорта в CSV"""
    await callback_query.answer("Функция экспорта временно недоступна", show_alert=True)


def create_csv_file(records: List[Dict[str, Any]]) -> io.BytesIO:
    """Создание CSV файла"""
    csv_buffer = io.StringIO()
    
    # Заголовки CSV
    fieldnames = [
        'fio', 'position', 'email', 'phone', 'department',
        'source_url', 'confidence', 'is_validated', 'is_correct'
    ]
    
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    
    # Записываем данные
    for record in records:
        writer.writerow({
            'fio': record.get('fio', ''),
            'position': record.get('position', ''),
            'email': record.get('email', ''),
            'phone': record.get('phone', ''),
            'department': record.get('department', ''),
            'source_url': record.get('source_url', ''),
            'confidence': record.get('confidence', 0.0),
            'is_validated': record.get('is_validated', False),
            'is_correct': record.get('is_correct', '')
        })
    
    # Конвертируем в BytesIO для отправки
    csv_bytes = io.BytesIO()
    csv_bytes.write(csv_buffer.getvalue().encode('utf-8-sig'))  # UTF-8 с BOM для Excel
    csv_bytes.seek(0)
    
    return csv_bytes


async def show_recent_results(callback_query: CallbackQuery, state: FSMContext):
    """Показ последних результатов"""
    await callback_query.answer("Функция истории временно недоступна", show_alert=True)


def get_recent_results_keyboard(results: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура для последних результатов"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    for result in results[:3]:  # Показываем только первые 3
        builder.add(InlineKeyboardButton(
            text=f"📋 Результат #{result['id']}",
            callback_data=f"show_result_{result['id']}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="📁 Экспорт всех",
        callback_data="export_all_csv"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_history"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


async def show_result_details(callback_query: CallbackQuery, state: FSMContext):
    """Показ деталей результата"""
    await callback_query.answer("Функция истории временно недоступна", show_alert=True)


def get_result_details_keyboard(result_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для деталей результата"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📁 Экспорт CSV",
        callback_data=f"export_csv_{result_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="🔍 Проверить вручную",
        callback_data=f"manual_check_{result_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_recent"
    ))
    
    builder.adjust(1)
    return builder.as_markup()
