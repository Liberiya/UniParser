"""
Модели базы данных
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    parsing_results = relationship("ParsingResult", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)


class ParsingResult(Base):
    """Модель результата парсинга"""
    __tablename__ = 'parsing_results'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    url = Column(Text, nullable=False)
    results = Column(JSON, nullable=False)  # Список найденных записей
    settings = Column(JSON, nullable=True)  # Настройки парсинга
    status = Column(String(50), default='completed')  # completed, failed, processing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="parsing_results")


class StaffRecord(Base):
    """Модель записи о сотруднике"""
    __tablename__ = 'staff_records'
    
    id = Column(Integer, primary_key=True)
    parsing_result_id = Column(Integer, nullable=False, index=True)
    fio = Column(String(255), nullable=False)
    position = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    department = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    raw_html_snippet = Column(Text, nullable=True)
    is_validated = Column(Boolean, default=False)  # Проверено ли вручную
    is_correct = Column(Boolean, nullable=True)  # Корректность (True/False/None)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserSettings(Base):
    """Модель настроек пользователя"""
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Настройки парсинга
    rate_limit_delay = Column(Float, default=2.0)
    max_depth = Column(Integer, default=2)
    js_render_timeout = Column(Integer, default=30)
    parsing_timeout = Column(Integer, default=120)
    confidence_threshold = Column(Float, default=0.6)
    js_render_enabled = Column(Boolean, default=True)
    
    # Дополнительные настройки
    auto_export_csv = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="settings")


class ValidationLog(Base):
    """Модель лога валидации"""
    __tablename__ = 'validation_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    staff_record_id = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False)  # correct, incorrect, manual_input
    data = Column(JSON, nullable=True)  # Данные для валидации
    created_at = Column(DateTime, default=datetime.utcnow)


class ExportLog(Base):
    """Модель лога экспорта"""
    __tablename__ = 'export_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    parsing_result_id = Column(Integer, nullable=True)
    export_type = Column(String(50), nullable=False)  # csv, json, excel
    records_count = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
