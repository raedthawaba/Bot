import sys
import os
from ai_engine.engine import AIEngine
from code_generator.generator import CodeGenerator
from bot.handler import TelegramBotHandler

def main():
    """نقطة البداية لنظام توليد تطبيقات Flutter بالذكاء الاصطناعي"""
    print("🚀 مرحباً بك في نظام AI Flutter Generator!")
    print("----------------------------------------")
    
    # خيارات التشغيل
    print("1. تشغيل عبر سطر الأوامر (CLI)")
    print("2. تشغيل عبر بوت تليجرام (Telegram Bot)")
    
    choice = input("👉 اختر طريقة التشغيل (1 أو 2): ")

    if choice == "1":
        user_command = input("✍️ أدخل وصف التطبيق الذي تريده: ")
        if not user_command.strip():
            print("❌ لم يتم إدخال أي أمر.")
            return
        
        engine = AIEngine()
        project_structure = engine.analyze_command(user_command)
        generator = CodeGenerator()
        generator.generate_project(project_structure)
        print("🎉 تم توليد التطبيق في مجلد: generated_flutter_app")

    elif choice == "2":
        bot = TelegramBotHandler()
        bot.run()
    
    else:
        print("❌ اختيار غير صحيح.")

if __name__ == "__main__":
    main()
