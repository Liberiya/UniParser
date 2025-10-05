"""
Состояния FSM для Telegram бота
"""

from aiogram.fsm.state import State, StatesGroup


class ParseStates(StatesGroup):
    """Состояния для парсинга"""
    waiting_for_url = State()
    parsing_in_progress = State()
    waiting_for_confirmation = State()


class SettingsStates(StatesGroup):
    """Состояния для настроек"""
    waiting_for_rate_limit = State()
    waiting_for_depth = State()
    waiting_for_confidence = State()


class ValidationStates(StatesGroup):
    """Состояния для валидации"""
    waiting_for_validation = State()
    waiting_for_manual_input = State()
