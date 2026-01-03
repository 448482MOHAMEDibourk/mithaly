# فرض القواعد والمنهجية (Enforcement & Methodology)

يحدد هذا المستند المتطلبات التشغيلية لفرض النظام والمنهجية داخل مستودع Mithaly، وتحديداً في بيئات التطوير (GitHub و VSCode).

## 1. تهيئة النظام (System Configuration)
يجب تهيئة المجلدات التالية لفرض القواعد:
- `.github/`: لفرض الفحوصات الآلية (CI).
- `.vscode/`: لتهيئة مهام الوكيل وأدوات المساعدة.

## 2. توجيهات الوكيل (Agent Instructions)
يجب على الوكيل (`mithaly_agent`) الالتزام بالآتي:

### أ. فرض القواعد (Rule Enforcement)
- الالتزام بقواعد الملفات الثابتة المعرفة في:
    - `/home/eburk/Documents/mithaly/docs`
    - `/home/eburk/Documents/mithaly/docs/architecture`

### ب. فرض المنهجية (Methodology Enforcement)
- **الاسترشاد بالخطط:** استخدام `/home/eburk/Documents/mithaly/docs/audit` و `/home/eburk/Documents/mithaly/docs/PLANS.md` (المؤرشف) كملاحظات وخطط تقنية.
- **إدارة السياق:** الالتزام بقراءة السياق المعماري في `/home/eburk/Documents/mithaly/docs/context` قبل كل عملية، وتسجيل التحديثات بعدها.
- **تتبع المهام:** فرض تسجيل كل مهمة في `/home/eburk/Documents/mithaly/docs/mithaly_todo.md` قبل التنفيذ، وترتيب الحالة بعد التنفيذ.
- **إدارة المعرفة:** تحديث السجلات وحفظ أنماط الفشل والنجاح في `/home/eburk/Documents/mithaly/docs/knowledge`.

## 3. الإدارة المؤقتة
تُعتبر `/home/eburk/Documents/mithaly/docs` هي مركز إدارة النظام في مرحلة التأسيس، قبل أن يتم تفويض الإدارة للنظام بشكل آلي وسيادي بالكامل.
