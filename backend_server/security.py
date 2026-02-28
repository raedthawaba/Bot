"""
وحدة الأمان والمصادقة
تتضمن: التحقق من المستخدمين، تشفير البيانات، وإدارة الجلسات
"""

import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings
from models import User, AuthToken, Device

# خوارزمية التشفير
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """تشفير كلمة المرور"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """إنشاء رمز وصول JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """فك تشفير رمز JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_whitelist(telegram_id: int) -> bool:
    """التحقق من وجود المستخدم في القائمة البيضاء"""
    if not settings.ALLOWED_USERS:
        return True  # إذا كانت القائمة فارغة، السماح للجميع
    return telegram_id in settings.ALLOWED_USERS


def check_user_permission(telegram_id: int, permission: str) -> bool:
    """التحقق من صلاحيات المستخدم"""
    # يمكن توسيع هذا للتحقق من صلاحيات محددة
    return verify_whitelist(telegram_id)


def generate_otp() -> str:
    """إنشاء رمز OTP عشوائي"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def generate_device_token() -> str:
    """إنشاء رمز جهاز عشوائي"""
    return secrets.token_urlsafe(32)


def encrypt_data(data: str) -> str:
    """تشفير البيانات باستخدام AES"""
    from cryptography.fernet import Fernet
    # في الإنتاج، يجب تخزين المفتاح بشكل آمن
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """فك تشفير البيانات"""
    from cryptography.fernet import Fernet
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()


class AuthManager:
    """مدير المصادقة"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, telegram_id: int, username: str = None,
                    first_name: str = None, last_name: str = None) -> User:
        """إنشاء مستخدم جديد"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """الحصول على المستخدم بواسطة معرف Telegram"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def get_or_create_user(self, telegram_id: int, username: str = None,
                           first_name: str = None, last_name: str = None) -> User:
        """الحصول على المستخدم أو إنشاؤه"""
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            user = self.create_user(telegram_id, username, first_name, last_name)
        return user

    def generate_otp_for_device(self, user_id: int, device_id: str) -> str:
        """إنشاء رمز OTP لربط الجهاز"""
        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        # حذف الرموز القديمة
        self.db.query(AuthToken).filter(
            AuthToken.user_id == user_id,
            AuthToken.device_id == device_id,
            AuthToken.is_used == False
        ).delete()

        # إنشاء رمز جديد
        auth_token = AuthToken(
            user_id=user_id,
            device_id=device_id,
            otp_code=otp,
            otp_expires_at=expires_at
        )
        self.db.add(auth_token)
        self.db.commit()

        return otp

    def verify_otp(self, user_id: int, device_id: str, otp: str) -> bool:
        """التحقق من رمز OTP"""
        auth_token = self.db.query(AuthToken).filter(
            AuthToken.user_id == user_id,
            AuthToken.device_id == device_id,
            AuthToken.otp_code == otp,
            AuthToken.is_used == False
        ).first()

        if not auth_token:
            return False

        if auth_token.otp_expires_at < datetime.utcnow():
            return False

        # تعيين الرمز كمستخدم
        auth_token.is_used = True
        self.db.commit()

        return True

    def create_auth_token(self, user_id: int, device_id: str) -> str:
        """إنشاء رمز مصادقة للجهاز"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=30)

        auth_token = AuthToken(
            user_id=user_id,
            device_id=device_id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(auth_token)
        self.db.commit()

        return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(lambda: None)
) -> User:
    """الحصول على المستخدم الحالي من رمز JWT"""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز المصالحة غير صالح",
            headers={"WWW-Authenticate": "Bearer"},
        )

    telegram_id: int = payload.get("sub")
    if telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="معرف المستخدم غير صالح",
        )

    # هنا يجب جلب المستخدم من قاعدة البيانات
    # هذا مثال بسيط، في الإنتاج يجب تحسينه
    return User(telegram_id=telegram_id)


def log_operation(
    db: Session,
    user_id: int,
    operation_type: str,
    description: str,
    device_id: int = None,
    command_id: int = None,
    ip_address: str = None
):
    """تسجيل عملية في السجل"""
    from models import OperationLog

    log = OperationLog(
        user_id=user_id,
        device_id=device_id,
        command_id=command_id,
        operation_type=operation_type,
        description=description,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
