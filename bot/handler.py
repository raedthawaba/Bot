import os
import shutil
import zipfile
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_engine.engine import AIEngine
from code_generator.generator import CodeGenerator
from config import TELEGRAM_BOT_TOKEN

class TelegramBotHandler:
    """معالج بوت تليجرام لنظام AI Flutter Generator"""
    
    def __init__(self):
        self.engine = AIEngine()
        self.generator = CodeGenerator()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /start"""
        await update.message.reply_text(
            "🚀 مرحباً بك في بوت AI Flutter Generator!\n\n"
            "أرسل لي وصفاً للتطبيق الذي تريده (بالعربية أو الإنجليزية)، "
            "وسأقوم بتوليد كود Flutter كامل لك وإرساله كملف مضغوط.\n\n"
            "مثال: 'أنشئ صفحة تسجيل دخول مع زر وحقل نص'"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة رسائل المستخدم وتوليد التطبيق"""
        user_command = update.message.text
        if not user_command:
            return

        await update.message.reply_text(f"🔍 جاري تحليل طلبك: '{user_command}'...")

        try:
            # 1. تحليل الأمر
            project_structure = self.engine.analyze_command(user_command)
            
            # 2. توليد الكود في مجلد مؤقت لكل مستخدم
            user_id = update.effective_user.id
            output_dir = f"generated_app_{user_id}"
            
            # تنظيف المجلد إذا كان موجوداً
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            
            # تحديث مسار المولد للمجلد المؤقت
            self.generator.output_dir = output_dir
            self.generator.lib_dir = os.path.join(output_dir, "lib")
            self.generator.screens_dir = os.path.join(self.generator.lib_dir, "screens")
            
            self.generator.generate_project(project_structure)

            # 3. ضغط المجلد لإرساله
            zip_filename = f"flutter_app_{user_id}.zip"
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        zipf.write(os.path.join(root, file), 
                                   os.path.relpath(os.path.join(root, file), output_dir))

            # 4. إرسال الملف للمستخدم
            await update.message.reply_text("✅ تم توليد التطبيق بنجاح! جاري إرسال الملف...")
            with open(zip_filename, 'rb') as f:
                await update.message.reply_document(document=f, filename="flutter_project.zip")

            # تنظيف الملفات المؤقتة
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

        except Exception as e:
            await update.message.reply_text(f"❌ عذراً، حدث خطأ أثناء توليد التطبيق: {str(e)}")

    def run(self):
        """تشغيل البوت"""
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        print("🤖 بوت التليجرام قيد التشغيل...")
        application.run_polling()
