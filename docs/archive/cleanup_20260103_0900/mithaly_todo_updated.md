# مهام Mithaly

## 🔴 مهام غير منجزة

### أولوية عالية
- [ ] تنفيذ توسيع `PolicyEnforcer` لقراءة تحريات الطبقات (Layer-sourced probes)

### أولوية متوسطة
- [ ] إضافة حالة `INFLECTION_POINT` في `BuildEngine` للقرار الاستباقي

### أولوية منخفضة
- [ ] دمج تحقق من بيئة التشغيل (preflight) ضمن `ExecutionPlanner`

## 🔄 قيد التنفيذ
- [x] **الدستور + المحرك**: تفعيل "قاعدة الانعطافية" — تقدم ملحوظ
  - تمت صياغة المبادئ في `docs/MITHALY_CONSTITUTION.md` (المولد مستقل والطبقات قادة إداريون وخدام).
  - أنشأت `PolicyEnforcer` ودمجتُه في مسار التنفيذ قبل التخطيط (`src/mithaly/core/policy.py`).
  - أنشأتُ `LayerRegistry` (`src/mithaly/core/registry.py`) لتمكين تسجيل الطبقات واكتشافها ديناميكياً.
  - نقلتُ المحرك المرجعي داخل الحزمة: `src/mithaly/core/engine.py` وإنشأت runner خفيف في `core/engine.py`.

**خطوات قادمة في هذه المهمة:**
- توسيع `PolicyEnforcer` لقراءة تحريات الطبقات المسجلة (Layer probes) ووزن القرارات.
- تعريف رسالة `INFLECTION_POINT` في حالة الحاجة إلى إيقاف أو إعادة توجيه التنفيذ.

## ✅ مهام منجزة
- [x] إنشاء `BuildEngine` داخل الحزمة - 2026-01-01
- [x] إعداد بنية المشروع الأساسية (مجلدات، docs، knowledge) - 2026-01-01
- [x] إضافة `LayerRegistry` - 2026-01-01
- [x] إضافة ودمج `PolicyEnforcer` (أساس) - 2026-01-01

---
*آخر تحديث: 2026-01-01*
