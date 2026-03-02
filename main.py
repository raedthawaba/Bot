import sys
import os
from ai_engine.engine import AIEngine
from code_generator.generator import CodeGenerator

def main():
    """نقطة البداية لنظام توليد تطبيقات Flutter بالذكاء الاصطناعي"""
    print("🚀 مرحباً بك في نظام AI Flutter Generator!")
    print("----------------------------------------")
    
    # استقبال أمر المستخدم
    if len(sys.argv) > 1:
        user_command = " ".join(sys.argv[1:])
    else:
        user_command = input("✍️ أدخل وصف التطبيق الذي تريده (مثال: صفحة تسجيل دخول مع زر وحقل نص): ")

    if not user_command.strip():
        print("❌ لم يتم إدخال أي أمر. يرجى المحاولة مرة أخرى.")
        return

    # 1. تحليل الأمر عبر محرك الذكاء الاصطناعي
    engine = AIEngine()
    project_structure = engine.analyze_command(user_command)

    # 2. توليد الكود عبر مولد الكود
    generator = CodeGenerator()
    generator.generate_project(project_structure)

    print("----------------------------------------")
    print("🎉 تم الانتهاء من توليد التطبيق بنجاح!")
    print("📂 يمكنك العثور على الملفات في مجلد: generated_flutter_app")
    print("📱 لتشغيل التطبيق، تأكد من تثبيت Flutter SDK ثم قم بتشغيل: flutter run")

if __name__ == "__main__":
    main()
