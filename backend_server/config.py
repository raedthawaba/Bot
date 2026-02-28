"""
ملف الإعدادات الرئيسية للمشروع
يتضمن إعدادات الخادم، قاعدة البيانات، الأمان، والتليجرام
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """إعدادات المشروع"""

    # إعدادات البيئة
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # إعدادات الخادم
    HOST: str = Field(default="127.0.0.1", env="HOST")
    PORT: int = Field(default=8000, env="PORT")

    # إعدادات قاعدة البيانات
    DATABASE_URL: str = Field(
        default="sqlite:///./teledroid.db",
        env="DATABASE_URL"
    )

    # إعدادات Redis
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")

    # إعدادات Telegram Bot
    TELEGRAM_BOT_TOKEN: str = Field(
        default="",
        env="TELEGRAM_BOT_TOKEN"
    )
    TELEGRAM_API_ID: int = Field(default=0, env="TELEGRAM_API_ID")
    TELEGRAM_API_HASH: str = Field(default="", env="TELEGRAM_API_HASH")

    # إعدادات OpenAI للذكاء الاصطناعي
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")

    # إعدادات الأمان
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 7,  # أسبوع
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # قائمة المستخدمين المسموح لهم (Whitelist)
    ALLOWED_USERS: List[int] = Field(
        default=[],
        env="ALLOWED_USERS"
    )

    # إعدادات الملفات
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")

    # إعدادات Webhook
    WEBHOOK_URL: str = Field(default="", env="WEBHOOK_URL")
    USE_WEBHOOK: bool = Field(default=False, env="USE_WEBHOOK")

    class Config:
        env_file = ".env"
        case_sensitive = True


# إنشاء كائن الإعدادات
settings = Settings()


# دالة لتحميل المتغيرات من .env
def load_env_variables():
    """تحميل المتغيرات من ملف .env"""
    from dotenv import load_dotenv
    load_dotenv()


# قائمة الأوامر المتاحة
AVAILABLE_COMMANDS = {
    "start": "بدء استخدام البوت",
    "help": "عرض المساعدة",
    "status": "عرض حالة الجهاز",
    "battery": "معلومات البطارية",
    "storage": "معلومات التخزين",
    "network": "معلومات الشبكة",
    "files": "إدارة الملفات",
    "tasks": "المهام المجدولة",
    "settings": "الإعدادات",
    "unlink": "إلغاء ربط الجهاز",
}

# قائمة الأذونات
PERMISSIONS = {
    "file_management": "إدارة الملفات",
    "device_info": "معلومات الجهاز",
    "task_scheduling": "جدولة المهام",
    "command_execution": "تنفيذ الأوامر",
    "analytics": "التحليل والذكاء الاصطناعي",
}
