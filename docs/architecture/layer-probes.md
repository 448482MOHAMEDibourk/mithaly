Layer probes — مواصفات مبسطة
=============================

الهدف
-----
تحديد واجهة قياسية (Probe) تُعلنها كل طبقة في Mithaly (gaps, planning, execution, feedback). تُسهل هذه الواجهة تبادل معلومات قابلة للقياس بين الطبقات و/أو أنظمة الحوكمة (مثل `PolicyEnforcer`) لاتخاذ قرارات مثل نقاط الانعطاف (INFLECTION_POINT).

متى تُستخدم
----------
- عند بداية معالجة مدخل المستخدم تُصدَر Probe من كل طبقة بناءً على التحليل الحالي.
- تُستخدم البروبس لشرح متطلبات (requirements)، قدرات (capabilities)، وسمات المهمة الحالية.

مخطط الحقول المقترح (YAML)
---------------------------
- `layer`: اسم الطبقة.
- `capabilities`: قائمة سلاسل تبين وظائف الطبقة (مث: extract_keywords).
- `requirements`: خريطة تُشير إلى احتياجات ممكنة أو مؤكدة (requires_db: yes/maybe/no).
- `attributes`: خريطة سمات إضافية (sensitive, estimated_time_seconds, priority).

مثال Probe (YAML):

```yaml
layer: gaps
capabilities:
  - extract_keywords
  - detect_databases
requirements:
  requires_db: maybe
  requires_network: yes
attributes:
  sensitive: false
  estimated_time_seconds: 30
```

حقل `requirements` يجب أن يستخدم قيماً قياسية: `yes`, `no`, `maybe`، أو أرقام/قيم قابلة للقياس (مثل `min_memory_mb`).

إرشادات التكامل
----------------
- تنتج كل طبقة Probe بعد تنفيذ التحليل الأصلي للمدخل.
- تجمع `LayerRegistry` البروبس (إن وُجدت) وتعرضها للـ `PolicyEnforcer` قبل مرحلة التخطيط.
- يجب على `PolicyEnforcer` قبول البروبس كمصدر للمعلومات مع `docs/knowledge/policies/*` لتوليد `policy_constraints`.

أمثلة استخدام لكل طبقة
----------------------
- gaps: تُعلن لغات مكتشفة، قواعد بيانات متوقعة، احتياجات توضيح.
- planning: تُعلن ما إذا كانت الخطة تعتمد على أدوات خارجية، أم أنها ستتطلب وقت تنفيذ طويل.
- execution: تُعلن متطلبات وقت تشغيل، حالات فشل معروفة، أو متطلبات بيئة (مثل docker).
- feedback: تُعلن ملاحظات استمرارية أو مخاطر متوقعة بعد التنفيذ.

ملاحظات
-------
- هذه مواصفة مبسطة؛ يمكن توسيعها لاحقاً لتشمل نسخ schema (v1, v2) أو توقيع JSON Schema مفصل.
- بعد الموافقة، أنصح بإضافة أمثلة حية في `tools/tests/` حيث تُصدَر بروبس وهمية وتُمرّر خلال محرك الاختبار.
