"""
نماذج قاعدة البيانات
يحتوي على جميع نماذج البيانات المستخدمة في المشروع
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from config import settings

# إنشاء قاعدة البيانات
Base = declarative_base()


class User(Base):
    """نموذج المستخدم"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # العلاقات
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("OperationLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.telegram_id}>"


class Device(Base):
    """نموذج الجهاز المرتبط"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_name = Column(String, nullable=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    device_model = Column(String, nullable=True)
    android_version = Column(String, nullable=True)
    fcm_token = Column(String, nullable=True)  # Firebase Cloud Messaging Token
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # العلاقات
    user = relationship("User", back_populates="devices")
    commands = relationship("Command", back_populates="device", cascade="all, delete-orphan")
    scheduled_tasks = relationship("ScheduledTask", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Device {self.device_id}>"


class Command(Base):
    """نموذج الأمر"""
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    command_type = Column(String, nullable=False)  # file, system, task, ai
    action = Column(String, nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # العلاقات
    user = relationship("User", back_populates="commands")
    device = relationship("Device", back_populates="commands")

    def __repr__(self):
        return f"<Command {self.id} - {self.action}>"


class ScheduledTask(Base):
    """نموذج المهمة المجدولة"""
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    name = Column(String, nullable=False)
    command_type = Column(String, nullable=False)
    action = Column(String, nullable=False)
    parameters = Column(JSON, nullable=True)
    schedule_type = Column(String, nullable=False)  # once, hourly, daily, weekly
    schedule_value = Column(String, nullable=True)  # cron expression or interval
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # العلاقات
    device = relationship("Device", back_populates="scheduled_tasks")

    def __repr__(self):
        return f"<ScheduledTask {self.id} - {self.name}>"


class OperationLog(Base):
    """نموذج سجل العمليات"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    command_id = Column(Integer, ForeignKey("commands.id"), nullable=True)
    operation_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # العلاقات
    user = relationship("User", back_populates="logs")

    def __repr__(self):
        return f"<OperationLog {self.id} - {self.operation_type}>"


class AuthToken(Base):
    """نموذج رمز المصادقة"""
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(String, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<AuthToken {self.id}>"


class DeviceStats(Base):
    """نموذج إحصائيات الجهاز"""
    __tablename__ = "device_stats"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=False)
    battery_level = Column(Integer, nullable=True)
    battery_status = Column(String, nullable=True)
    storage_total = Column(Float, nullable=True)
    storage_used = Column(Float, nullable=True)
    network_type = Column(String, nullable=True)
    network_speed = Column(Float, nullable=True)
    memory_used = Column(Float, nullable=True)
    memory_total = Column(Float, nullable=True)
    cpu_usage = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<DeviceStats {self.id}>"


# إنشاء محرك قاعدة البيانات
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

# إنشاء Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """الحصول على جلسة قاعدة البيانات"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """إنشاء جميع الجداول"""
    Base.metadata.create_all(bind=engine)
