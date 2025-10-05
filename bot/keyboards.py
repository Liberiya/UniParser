"""
Клавиатуры для Telegram бота
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура бота"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="🔍 Парсить URL"))
    builder.add(KeyboardButton(text="📋 История"))
    builder.add(KeyboardButton(text="⚙️ Настройки"))
    builder.add(KeyboardButton(text="❓ Помощь"))
    
    builder.adjust(2)
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие..."
    )


def get_parse_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для парсинга"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🚀 Начать парсинг",
        callback_data="start_parsing"
    ))
    builder.add(InlineKeyboardButton(
        text="⚙️ Настройки парсинга",
        callback_data="parse_settings"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_history_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для истории"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📊 Последние результаты",
        callback_data="show_recent"
    ))
    builder.add(InlineKeyboardButton(
        text="📁 Экспорт CSV",
        callback_data="export_csv"
    ))
    builder.add(InlineKeyboardButton(
        text="🗑 Очистить историю",
        callback_data="clear_history"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="⏱ Rate Limit",
        callback_data="settings_rate_limit"
    ))
    builder.add(InlineKeyboardButton(
        text="🔍 Глубина парсинга",
        callback_data="settings_depth"
    ))
    builder.add(InlineKeyboardButton(
        text="🌐 JS Рендеринг",
        callback_data="settings_js_render"
    ))
    builder.add(InlineKeyboardButton(
        text="🎯 Confidence Threshold",
        callback_data="settings_confidence"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_staff_item_keyboard(staff_id: int, source_url: str) -> InlineKeyboardMarkup:
    """Клавиатура для элемента списка сотрудников"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🔗 Источник",
        url=source_url
    ))
    builder.add(InlineKeyboardButton(
        text="✅ Корректно",
        callback_data=f"validate_correct_{staff_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Неверно",
        callback_data=f"validate_incorrect_{staff_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="📝 Добавить в CSV",
        callback_data=f"add_to_csv_{staff_id}"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_pagination_keyboard(page: int, total_pages: int, prefix: str = "page") -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    builder = InlineKeyboardBuilder()
    
    if page > 1:
        builder.add(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"{prefix}_{page-1}"
        ))
    
    builder.add(InlineKeyboardButton(
        text=f"{page}/{total_pages}",
        callback_data="current_page"
    ))
    
    if page < total_pages:
        builder.add(InlineKeyboardButton(
            text="➡️",
            callback_data=f"{prefix}_{page+1}"
        ))
    
    return builder.as_markup()


def get_confirmation_keyboard(action: str, item_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    
    callback_data = f"confirm_{action}"
    if item_id:
        callback_data += f"_{item_id}"
    
    builder.add(InlineKeyboardButton(
        text="✅ Да",
        callback_data=callback_data
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Нет",
        callback_data="cancel_action"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_results_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для результатов парсинга"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📁 Экспорт CSV",
        callback_data="export_csv"
    ))
    builder.add(InlineKeyboardButton(
        text="🔍 Проверить вручную",
        callback_data="manual_check"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup()
