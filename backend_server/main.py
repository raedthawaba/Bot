"""
النقطة الرئيسية للخادم
يتضمن: API endpoints، ربط البوت، وإعداد السيرفر
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from config import settings, AVAILABLE_COMMANDS
from models import (
    Base, engine, get_db, init_db,
    User, Device, Command, ScheduledTask, OperationLog, DeviceStats
)
from security import (
    AuthManager, verify_whitelist, generate_device_token,
    create_access_token, decode_token
)
from ai_engine import ai_engine


# إنشاء تطبيق FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    # بدء التشغيل
    print("🚀 جاري بدء الخادم...")

    # إنشاء قاعدة البيانات
    init_db()

    # إنشاء مجلد الرفع
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    yield

    # إيقاف التشغيل
    print("🛑 جاري إيقاف الخادم...")


app = FastAPI(
    title="TeleDroid AI Agent API",
    description="API للتحكم في هاتف Android عبر Telegram",
    version="1.0.0",
    lifespan=lifespan
)

# إضافة CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# نماذج البيانات (Pydantic)
class UserResponse(BaseModel):
    """نموذج استجابة المستخدم"""
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    """نموذج استجابة الجهاز"""
    id: int
    device_id: str
    device_name: Optional[str] = None
    device_model: Optional[str] = None
    is_online: bool
    last_seen: datetime

    class Config:
        from_attributes = True


class CommandRequest(BaseModel):
    """نموذج طلب الأمر"""
    command_type: str
    action: str
    parameters: Optional[dict] = None


class CommandResponse(BaseModel):
    """نموذج استجابة الأمر"""
    id: int
    command_type: str
    action: str
    status: str
    result: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceLinkRequest(BaseModel):
    """نموذج طلب ربط جهاز"""
    device_id: str
    device_name: Optional[str] = None
    device_model: Optional[str] = None
    android_version: Optional[str] = None
    fcm_token: Optional[str] = None


class DeviceLinkResponse(BaseModel):
    """نموذج استجابة ربط جهاز"""
    success: bool
    message: str
    device_token: Optional[str] = None


class AICommandRequest(BaseModel):
    """نموذج طلب الأمر الذكي"""
    message: str
    context: Optional[dict] = None


# ==================== نقاط النهاية الرئيسية ====================

@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "message": "TeleDroid AI Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """فحص صحة الخادم"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== نقاط نهاية المستخدمين ====================

@app.post("/api/v1/users/register", response_model=UserResponse)
async def register_user(
    telegram_id: int = Form(...),
    username: Optional[str] = Form(None),
    first_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """تسجيل مستخدم جديد"""
    # التحقق من القائمة البيضاء
    if not verify_whitelist(telegram_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك بالوصول"
        )

    auth_manager = AuthManager(db)
    user = auth_manager.get_or_create_user(telegram_id, username, first_name)

    return user


@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """الحصول على معلومات المستخدم الحالي"""
    auth_manager = AuthManager(db)
    user = auth_manager.get_user_by_telegram_id(telegram_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )

    return user


# ==================== نقاط نهاية الأجهزة ====================

@app.post("/api/v1/devices/link", response_model=DeviceLinkResponse)
async def link_device(
    request: DeviceLinkRequest,
    telegram_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """ربط جهاز جديد"""
    # التحقق من المستخدم
    auth_manager = AuthManager(db)
    user = auth_manager.get_user_by_telegram_id(telegram_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )

    # التحقق من وجود الجهاز
    device = db.query(Device).filter(Device.device_id == request.device_id).first()

    if device:
        # تحديث معلومات الجهاز
        device.device_name = request.device_name
        device.device_model = request.device_model
        device.android_version = request.android_version
        device.fcm_token = request.fcm_token
        device.is_online = True
        device.last_seen = datetime.utcnow()
    else:
        # إنشاء جهاز جديد
        device = Device(
            user_id=user.id,
            device_id=request.device_id,
            device_name=request.device_name,
            device_model=request.device_model,
            android_version=request.android_version,
            fcm_token=request.fcm_token,
            is_online=True
        )
        db.add(device)

    db.commit()

    # إنشاء رمز المصادقة
    device_token = auth_manager.create_auth_token(user.id, request.device_id)

    return DeviceLinkResponse(
        success=True,
        message="تم ربط الجهاز بنجاح",
        device_token=device_token
    )


@app.post("/api/v1/devices/unlink")
async def unlink_device(
    device_id: str,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """إلغاء ربط جهاز"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    device = db.query(Device).filter(
        Device.device_id == device_id,
        Device.user_id == user.id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="الجهاز غير موجود")

    db.delete(device)
    db.commit()

    return {"success": True, "message": "تم إلغاء ربط الجهاز"}


@app.get("/api/v1/devices", response_model=List[DeviceResponse])
async def get_user_devices(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """الحصول على أجهزة المستخدم"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return []

    devices = db.query(Device).filter(Device.user_id == user.id).all()
    return devices


@app.post("/api/v1/devices/heartbeat")
async def device_heartbeat(
    device_id: str,
    db: Session = Depends(get_db)
):
    """إشارة حياة من الجهاز"""
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="الجهاز غير موجود")

    device.is_online = True
    device.last_seen = datetime.utcnow()
    db.commit()

    return {"success": True}


# ==================== نقاط نهاية الأوامر ====================

@app.post("/api/v1/commands/execute")
async def execute_command(
    request: CommandRequest,
    telegram_id: int,
    device_id: str,
    db: Session = Depends(get_db)
):
    """تنفيذ أمر على الجهاز"""
    # التحقق من المستخدم والجهاز
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    device = db.query(Device).filter(
        Device.device_id == device_id,
        Device.user_id == user.id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="الجهاز غير موجود")

    # إنشاء الأمر
    command = Command(
        user_id=user.id,
        device_id=device.id,
        command_type=request.command_type,
        action=request.action,
        parameters=request.parameters,
        status="pending"
    )
    db.add(command)
    db.commit()
    db.refresh(command)

    # إرسال الأمر للجهاز (سيتم تنفيذه بواسطة التطبيق)
    # في الإنتاج، يمكن استخدام WebSocket أو Push Notification

    return {
        "success": True,
        "command_id": command.id,
        "message": "تم إرسال الأمر للجهاز"
    }


@app.get("/api/v1/commands/pending")
async def get_pending_commands(
    device_id: str,
    db: Session = Depends(get_db)
):
    """الحصول على الأوامر المعلقة للجهاز"""
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="الجهاز غير موجود")

    commands = db.query(Command).filter(
        Command.device_id == device.id,
        Command.status == "pending"
    ).all()

    return [
        {
            "id": cmd.id,
            "command_type": cmd.command_type,
            "action": cmd.action,
            "parameters": cmd.parameters
        }
        for cmd in commands
    ]


@app.post("/api/v1/commands/result")
async def submit_command_result(
    command_id: int,
    status: str,
    result: Optional[dict] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """تقديم نتيجة الأمر"""
    command = db.query(Command).filter(Command.id == command_id).first()

    if not command:
        raise HTTPException(status_code=404, detail="الأمر غير موجود")

    command.status = status
    command.result = result
    command.error_message = error_message

    if status in ["completed", "failed"]:
        command.completed_at = datetime.utcnow()

    db.commit()

    return {"success": True}


# ==================== نقاط نهاية الذكاء الاصطناعي ====================

@app.post("/api/v1/ai/analyze")
async def analyze_with_ai(request: AICommandRequest):
    """تحليل الأمر باستخدام AI"""
    result = await ai_engine.analyze_command(request.message, request.context)
    return result


@app.post("/api/v1/ai/chat")
async def chat_with_ai(
    message: str,
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """المحادثة مع AI"""
    # الحصول على سياق المستخدم
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    # تحليل الأمر
    result = ai_engine.analyze_command(message)

    if result.get("success"):
        # إنشاء رد مناسب
        response = ai_engine.generate_response(result, message)
        return {
            "success": True,
            "response": response,
            "action": result
        }
    else:
        return {
            "success": False,
            "response": result.get("error", "تعذر فهم الأمر"),
            "action": None
        }


# ==================== نقاط نهاية الملفات ====================

@app.post("/api/v1/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    device_id: str = Form(...),
    path: str = Form("/"),
    db: Session = Depends(get_db)
):
    """رفع ملف إلى الجهاز"""
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="الجهاز غير موجود")

    # حفظ الملف
    file_path = os.path.join(settings.UPLOAD_DIR, f"{device_id}_{file.filename}")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "success": True,
        "file_path": file_path,
        "file_size": len(content)
    }


# ==================== نقاط نهاية المهام المجدولة ====================

@app.get("/api/v1/scheduled-tasks")
async def get_scheduled_tasks(
    device_id: str,
    db: Session = Depends(get_db)
):
    """الحصول على المهام المجدولة"""
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        return []

    tasks = db.query(ScheduledTask).filter(
        ScheduledTask.device_id == device.id
    ).all()

    return [
        {
            "id": task.id,
            "name": task.name,
            "command_type": task.command_type,
            "action": task.action,
            "schedule_type": task.schedule_type,
            "is_active": task.is_active,
            "next_run": task.next_run
        }
        for task in tasks
    ]


@app.post("/api/v1/scheduled-tasks")
async def create_scheduled_task(
    device_id: str,
    name: str = Form(...),
    command_type: str = Form(...),
    action: str = Form(...),
    schedule_type: str = Form(...),
    schedule_value: str = Form(...),
    parameters: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """إنشاء مهمة مجدولة"""
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="الجهاز غير موجود")

    task = ScheduledTask(
        device_id=device.id,
        name=name,
        command_type=command_type,
        action=action,
        schedule_type=schedule_type,
        schedule_value=schedule_value,
        parameters=json.loads(parameters) if parameters else None
    )

    db.add(task)
    db.commit()

    return {"success": True, "task_id": task.id}


# ==================== نقاط نهاية السجلات ====================

@app.get("/api/v1/logs")
async def get_operation_logs(
    telegram_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """الحصول على سجلات العمليات"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        return []

    logs = db.query(OperationLog).filter(
        OperationLog.user_id == user.id
    ).order_by(OperationLog.created_at.desc()).limit(limit).all()

    return [
        {
            "id": log.id,
            "operation_type": log.operation_type,
            "description": log.description,
            "created_at": log.created_at
        }
        for log in logs
    ]


# ==================== نقطة نهاية الإحصائيات ====================

@app.get("/api/v1/stats/{device_id}")
async def get_device_stats(
    device_id: str,
    db: Session = Depends(get_db)
):
    """الحصول على إحصائيات الجهاز"""
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="الجهاز غير موجود")

    stats = db.query(DeviceStats).filter(
        DeviceStats.device_id == device_id
    ).order_by(DeviceStats.created_at.desc()).first()

    if not stats:
        return {
            "message": "لا توجد إحصائيات متاحة"
        }

    return {
        "battery": {
            "level": stats.battery_level,
            "status": stats.battery_status
        },
        "storage": {
            "total": stats.storage_total,
            "used": stats.storage_used
        },
        "network": {
            "type": stats.network_type,
            "speed": stats.network_speed
        },
        "memory": {
            "total": stats.memory_total,
            "used": stats.memory_used
        }
    }


# استيراد json
import json

# تشغيل السيرفر
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
