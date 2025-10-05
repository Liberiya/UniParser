"""
Обработчики команд Telegram бота
"""

from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.handlers.start import start_handler
from bot.handlers.parse import parse_handler, parse_url_handler
from bot.handlers.history import (
    history_handler, export_csv_handler, show_recent_results, 
    show_result_details
)
from bot.handlers.settings import (
    settings_handler, update_settings_handler,
    handle_rate_limit_input, handle_depth_input, handle_confidence_input
)
from bot.handlers.help import help_handler
from bot.handlers.validate import (
    validate_handler, manual_validation_handler,
    validate_correct_callback, validate_incorrect_callback,
    manual_check_handler
)
from bot.states import ParseStates, SettingsStates, ValidationStates


def register_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков"""
    
    # Команды
    dp.message.register(start_handler, CommandStart())
    dp.message.register(parse_handler, Command("parse"))
    dp.message.register(history_handler, Command("history"))
    dp.message.register(settings_handler, Command("settings"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(validate_handler, Command("validate"))
    
    # Обработчики состояний
    dp.message.register(parse_url_handler, ParseStates.waiting_for_url)
    dp.message.register(handle_rate_limit_input, SettingsStates.waiting_for_rate_limit)
    dp.message.register(handle_depth_input, SettingsStates.waiting_for_depth)
    dp.message.register(handle_confidence_input, SettingsStates.waiting_for_confidence)
    dp.message.register(manual_validation_handler, ValidationStates.waiting_for_manual_input)
    
    # Callback обработчики
    dp.callback_query.register(export_csv_handler, lambda c: c.data.startswith("export_csv"))
    dp.callback_query.register(update_settings_handler, lambda c: c.data.startswith("settings_"))
    dp.callback_query.register(show_recent_results, lambda c: c.data == "show_recent")
    dp.callback_query.register(show_result_details, lambda c: c.data.startswith("show_result_"))
    dp.callback_query.register(validate_correct_callback, lambda c: c.data.startswith("validate_correct_"))
    dp.callback_query.register(validate_incorrect_callback, lambda c: c.data.startswith("validate_incorrect_"))
    dp.callback_query.register(manual_check_handler, lambda c: c.data.startswith("manual_check_"))
    
    logger.info("All handlers registered")
