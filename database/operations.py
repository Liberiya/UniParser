"""
Операции с базой данных
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, select, update, delete
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from loguru import logger

from database.models import Base, User, ParsingResult, StaffRecord, UserSettings, ValidationLog, ExportLog


class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных"""
        database_url = os.getenv("DATABASE_URL", "sqlite:///data/parser_bot.db")
        
        # Создаем директорию для SQLite если нужно
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(
            database_url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Создаем таблицы
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized: {database_url}")
    
    def get_session(self) -> Session:
        """Получение сессии базы данных"""
        return self.SessionLocal()


# Глобальный экземпляр менеджера
db_manager = DatabaseManager()


async def init_database():
    """Инициализация базы данных (асинхронная обертка)"""
    # База данных уже инициализирована в конструкторе
    logger.info("Database ready to work")


def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
    """Получение или создание пользователя"""
    session = db_manager.get_session()
    try:
        # Ищем существующего пользователя
        user = session.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        
        if user:
            # Обновляем данные если изменились
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            
            if updated:
                user.updated_at = datetime.utcnow()
                session.commit()
            
            return user
        else:
            # Создаем нового пользователя
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Создаем настройки по умолчанию
            settings = UserSettings(user_id=user.id)
            session.add(settings)
            session.commit()
            
            logger.info(f"Создан новый пользователь: {telegram_id}")
            return user
            
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при создании/получении пользователя: {e}")
        raise
    finally:
        session.close()


def get_user_settings(user_id: int) -> Dict[str, Any]:
    """Получение настроек пользователя"""
    session = db_manager.get_session()
    try:
        settings = session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        ).scalar_one_or_none()
        
        if settings:
            return {
                'rate_limit_delay': settings.rate_limit_delay,
                'max_depth': settings.max_depth,
                'js_render_timeout': settings.js_render_timeout,
                'parsing_timeout': settings.parsing_timeout,
                'confidence_threshold': settings.confidence_threshold,
                'js_render_enabled': settings.js_render_enabled,
                'auto_export_csv': settings.auto_export_csv,
                'notifications_enabled': settings.notifications_enabled
            }
        else:
            # Возвращаем настройки по умолчанию
            return {
                'rate_limit_delay': 2.0,
                'max_depth': 2,
                'js_render_timeout': 30,
                'parsing_timeout': 120,
                'confidence_threshold': 0.6,
                'js_render_enabled': True,
                'auto_export_csv': False,
                'notifications_enabled': True
            }
            
    except Exception as e:
        logger.error(f"Ошибка при получении настроек пользователя: {e}")
        return {}
    finally:
        session.close()


def update_user_settings(user_id: int, settings: Dict[str, Any]) -> bool:
    """Обновление настроек пользователя"""
    session = db_manager.get_session()
    try:
        user_settings = session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        ).scalar_one_or_none()
        
        if user_settings:
            # Обновляем существующие настройки
            for key, value in settings.items():
                if hasattr(user_settings, key):
                    setattr(user_settings, key, value)
            
            user_settings.updated_at = datetime.utcnow()
            session.commit()
            return True
        else:
            # Создаем новые настройки
            new_settings = UserSettings(user_id=user_id, **settings)
            session.add(new_settings)
            session.commit()
            return True
            
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при обновлении настроек: {e}")
        return False
    finally:
        session.close()


async def save_parsing_result(user_id: int, url: str, results: List[Dict[str, Any]], settings: Dict[str, Any]) -> int:
    """Сохранение результата парсинга"""
    session = db_manager.get_session()
    try:
        # Создаем запись результата парсинга
        parsing_result = ParsingResult(
            user_id=user_id,
            url=url,
            results=results,
            settings=settings,
            status='completed'
        )
        session.add(parsing_result)
        session.commit()
        session.refresh(parsing_result)
        
        # Создаем записи о сотрудниках
        for result in results:
            staff_record = StaffRecord(
                parsing_result_id=parsing_result.id,
                fio=result.get('fio', ''),
                position=result.get('position', ''),
                email=result.get('email', ''),
                phone=result.get('phone', ''),
                department=result.get('department', ''),
                source_url=result.get('source', url),
                confidence=result.get('confidence', 0.0),
                raw_html_snippet=result.get('raw_html_snippet', '')
            )
            session.add(staff_record)
        
        session.commit()
        logger.info(f"Сохранен результат парсинга: {len(results)} записей")
        return parsing_result.id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при сохранении результата парсинга: {e}")
        raise
    finally:
        session.close()


def get_parsing_results(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Получение результатов парсинга пользователя"""
    session = db_manager.get_session()
    try:
        results = session.execute(
            select(ParsingResult)
            .where(ParsingResult.user_id == user_id)
            .order_by(ParsingResult.created_at.desc())
            .limit(limit)
        ).scalars().all()
        
        return [
            {
                'id': result.id,
                'url': result.url,
                'results_count': len(result.results) if result.results else 0,
                'created_at': result.created_at,
                'status': result.status
            }
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Ошибка при получении результатов парсинга: {e}")
        return []
    finally:
        session.close()


def get_staff_records(parsing_result_id: int) -> List[Dict[str, Any]]:
    """Получение записей о сотрудниках"""
    session = db_manager.get_session()
    try:
        records = session.execute(
            select(StaffRecord)
            .where(StaffRecord.parsing_result_id == parsing_result_id)
            .order_by(StaffRecord.confidence.desc())
        ).scalars().all()
        
        return [
            {
                'id': record.id,
                'fio': record.fio,
                'position': record.position,
                'email': record.email,
                'phone': record.phone,
                'department': record.department,
                'source_url': record.source_url,
                'confidence': record.confidence,
                'raw_html_snippet': record.raw_html_snippet,
                'is_validated': record.is_validated,
                'is_correct': record.is_correct
            }
            for record in records
        ]
        
    except Exception as e:
        logger.error(f"Ошибка при получении записей о сотрудниках: {e}")
        return []
    finally:
        session.close()


def validate_staff_record(record_id: int, is_correct: bool, user_id: int) -> bool:
    """Валидация записи о сотруднике"""
    session = db_manager.get_session()
    try:
        # Обновляем запись
        session.execute(
            update(StaffRecord)
            .where(StaffRecord.id == record_id)
            .values(
                is_validated=True,
                is_correct=is_correct,
                updated_at=datetime.utcnow()
            )
        )
        
        # Добавляем запись в лог валидации
        validation_log = ValidationLog(
            user_id=user_id,
            staff_record_id=record_id,
            action='correct' if is_correct else 'incorrect'
        )
        session.add(validation_log)
        
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при валидации записи: {e}")
        return False
    finally:
        session.close()


def log_export(user_id: int, parsing_result_id: int, export_type: str, records_count: int, file_path: str = None) -> bool:
    """Логирование экспорта"""
    session = db_manager.get_session()
    try:
        export_log = ExportLog(
            user_id=user_id,
            parsing_result_id=parsing_result_id,
            export_type=export_type,
            records_count=records_count,
            file_path=file_path
        )
        session.add(export_log)
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при логировании экспорта: {e}")
        return False
    finally:
        session.close()


def delete_user_data(user_id: int) -> bool:
    """Удаление всех данных пользователя (GDPR)"""
    session = db_manager.get_session()
    try:
        # Удаляем все связанные данные
        session.execute(delete(ValidationLog).where(ValidationLog.user_id == user_id))
        session.execute(delete(ExportLog).where(ExportLog.user_id == user_id))
        session.execute(delete(StaffRecord).where(StaffRecord.parsing_result_id.in_(
            select(ParsingResult.id).where(ParsingResult.user_id == user_id)
        )))
        session.execute(delete(ParsingResult).where(ParsingResult.user_id == user_id))
        session.execute(delete(UserSettings).where(UserSettings.user_id == user_id))
        session.execute(delete(User).where(User.id == user_id))
        
        session.commit()
        logger.info(f"Удалены все данные пользователя: {user_id}")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при удалении данных пользователя: {e}")
        return False
    finally:
        session.close()
