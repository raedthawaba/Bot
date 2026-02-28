"""
معالج بوت Telegram
يتضمن: معالجة الأوامر، إدارة الملفات، والتفاعل مع المستخدم
"""

import asyncio
import io
from typing import Dict, List, Optional
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import settings, AVAILABLE_COMMANDS
from models import User, Device, Command, SessionLocal
from security import AuthManager, verify_whitelist, log_operation
from ai_engine import ai_engine


class TelegramBotHandler:
    """معالج بوت Telegram"""

    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.auth_manager = None

    async def start(self):
        """بدء البوت"""
        self.application = Application.builder().token(self.token).build()
        self.auth_manager = AuthManager(SessionLocal())

        # تسجيل المعالجات
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("battery", self.battery_command))
        self.application.add_handler(CommandHandler("storage", self.storage_command))
        self.application.add_handler(CommandHandler("network", self.network_command))
        self.application.add_handler(CommandHandler("files", self.files_command))
        self.application.add_handler(CommandHandler("tasks", self.tasks_command))
        self.application.add_handler(CommandHandler("link", self.link_command))
        self.application.add_handler(CommandHandler("unlink", self.unlink_command))

        # معالجة الرسائل
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))

        # معالجة الأزرار
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

        # بدء البوت
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /start"""
        user = update.effective_user

        # التحقق من القائمة البيضاء
        if not verify_whitelist(user.id):
            await update.message.reply_text(
                "❌ عذراً، ليس لديك إذن للوصول إلى هذا البوت.",
                reply_markup=ReplyKeyboardRemove()
            )
            return

        # إنشاء أو تحديث المستخدم
        db = SessionLocal()
        try:
            self.auth_manager = AuthManager(db)
            db_user = self.auth_manager.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )

            # إنشاء سجل
            log_operation(db, db_user.id, "bot_start", f"المستخدم {user.id} بدأ استخدام البوت")

            # إنشاء لوحة المفاتيح الرئيسية
            keyboard = [
                [KeyboardButton("📊 حالة الجهاز")],
                [KeyboardButton("📁 إدارة الملفات"), KeyboardButton("📋 المهام المجدولة")],
                [KeyboardButton("🔗 ربط جهاز"), KeyboardButton("❓ مساعدة")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"🎉 مرحباً {user.first_name}!\n\n"
                "أنا بوت التحكم بهاتفك الذكي.\n"
                "يمكنني مساعدتك في:\n"
                "• عرض حالة الجهاز\n"
                "• إدارة الملفات\n"
                "• جدولة المهام\n"
                "• والمزيد...\n\n"
                "اضغط على زر 'ربط جهاز' للبدء!",
                reply_markup=reply_markup
            )
        finally:
            db.close()

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /help"""
        help_text = """
🤖 *مساعدة البوت*

*الأوامر المتاحة:*

/start - بدء استخدام البوت
/help - عرض المساعدة
/status - حالة الجهاز
/battery - معلومات البطارية
/storage - معلومات التخزين
/network - معلومات الشبكة
/files - إدارة الملفات
/tasks - المهام المجدولة
/link - ربط جهاز جديد
/unlink - إلغاء ربط الجهاز

*كيفية الاستخدام:*
1. أولاً، ثبت تطبيق Android Agent على هاتفك
2. اضغط 'ربط جهاز' واتبع التعليمات
3. أرسل أوامر للبوت للتحكم بهاتفك

*مثال على الأوامر:*
- "أعرض حالة البطارية"
- "أنشئ مجلد جديد اسمه Backup"
- "احذف ملفات الكاش"
"""

        if update.message:
            await update.message.reply_text(help_text, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.edit_text(help_text, parse_mode="Markdown")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /status"""
        user_id = update.effective_user.id

        if not verify_whitelist(user_id):
            await update.message.reply_text("❌ ليس لديك إذن.")
            return

        db = SessionLocal()
        try:
            # التحقق من ربط جهاز
            device = db.query(Device).join(User).filter(
                User.telegram_id == user_id,
                Device.is_online == True
            ).first()

            if not device:
                await update.message.reply_text(
                    "❌ لم تقم بربط جهاز بعد.\n"
                    "اضغط 'ربط جهاز' للبدء."
                )
                return

            # إرسال طلب للحصول على حالة الجهاز
            await update.message.reply_text("⏳ جاري جلب حالة الجهاز...")

            # هنا يتم إرسال الأمر للجهاز
            # في الإنتاج، سيتم إرسال الطلب للتطبيق
            status_info = {
                "online": True,
                "battery": {"level": 85, "status": "Charging"},
                "storage": {"total": 128, "used": 64},
                "network": {"type": "WiFi", "speed": 50}
            }

            response = f"""
📊 *حالة الجهاز*

✅ الجهاز متصل

🔋 البطارية: {status_info['battery']['level']}%
   الحالة: {status_info['battery']['status']}

💾 التخزين: {status_info['storage']['used']}/{status_info['storage']['total']} GB

🌐 الشبكة: {status_info['network']['type']}
   السرعة: {status_info['network']['speed']} Mbps
"""

            await update.message.reply_text(response, parse_mode="Markdown")
        finally:
            db.close()

    async def battery_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /battery"""
        await update.message.reply_text("🔋 جاري جلب معلومات البطارية...")

        # محاكاة استجابة
        response = """
🔋 *معلومات البطارية*

• المستوى: 85%
• الحالة: قيد الشحن
• درجة الحرارة: 32°C
• السعة: 4500 mAh
"""
        await update.message.reply_text(response, parse_mode="Markdown")

    async def storage_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /storage"""
        await update.message.reply_text("💾 جاري جلب معلومات التخزين...")

        response = """
💾 *معلومات التخزين*

• الإجمالي: 128 GB
• المستخدم: 64 GB
• المتبقي: 64 GB (50%)

*التقسيمات:*
• التطبيقات: 25 GB
• الصور: 20 GB
• الفيديو: 10 GB
• أخرى: 9 GB
"""
        await update.message.reply_text(response, parse_mode="Markdown")

    async def network_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /network"""
        await update.message.reply_text("🌐 جاري جلب معلومات الشبكة...")

        response = """
🌐 *معلومات الشبكة*

• نوع الاتصال: WiFi
• اسم الشبكة: Home-5G
• IP المحلي: 192.168.1.100
• السرعة: 50 Mbps
• الإشارة: ممتازة
"""
        await update.message.reply_text(response, parse_mode="Markdown")

    async def files_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /files"""
        keyboard = [
            [InlineKeyboardButton("📁 عرض الملفات", callback_data="files_list")],
            [InlineKeyboardButton("📤 رفع ملف", callback_data="files_upload")],
            [InlineKeyboardButton("📥 تنزيل ملف", callback_data="files_download")],
            [InlineKeyboardButton("🗑️ حذف ملف", callback_data="files_delete")],
            [InlineKeyboardButton("➕ إنشاء مجلد", callback_data="files_create_folder")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📁 *إدارة الملفات*\n\nاختر الإجراء المطلوب:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /tasks"""
        keyboard = [
            [InlineKeyboardButton("📋 عرض المهام", callback_data="tasks_list")],
            [InlineKeyboardButton("➕ إضافة مهمة", callback_data="tasks_add")],
            [InlineKeyboardButton("❌ حذف مهمة", callback_data="tasks_delete")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📋 *المهام المجدولة*\n\nاختر الإجراء المطلوب:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /link لربط جهاز"""
        user = update.effective_user

        keyboard = [
            [InlineKeyboardButton("📱 فتح تطبيق Android Agent", callback_data="open_app")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔗 *ربط جهاز جديد*\n\n"
            "1. ثبت تطبيق Android Agent على هاتفك\n"
            "2. افتح التطبيق واسمح بالصلاحيات المطلوبة\n"
            "3. أدخل رمز الربط الموضح في التطبيق\n\n"
            "احتاج مساعدة؟ اضغط على الزر أدناه:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def unlink_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /unlink لإلغاء ربط جهاز"""
        user_id = update.effective_user.id

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                # حذف الأجهزة المرتبطة
                db.query(Device).filter(Device.user_id == user.id).delete()
                db.commit()

                await update.message.reply_text(
                    "✅ تم إلغاء ربط جميع الأجهزة بنجاح."
                )
            else:
                await update.message.reply_text(
                    "ℹ️ لم تقم بربط أي جهاز."
                )
        finally:
            db.close()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        user = update.effective_user
        message_text = update.message.text

        # التحقق من القائمة البيضاء
        if not verify_whitelist(user.id):
            return

        # معالجة أزرار لوحة المفاتيح
        if message_text == "📊 حالة الجهاز":
            await self.status_command(update, context)
        elif message_text == "📁 إدارة الملفات":
            await self.files_command(update, context)
        elif message_text == "📋 المهام المجدولة":
            await self.tasks_command(update, context)
        elif message_text == "🔗 ربط جهاز":
            await self.link_command(update, context)
        elif message_text == "❓ مساعدة":
            await self.help_command(update, context)
        else:
            # استخدام AI لتحليل الأمر
            await self.handle_ai_command(update, message_text)

    async def handle_ai_command(self, update: Update, message_text: str):
        """معالجة الأمر باستخدام AI"""
        await update.message.reply_text("🤔 جاري تحليل الأمر...")

        # تحليل الأمر
        result = ai_engine.analyze_command(message_text)

        if result.get("success"):
            # تنفيذ الأمر
            response = ai_engine.generate_response(result, message_text)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                f"❌ {result.get('error', 'تعذر فهم الأمر')}\n\n"
                "جرب استخدام الأزرار أو الأوامر المحددة."
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة استدعاءات الأزرار"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "back_main":
            await self.start_command(update, context)
        elif data == "files_list":
            await query.message.edit_text("📁 جاري عرض الملفات...")
        elif data == "tasks_list":
            await query.message.edit_text("📋 جاري عرض المهام...")

    async def send_file(self, chat_id: int, file_path: str, caption: str = None):
        """إرسال ملف للمستخدم"""
        if not self.application:
            return

        async with self.application.bot:
            await self.application.bot.send_document(
                chat_id=chat_id,
                document=open(file_path, 'rb'),
                caption=caption
            )

    async def send_photo(self, chat_id: int, photo_path: str, caption: str = None):
        """إرسال صورة للمستخدم"""
        if not self.application:
            return

        async with self.application.bot:
            await self.application.bot.send_photo(
                chat_id=chat_id,
                photo=open(photo_path, 'rb'),
                caption=caption
            )


# دالة لتشغيل البوت
def run_bot():
    """تشغيل بوت Telegram"""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN")
        return

    bot = TelegramBotHandler(settings.TELEGRAM_BOT_TOKEN)
    asyncio.run(bot.start())
