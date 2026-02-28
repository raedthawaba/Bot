#!/data/data/com.termux/files/usr/bin/bash

# تحديث المستودعات وتثبيت الحزم الأساسية وأدوات البناء
echo "جاري تحديث المستودعات وتثبيت أدوات البناء المتقدمة..."
pkg update -y && pkg upgrade -y
pkg install python git clang make rust pkg-config libffi openssl ndk-sysroot binutils -y

# ضبط متغيرات البيئة للبناء (حل مشكلة pydantic-core)
echo "ضبط متغيرات البيئة للبناء..."
export ANDROID_API_LEVEL=24
if ! grep -q "ANDROID_API_LEVEL" ~/.bashrc; then
    echo 'export ANDROID_API_LEVEL=24' >> ~/.bashrc
fi

# إنشاء بيئة افتراضية (venv) لضمان استقرار المكتبات
echo "إنشاء بيئة افتراضية (venv)..."
python -m venv venv
source venv/bin/activate

# تحديث أدوات pip داخل البيئة الافتراضية
echo "تحديث pip و setuptools و wheel..."
pip install --upgrade pip setuptools wheel

# تثبيت المتطلبات البرمجية للبوت
echo "جاري تثبيت مكتبات Python المطلوبة (قد يستغرق وقتاً لبناء pydantic-core)..."
pip install -r requirements.txt

# إنشاء مجلدات العمل الضرورية
mkdir -p uploads

echo "----------------------------------------"
echo "تم الانتهاء من التثبيت بنجاح!"
echo "لتشغيل البوت، استخدم الأمر التالي:"
echo "source venv/bin/activate && python main.py"
echo "----------------------------------------"
