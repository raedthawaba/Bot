#!/data/data/com.termux/files/usr/bin/bash

# الانتقال لمجلد المشروع
cd "$(dirname "$0")"

# تفعيل البيئة الافتراضية إذا كانت موجودة
if [ -d "venv" ]; then
    echo "تفعيل البيئة الافتراضية (venv)..."
    source venv/bin/activate
else
    echo "خطأ: البيئة الافتراضية (venv) غير موجودة. يرجى تشغيل ./setup_termux.sh أولاً."
    exit 1
fi

# تشغيل البوت
echo "جاري تشغيل البوت..."
python main.py
