import re

class AIEngine:
    """محرك الذكاء الاصطناعي لتحليل أوامر المستخدم وتحويلها إلى هيكل بيانات"""
    
    def __init__(self):
        # كلمات مفتاحية بسيطة للتحليل الأولي (يمكن توسيعها باستخدام NLP لاحقاً)
        self.keywords = {
            "page": ["صفحة", "شاشة", "page", "screen"],
            "button": ["زر", "أضف زر", "button"],
            "input": ["حقل", "إدخال", "input", "textfield"],
            "text": ["نص", "text", "label"],
            "color": ["لون", "color", "theme"]
        }

    def analyze_command(self, command):
        """تحليل النص وتحويله إلى هيكل بيانات يمثل التطبيق"""
        print(f"🔍 جاري تحليل الأمر: {command}")
        
        # هيكل افتراضي للمشروع
        project_structure = {
            "app_name": "MyGeneratedApp",
            "pages": []
        }

        # تقسيم الأمر حسب الصفحات (إذا وجد)
        pages_raw = re.split(r'صفحة|شاشة|page|screen', command)
        
        for idx, p_content in enumerate(pages_raw):
            if not p_content.strip():
                continue
                
            page = {
                "name": f"Page{idx}",
                "elements": []
            }

            # البحث عن الأزرار
            if any(word in p_content for word in self.keywords["button"]):
                page["elements"].append({"type": "button", "label": "Click Me"})

            # البحث عن حقول الإدخال
            if any(word in p_content for word in self.keywords["input"]):
                page["elements"].append({"type": "input", "hint": "Enter text..."})

            # البحث عن النصوص
            if any(word in p_content for word in self.keywords["text"]):
                page["elements"].append({"type": "text", "value": "Hello World"})

            project_structure["pages"].append(page)

        if not project_structure["pages"]:
            # إضافة صفحة افتراضية إذا لم يتم التعرف على أي صفحة
            project_structure["pages"].append({
                "name": "HomePage",
                "elements": [{"type": "text", "value": "Welcome to AI App"}]
            })

        return project_structure
