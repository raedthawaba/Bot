"""
محرك الذكاء الاصطناعي
يتضمن: معالجة اللغة الطبيعية، تحليل الأوامر، وتحويلها إلى مهام تنفيذية
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI

from config import settings


class AIEngine:
    """محرك الذكاء الاصطناعي للمشروع"""

    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def analyze_command(self, user_message: str, context: Optional[Dict] = None) -> Dict:
        """
        تحليل أمر المستخدم وتحويله إلى مهمة تنفيذية

        Args:
            user_message: نص الأمر من المستخدم
            context: سياق المحادثة (اختياري)

        Returns:
            Dict: المهمة التنفيذية المحولة
        """
        # أولاً، حاول تحليل الأمر مباشرة
        parsed_command = self._parse_command_directly(user_message)
        if parsed_command:
            return parsed_command

        # إذا فشل التحليل المباشر، استخدم AI
        if self.client:
            return await self._analyze_with_ai(user_message, context)

        # إذا لم يكن هناك AI، أعد خطأ
        return {
            "success": False,
            "error": "تعذر تحليل الأمر. يرجى استخدام أوامر محددة."
        }

    def _parse_command_directly(self, message: str) -> Optional[Dict]:
        """تحليل الأمر مباشرة باستخدام أنماط محددة"""
        message = message.lower().strip()

        # أنماط أوامر الملفات
        file_patterns = {
            r"(?:أعرض|عرض|list).*?(?:ملفات|files)": {
                "action": "list_files",
                "command_type": "file"
            },
            r"(?:أنشئ|إنشاء|create).*?(?:مجلد|folder)": {
                "action": "create_folder",
                "command_type": "file"
            },
            r"(?:حذف|delete).*?(?:ملف|file)": {
                "action": "delete_file",
                "command_type": "file"
            },
            r"(?:رفع|upload).*?(?:ملف)": {
                "action": "upload_file",
                "command_type": "file"
            },
            r"(?:تنزيل|download).*?(?:ملف)": {
                "action": "download_file",
                "command_type": "file"
            },
        }

        # أنماط أوامر النظام
        system_patterns = {
            r"(?:حالة|status).*?(?:جهاز|phone|mobile)": {
                "action": "device_status",
                "command_type": "system"
            },
            r"(?:بطارية|battery)": {
                "action": "battery_info",
                "command_type": "system"
            },
            r"(?:تخزين|storage|memory)": {
                "action": "storage_info",
                "command_type": "system"
            },
            r"(?:شبكة|network|إنترنت)": {
                "action": "network_info",
                "command_type": "system"
            },
            r"(?:معلومات|info).*?(?:النظام|system)": {
                "action": "system_info",
                "command_type": "system"
            },
        }

        # أنماط أوامر المهام
        task_patterns = {
            r"(?:مهام|tasks).*?(?:مجدولة|scheduled)": {
                "action": "list_scheduled_tasks",
                "command_type": "task"
            },
            r"(?:أنشئ|إنشاء).*?(?:مهمة|task)": {
                "action": "create_task",
                "command_type": "task"
            },
            r"(?:حذف|delete).*?(?:مهمة|task)": {
                "action": "delete_task",
                "command_type": "task"
            },
        }

        # التحقق من الأنماط
        all_patterns = {**file_patterns, **system_patterns, **task_patterns}

        for pattern, result in all_patterns.items():
            if re.search(pattern, message):
                result_copy = result.copy()
                # استخراج المعلمات من الرسالة
                params = self._extract_parameters(message)
                result_copy["parameters"] = params
                result_copy["success"] = True
                return result_copy

        return None

    def _extract_parameters(self, message: str) -> Dict[str, Any]:
        """استخراج المعلمات من رسالة المستخدم"""
        params = {}

        # استخراج مسار الملف
        path_match = re.search(r"(?:في|to|from|/)\s*([/\w\s]+)", message)
        if path_match:
            params["path"] = path_match.group(1).strip()

        # استخراج اسم الملف أو المجلد
        name_match = re.search(r"(?:اسم|name)\s*[:\-]?\s*(\w+)", message)
        if name_match:
            params["name"] = name_match.group(1)

        return params

    async def _analyze_with_ai(self, user_message: str, context: Optional[Dict] = None) -> Dict:
        """تحليل الأمر باستخدام OpenAI"""
        system_prompt = """أنت مساعد ذكي يتحكم في هاتف Android. مهمتك هي تحويل أوامر المستخدم إلى مهام تنفيذية JSON.

الأوامر المدعومة:

1. إدارة الملفات:
   - list_files: عرض الملفات في مجلد
   - create_folder: إنشاء مجلد جديد
   - delete_file: حذف ملف
   - upload_file: رفع ملف
   - download_file: تنزيل ملف

2. معلومات النظام:
   - device_status: حالة الجهاز الشاملة
   - battery_info: معلومات البطارية
   - storage_info: معلومات التخزين
   - network_info: معلومات الشبكة

3. المهام:
   - list_scheduled_tasks: عرض المهام المجدولة
   - create_task: إنشاء مهمة مجدولة
   - delete_task: حذف مهمة

المخرجات يجب أن تكون JSON فقط بدون أي نص آخر:
{
  "success": true/false,
  "command_type": "file/system/task/ai",
  "action": "اسم_الأمر",
  "parameters": {
    // المعلمات المطلوبة للأمر
  },
  "description": "وصف的人类看得懂的"
}

إذا لم تتمكن من فهم الأمر، أعد:
{
  "success": false,
  "error": "سبب_الخطأ"
}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()

            # استخراج JSON من النتيجة
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            result = json.loads(result_text)
            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في تحليل الأمر: {str(e)}"
            }

    def analyze_data(self, data: str, data_type: str = "text") -> Dict:
        """تحليل البيانات باستخدام AI

        Args:
            data: البيانات المراد تحليلها
            data_type: نوع البيانات (text, csv, log)

        Returns:
            Dict: نتيجة التحليل
        """
        if not self.client:
            return {
                "success": False,
                "error": "خدمة AI غير متاحة"
            }

        prompts = {
            "text": "حلل النص التالي وأعط ملخصاً وأفكاراً رئيسية:",
            "csv": "حلل بيانات CSV التالية وأعط إحصائيات وأفكار:",
            "log": "حلل ملف السجل التالي وحدد المشاكل والأخطاء:"
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "أنت محلل بيانات متخصص. أجب بالعربية."},
                    {"role": "user", "content": f"{prompts.get(data_type, prompts['text'])}\n\n{data[:2000]}"}
                ],
                temperature=0.5,
                max_tokens=1000
            )

            return {
                "success": True,
                "result": response.choices[0].message.content
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def suggest_actions(self, context: Dict) -> List[str]:
        """اقتراح إجراءات للمستخدم بناءً على السياق"""
        suggestions = []

        # اقتراحات بناءً على حالة الجهاز
        if context.get("battery_low"):
            suggestions.append("خفض سطوع الشاشة")
            suggestions.append("إغلاق التطبيقات المفتوحة")

        if context.get("storage_low"):
            suggestions.append("حذف ملفات الكاش")
            suggestions.append("نقل الصور إلى السحابة")

        if context.get("network_slow"):
            suggestions.append("إعادة تشغيل الواي فاي")
            suggestions.append("البحث عن شبكات أفضل")

        return suggestions

    def generate_response(self, command_result: Dict, user_message: str) -> str:
        """إنشاء رد مناسب للمستخدم"""
        if not command_result.get("success"):
            return f"❌ حدث خطأ: {command_result.get('error', 'خطأ غير معروف')}"

        # تنسيق النتيجة
        response = "✅ تم تنفيذ الأمر بنجاح\n\n"

        if command_result.get("command_type") == "system":
            response += self._format_system_info(command_result.get("result", {}))
        elif command_result.get("command_type") == "file":
            response += self._format_file_info(command_result.get("result", {}))
        elif command_result.get("command_type") == "task":
            response += self._format_task_info(command_result.get("result", {}))
        else:
            response += str(command_result.get("result", {}))

        return response

    def _format_system_info(self, result: Dict) -> str:
        """تنسيق معلومات النظام"""
        lines = []

        if "battery" in result:
            battery = result["battery"]
            lines.append(f"🔋 البطارية: {battery.get('level', 'N/A')}%")
            lines.append(f"   الحالة: {battery.get('status', 'N/A')}")

        if "storage" in result:
            storage = result["storage"]
            lines.append(f"💾 التخزين: {storage.get('used', 'N/A')}/{storage.get('total', 'N/A')} GB")

        if "network" in result:
            network = result["network"]
            lines.append(f"🌐 الشبكة: {network.get('type', 'N/A')}")
            if network.get("speed"):
                lines.append(f"   السرعة: {network.get('speed')} Mbps")

        return "\n".join(lines)

    def _format_file_info(self, result: Dict) -> str:
        """تنسيق معلومات الملفات"""
        lines = []

        if "files" in result:
            files = result["files"]
            lines.append(f"📁 الملفات ({len(files)}):")
            for f in files[:10]:  # عرض أول 10 ملفات
                lines.append(f"   • {f.get('name')} ({f.get('size', 'N/A')})")

        if "folder" in result:
            lines.append(f"✅ تم إنشاء المجلد: {result['folder']}")

        if "deleted" in result:
            lines.append(f"🗑️ تم حذف: {result['deleted']}")

        return "\n".join(lines)

    def _format_task_info(self, result: Dict) -> str:
        """تنسيق معلومات المهام"""
        lines = []

        if "tasks" in result:
            tasks = result["tasks"]
            lines.append(f"📋 المهام ({len(tasks)}):")
            for task in tasks:
                status_icon = "✅" if task.get("active") else "❌"
                lines.append(f"   {status_icon} {task.get('name')}")

        if "created" in result:
            lines.append(f"✅ تم إنشاء المهمة: {result['created']}")

        return "\n".join(lines)


# إنشاء كائن المحرك
ai_engine = AIEngine()
