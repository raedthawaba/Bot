#!/data/data/com.termux/files/usr/bin/bash

# تحديث المستودعات وتثبيت الحزم الأساسية
echo "جاري تحديث المستودعات وتثبيت الحزم الأساسية..."
pkg update -y && pkg upgrade -y
pkg install python git binutils rust make clang -y

# تثبيت مكتبات التشفير والاعتماديات التي تفشل في pip
echo "جاري تثبيت مكتبات التشفير والاعتماديات عبر pkg..."
pkg install python-cryptography python-pydantic -y

# تثبيت المتطلبات البرمجية للبوت
echo "جاري تثبيت مكتبات Python المطلوبة..."
# ملاحظة: في Termux يفضل عدم استخدام --upgrade pip لتجنب كسر الحزمة
pip install -r requirements.txt

# إنشاء مجلدات العمل الضرورية
mkdir -p uploads

echo "----------------------------------------"
echo "تم الانتهاء من التثبيت بنجاح!"
echo "لتشغيل البوت، استخدم الأمر التالي:"
echo "python main.py"
echo "----------------------------------------"
