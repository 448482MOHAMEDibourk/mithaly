# تكامل الإستراتيجية مع السياق - 2025-12-24

## 1. ملخص الأهداف (مستخلص من `strategy/GOALS.md`)
- الهدف النهائي: إنتاج مشاريع قابلة للتشغيل والنشر في المجلد `OUTPUT/` بدءًا من المواصفات والوصف النصي المتوفر في `INPUT/`.
- أولويات حالية:
  - تهيئة بيئة توجيهية واضحة ومثبتة للمهام (تنظيم: `AGENT_CONTEXT.json`, `CONTEXT_LOG.jsonl`).
  - استخراج خارطة طريق وملخّص التنفيذ من الأرشيف `/home/eburk/Documents/mithaly/project_management/archive/14.12.2025`.
  - تحسين أداء التنفيذ عبر تنفيذ متوازٍ، ذاكرة سياقية محسنة، وآليات تصحيح تلقائي.

## 2. قواعد تشغيلية تؤثر على التنفيذ (مستخلص من `strategy/rules/architecture_rules.json`)
- "dependency_flow_rules": التحقق من تبعيات التدفق الوظيفي قبل تنفيذ أي خطة (قواعد: `check_dependencies`, `validate_flow`).
- "functional_poles" → `decision_logic` مفعّل: وجود قواعد متعلقة بمنطق القرارات داخل الوحدات (قواعد ابتدائية: `logic1`, `logic2`).

## 3. المهام العالقة الحرجة (مستخلصة من `strategy/tasks/core`)
1. `task_1_debug_node.md` — إضافة `debug_node` إلى `core/graph.py` لدمج `DebuggerSpecialist` في تدفق التنفيذ عند الفشل.
2. `task_2_register_specialist.md` — تسجيل `DebuggerSpecialist` في `core/engine.py` لضمان تهيئته وتوفّره.
3. `task_3_verification.md` — التحقّق باستخدام `INPUT/multistack_debug_demo` للتأكد من أن آلية التصحيح تعمل وتُنتج ملف باتش.

ملاحظة: هذه المهام تعتبر محورًا ذا أولوية عالية لأنها تؤمن آلية التصحيح التلقائي (key reliability loop).

### حالة المهام

- `task_2_register_specialist.md`: **مكتمل** (مسجّل DebuggerSpecialist في `core/engine.py` بتاريخ 2025-12-24)
- `task_1_debug_node.md`: لم يبدأ بعد
- `task_3_verification.md`: لم يبدأ بعد

## 4. الفجوات الحرجة وربطها بالـ Blueprint
- لا يزال غائبًا endpoint مخصّص لتوليد مشروع من وصف حر (`/api/v1/generate/project`). (يرتبط بتوصية في `blueprint_summary.md`)
- غياب اختبار دمج (CI) يضمن عدم انزلاق العقد (API ↔ run_mission.py).
- الحاجة لصياغة صريحة لنماذج Pydantic تعكس العقد وتظهر في OpenAPI.

## 5. توصيات تنفيذية قصيرة المدى (قابلة للتنفيذ الآن)
1. أتم الأولوية: إكمال المهام `task_1`, `task_2`, `task_3` بترتيب التنفيذ التالي:
   - أ) `task_2`: تأكيد تسجيل `DebuggerSpecialist` في `core/engine.py` (سريع، يقلل أخطاء التهيئة).
   - ب) `task_1`: إضافة `debug_node` في `core/graph.py` وربط المسارات المناسبة.
   - ج) `task_3`: تشغيل تحقق باستخدام `INPUT/multistack_debug_demo` والتحقق من ناتج الباتش.

2. دمج نتيجة المهمة أعلاه في سياق التشغيل: أضف إدخالًا في `CONTEXT_LOG.jsonl` مع `mission_result` و`decision` عند نجاح التحقق.

3. تنفيذ CI-smoke: سكربت بسيط يقوم بتشغيل خادم FastAPI محليًا ثم يرسل الطلبات الثلاثة المتوافقة إلى `/api/v1/agents/run`، للتحقق من تماسك العقد.

4. تصميم نموذج Pydantic مبدئي لـ `ProjectGenerationRequest` وبدء تنفيذ نقطة نهاية `POST /api/v1/generate/project` كـ "بوابة مردّدة" تستخدم `AgentService` لبدء مهمات التوليد.

## 6. التوصية للخطوة التالية (فورية)
- أبدأ بتطبيق `task_2_register_specialist.md` الآن (تعديل صغير في `core/engine.py`). بعد ذلك أتابع `task_1` ثم `task_3` للتحقق.

---

ملف هذا يُضاف إلى الذاكرة السياقية ليتوافق مع `blueprint_summary.md` ويُستخدم لتوجيه الخطوات التنفيذية التالية.
