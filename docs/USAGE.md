Usage — تشغيل واختبار Mithaly
=============================

تشغيل سريع (مستند إلى نسخة الحزمة في `src`):

1) استيراد وتشغيل دورة المحرك من الحزمة (غير تفاعلي):

Usage — تشغيل واختبار Mithaly
=============================

تشغيل سريع (مستند إلى نسخة الحزمة في `src`):

1) استيراد وتشغيل دورة المحرك من الحزمة (غير تفاعلي):

```bash
PYTHONPATH=./src python3 -c "from mithaly.core.engine import BuildEngine; e=BuildEngine(); e.run_lifecycle({'text':'اختبار'} )"
```

2) تشغيل الرنّير الخفيف من الجذر:

```bash
python3 core/engine.py
```

ملاحظات:
- إذا أردت السلوك التفاعلي (إجابة على أسئلة توضيح)، شغّل الرنّير في طرفية تفاعلية.
- لاختبار الطبقات أو الوحدات المفردة، استوردها مباشرة عبر `PYTHONPATH=./src`.

أمثلة متقدمة:
- تهيئة سياسات مخصصة للـ `PolicyEnforcer`: ضع ملف إعدادات ضمن `docs/knowledge/policies/` ثم حمّله من `PolicyEnforcer` (مستقبلي).

تشغيل الاختبارات وCI:

- تشغيل الاختبارات محلياً (تأكد من وجود `PYTHONPATH=./src`):

```bash
PYTHONPATH=./src python3 tools/tests/probe_policy_tests.py
PYTHONPATH=./src python3 tools/tests/policy_smoke.py
```

- ملف سير العمل للـ CI: [/.github/workflows/ci.yml](.github/workflows/ci.yml) — يقوم بتشغيل الاختبارات على كل `push` و`pull_request`.
