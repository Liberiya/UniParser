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
from database.operations import get_parsing_results, get_staff_records, log_export


async def history_handler(message: Message, state: FSMContext):
    """Обработчик команды /history"""
    user = message.from_user
    
    # Получаем последние результаты
    results = get_parsing_results(user.id, limit=10)
    
    if not results:
        await message.answer(
            "📋 <b>История парсинга</b>\n\n"
            "У вас пока нет результатов парсинга.\n"
            "Начните с команды /parse или используйте кнопку \"Парсить URL\"",
            reply_markup=get_history_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Формируем текст с результатами
    text = "📋 <b>История парсинга</b>\n\n"
    text += f"Найдено результатов: {len(results)}\n\n"
    
    for i, result in enumerate(results[:5], 1):
        text += f"<b>{i}. {result['url'][:50]}...</b>\n"
        text += f"Записей: {result['results_count']}\n"
        text += f"Дата: {result['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        text += f"Статус: {result['status']}\n\n"
    
    if len(results) > 5:
        text += f"... и еще {len(results) - 5} результатов\n\n"
    
    text += "Выберите действие:"
    
    await message.answer(
        text,
        reply_markup=get_history_keyboard(),
        parse_mode="HTML"
    )


async def export_csv_handler(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик экспорта в CSV"""
    user = callback_query.from_user
    
    try:
        # Получаем ID результата парсинга из callback_data
        parsing_result_id = int(callback_query.data.split('_')[-1])
        
        # Получаем записи о сотрудниках
        records = get_staff_records(parsing_result_id)
        
        if not records:
            await callback_query.answer("Нет данных для экспорта", show_alert=True)
            return
        
        # Создаем CSV файл
        csv_file = create_csv_file(records)
        
        # Отправляем файл
        await callback_query.message.answer_document(
            document=csv_file,
            caption=f"📁 <b>Экспорт CSV</b>\n\n"
                   f"Экспортировано записей: {len(records)}\n"
                   f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML"
        )
        
        # Логируем экспорт
        log_export(user.id, parsing_result_id, 'csv', len(records))
        
        await callback_query.answer("CSV файл отправлен!")
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте CSV: {e}")
        await callback_query.answer("Ошибка при создании CSV файла", show_alert=True)


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
    user = callback_query.from_user
    
    # Получаем последние результаты
    results = get_parsing_results(user.id, limit=5)
    
    if not results:
        await callback_query.answer("Нет результатов для показа", show_alert=True)
        return
    
    text = "📊 <b>Последние результаты</b>\n\n"
    
    for i, result in enumerate(results, 1):
        text += f"<b>{i}. Результат #{result['id']}</b>\n"
        text += f"URL: {result['url'][:60]}...\n"
        text += f"Записей: {result['results_count']}\n"
        text += f"Дата: {result['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await callback_query.message.edit_text(
        text,
        reply_markup=get_recent_results_keyboard(results),
        parse_mode="HTML"
    )


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
    try:
        result_id = int(callback_query.data.split('_')[-1])
        
        # Получаем записи
        records = get_staff_records(result_id)
        
        if not records:
            await callback_query.answer("Нет записей для показа", show_alert=True)
            return
        
        # Группируем по confidence
        high_conf = [r for r in records if r['confidence'] >= 0.7]
        medium_conf = [r for r in records if 0.5 <= r['confidence'] < 0.7]
        low_conf = [r for r in records if r['confidence'] < 0.5]
        
        text = f"📋 <b>Результат #{result_id}</b>\n\n"
        text += f"Всего записей: {len(records)}\n"
        text += f"• Высокая достоверность: {len(high_conf)}\n"
        text += f"• Средняя достоверность: {len(medium_conf)}\n"
        text += f"• Низкая достоверность: {len(low_conf)}\n\n"
        
        # Показываем первые несколько записей
        for i, record in enumerate(records[:5], 1):
            text += f"<b>{i}. {record['fio']}</b>\n"
            text += f"Должность: {record['position'] or 'Не указана'}\n"
            text += f"Email: {record['email'] or 'Не указан'}\n"
            text += f"Достоверность: {record['confidence']:.2f}\n\n"
        
        if len(records) > 5:
            text += f"... и еще {len(records) - 5} записей\n\n"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_result_details_keyboard(result_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при показе деталей результата: {e}")
        await callback_query.answer("Ошибка при загрузке деталей", show_alert=True)


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
