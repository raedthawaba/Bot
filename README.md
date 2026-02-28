# TeleDroid AI Agent

بوت تليجرام ذكاء اصطناعي للتحكم وتنفيذ مهام على الجوال

## نظرة عامة على المشروع

TeleDroid هو نظام متكامل يتيح لك التحكم في هاتفك Android عبر بوت Telegram باستخدام أوامر نصية أو ذكية. يجمع المشروع بين بوت Telegram، خادم backend بـ Python، وتطبيق Android Agent.

## المميزات الرئيسية

- **إدارة الملفات**: عرض، إنشاء، حذف، رفع، وتنزيل الملفات
- **معلومات الجهاز**: حالة البطارية، التخزين، الشبكة، الذاكرة
- **الذكاء الاصطناعي**: تحليل الأوامر الطبيعية وتحويلها لمهام تنفيذية
- **المهام المجدولة**: جدولة مهام للتنفيذ التلقائي
- **الأمان**: نظام قائمة بيضاء، تشفير، وتسجيل العمليات

## هيكل المشروع

```
TeleDroid-AI-Agent/
├── backend_server/          # خادم Python
│   ├── main.py             # نقطة الدخول للـ API
│   ├── bot_handler.py      # معالج بوت Telegram
│   ├── ai_engine.py        # محرك الذكاء الاصطناعي
│   ├── security.py         # وحدة الأمان
│   ├── models.py           # نماذج قاعدة البيانات
│   ├── config.py           # الإعدادات
│   └── requirements.txt    # المتطلبات
│
└── android_agent/           # تطبيق Android
    ├── app/
    │   └── src/main/
    │       ├── java/com/teledroid/agent/
    │       │   ├── TeleDroidApp.kt
    │       │   ├── ui/MainActivity.kt
    │       │   ├── data/
    │       │   │   ├── model/Models.kt
    │       │   │   ├── remote/ApiService.kt
    │       │   │   ├── local/AppDatabase.kt
    │       │   │   └── repository/Repositories.kt
    │       │   ├── executor/CommandExecutor.kt
    │       │   ├── service/AgentService.kt
    │       │   └── receiver/Receivers.kt
    │       └── res/
    │           └── layout/activity_main.xml
    └── build.gradle
```

## متطلبات التشغيل

### الخادم الخلفي

- Python 3.10+
- Redis (اختياري)
- Telegram Bot Token

### تطبيق Android

- Android Studio
- Kotlin
- SDK 24+

## طريقة التشغيل

### 1. إعداد الخادم

```bash
cd backend_server

# إنشاء البيئة الافتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate     # Windows

# تثبيت المتطلبات
pip install -r requirements.txt

# نسخ ملف الإعدادات
cp .env.example .env

# تعديل ملف .env
# - TELEGRAM_BOT_TOKEN
# - OPENAI_API_KEY (اختياري)
# - SECRET_KEY

# تشغيل الخادم
python main.py
```

### 2. إعداد بوت Telegram

1. افتح Telegram وابحث عن @BotFather
2. أنشئ بوت جديداً باستخدام /newbot
3. احصل على الـ Token
4. أضف Token في ملف .env

### 3. إعداد تطبيق Android

1. افتح المشروع في Android Studio
2. قم ببناء المشروع
3. ثبت التطبيق على هاتفك
4. أدخل معرف Telegram الخاص بك
5. اضغط "ربط الجهاز" ثم "بدء"

## الأوامر المتاحة

| الأمر | الوصف |
|-------|-------|
| /start | بدء استخدام البوت |
| /help | عرض المساعدة |
| /status | حالة الجهاز |
| /battery | معلومات البطارية |
| /storage | معلومات التخزين |
| /network | معلومات الشبكة |
| /files | إدارة الملفات |
| /tasks | المهام المجدولة |
| /link | ربط جهاز جديد |
| /unlink | إلغاء ربط الجهاز |

## أوامر الذكاء الاصطناعي

البوت يدعم الأوامر الطبيعية مثل:

- "أعرض حالة البطارية"
- "أنشئ مجلد جديد اسمه Backup"
- "احذف ملفات الكاش"
- "أعرض الملفات في مجلد التحميلات"

## واجهة برمجة التطبيقات (API)

### نقاط النهاية الرئيسية

- `POST /api/v1/devices/link` - ربط جهاز
- `POST /api/v1/devices/heartbeat` - إشارة حياة
- `GET /api/v1/commands/pending` - الأوامر المعلقة
- `POST /api/v1/commands/result` - نتيجة الأمر
- `POST /api/v1/ai/analyze` - تحليل بالذكاء الاصطناعي
- `POST /api/v1/files/upload` - رفع ملف
- `GET /api/v1/scheduled-tasks` - المهام المجدولة

## الأمان

- **قائمة بيضاء**: يتحقق من معرف Telegram للمستخدم
- **تشفير**: تشفير البيانات بين التطبيق والخادم
- **تسجيل**: جميع العمليات مسجلة في السجل
- **صلاحيات**: نظام Role-based access

## التطوير المستقبلي

- دعم الأوامر الصوتية
- دعم تحليل الصور
- لوحة تحكم ويب
- دعم أجهزة متعددة
- تكامل مع خدمات سحابية

## الترخيص

MIT License

## المساهمة

المراجعات والمساهمات مرحب بها!
