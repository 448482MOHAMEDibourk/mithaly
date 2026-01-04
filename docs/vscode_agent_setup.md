# إعداد بيئة التطوير في VS Code لعمليات الوكيل المخصص (Custom Agent)

مرحبًا — هذا الملف يشرح الإعداد السريع لتطوير وتشغيل وكيل Mithaly داخل VS Code.

الخطوات الموصى بها:

- افتح المجلد الجذري للمشروع في VS Code: `File → Open Folder` → اختر `/home/eburk/Documents/mithaly`.
- اعتمد الاكتشاف التلقائي لمفسّر Python (Settings: `Python: Select Interpreter`).
- التمديدات الموصى بها:
  - `ms-python.python`
  - `ms-python.vscode-pylance`

الملفات المفيدة في `.vscode/`:
- `settings.json` — إعدادات تنسيق واختبار أساسية (format on save, pytest).
- `launch.json` — تكوينات لتشغيل المحرك، تشغيل ملف، أو تشغيل `pytest`.
- `tasks.json` — مهام جاهزة للتشغيل السريع: تشغيل المحرك، تشغيل الاختبارات، ومسح التكرارات.

تشغيل سريع من داخل VS Code:

1. لبدء المحرك: افتح لوحة الأوامر (Ctrl+Shift+P) → `Tasks: Run Task` → اختر `Run Mithaly Engine`.
2. لتشغيل الاختبارات: اختَر `Run tests (pytest)` من `Tasks` أو استخدم `Debug: Start Debugging` مع تكوين `Python: pytest`.

ملاحظات أمان:
- الإعدادات لا تغيّر أي ملف مصدر. المهام التي تحرّر/تحذف ملفات تطلب تأكيدًا صريحًا.

إذا رغبت، أنشئ فرعًا آخر للعمل التجريبي قبل الدمج: `git checkout -b feature/agent-vscode-config`.
