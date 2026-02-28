#!/data/data/com.termux/files/usr/bin/bash

# تحديث المستودعات وتثبيت الحزم الأساسية
echo "جاري تحديث المستودعات وتثبيت الحزم الأساسية..."
pkg update -y && pkg upgrade -y
pkg install python python-pip git -y

# تثبيت المتطلبات البرمجية للبوت
echo "جاري تثبيت مكتبات Python المطلوبة..."
pip install --upgrade pip
pip install -r requirements.txt

# إنشاء مجلدات العمل الضرورية
mkdir -p uploads

echo "----------------------------------------"
echo "تم الانتهاء من التثبيت بنجاح!"
echo "لتشغيل البوت، استخدم الأمر التالي:"
echo "python main.py"
echo "----------------------------------------"
