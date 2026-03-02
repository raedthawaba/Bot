import os

class CodeGenerator:
    """مولد الكود المسؤول عن تحويل هيكل البيانات إلى ملفات Dart/Flutter"""
    
    def __init__(self, output_dir="generated_flutter_app"):
        self.output_dir = output_dir
        self.lib_dir = os.path.join(self.output_dir, "lib")
        self.screens_dir = os.path.join(self.lib_dir, "screens")

    def generate_project(self, project_structure):
        """توليد المشروع بالكامل"""
        print(f"🛠️ جاري توليد مشروع Flutter: {project_structure['app_name']}")
        
        # إنشاء المجلدات
        os.makedirs(self.screens_dir, exist_ok=True)

        # توليد ملف main.dart
        self._generate_main_dart(project_structure)

        # توليد الصفحات (Screens)
        for page in project_structure["pages"]:
            self._generate_screen(page)

        print(f"✅ تم توليد المشروع بنجاح في: {self.output_dir}")

    def _generate_main_dart(self, project_structure):
        """توليد ملف main.dart الأساسي"""
        main_content = f"""
import 'package:flutter/material.dart';
import 'screens/{project_structure['pages'][0]['name'].lower()}.dart';

void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{project_structure['app_name']}',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const {project_structure['pages'][0]['name']}(),
    );
  }}
}}
"""
        with open(os.path.join(self.lib_dir, "main.dart"), "w", encoding="utf-8") as f:
            f.write(main_content.strip())

    def _generate_screen(self, page):
        """توليد ملف Dart لكل صفحة"""
        elements_code = []
        for element in page["elements"]:
            if element["type"] == "button":
                elements_code.append(f"ElevatedButton(onPressed: () {{}}, child: const Text('{element.get('label', 'Button')}')),")
            elif element["type"] == "input":
                elements_code.append(f"const TextField(decoration: InputDecoration(hintText: '{element.get('hint', 'Enter text...')}')),")
            elif element["type"] == "text":
                elements_code.append(f"const Text('{element.get('value', 'Text')}', style: TextStyle(fontSize: 20)),")

        screen_content = f"""
import 'package:flutter/material.dart';

class {page['name']} extends StatelessWidget {{
  const {page['name']}({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{page['name']}'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            {chr(10).join(elements_code)}
          ],
        ),
      ),
    );
  }}
}}
"""
        filename = f"{page['name'].lower()}.dart"
        with open(os.path.join(self.screens_dir, filename), "w", encoding="utf-8") as f:
            f.write(screen_content.strip())
