"""
Обработчик команды /start
"""

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.keyboards import get_main_keyboard


async def start_handler(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user = message.from_user
    logger.info(f"Пользователь {user.full_name} ({user.id}) запустил бота")
    
    # Очищаем состояние
    await state.clear()
    
    welcome_text = f"""
🎓 <b>Добро пожаловать в University Staff Parser Bot!</b>

Привет, {user.first_name}! 👋

Этот бот поможет вам извлечь информацию о преподавателях и сотрудниках с сайтов российских вузов.

<b>Возможности бота:</b>
• Парсинг любых сайтов (включая JS-страницы)
• Извлечение ФИО, должностей, email адресов
• Оценка достоверности данных
• Экспорт результатов в CSV
• История парсинга

<b>Как использовать:</b>
1. Нажмите "Парсить URL" и отправьте ссылку на страницу вуза
2. Дождитесь результатов парсинга
3. Просмотрите найденные данные
4. Экспортируйте результаты в CSV при необходимости

Выберите действие из меню ниже:
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
