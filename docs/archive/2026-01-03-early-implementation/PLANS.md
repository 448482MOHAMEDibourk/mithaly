Mithaly Roadmap and Phases
==========================

هدف هذا الملف: وصف خارطة الطريق للمراحل الرئيسية لتأسيس Mithaly من MVP إلى التشغيل الكامل.

ملخص المراحل
------------

Phase 0 — Light setup (today — dev-ready)
- إعداد بيئة تطوير خفيفة:
  - تأكيد وجود runtime محلي للـ LLM (مثل `ollama`).
  - سكربت بدء بسيط: `scripts/start_llm.sh` (دعم Docker وruntime).
  - مسارات النماذج المحلية: `~/.local/share/mithaly/models`.
  - واجهات مؤقتة/محاكاة للطبقات لاختبار التكامل.
  معيار الانتقال: تنفيذ اختبارات مدخلة تظهر أن `gaps -> planning -> execution -> feedback` تعمل مع mock LLM.

Phase 1 — MVP للطبقات (1–2 أسابيع)
- أهداف:
  - تنفيذ وحدات `GapAnalyzer`, `ExecutionPlanner`, `SafeExecutor`, `FeedbackLoop` بواجهات `process()` قابلة للاختبار.
  - إضافة `LayerRegistry` و`PolicyEnforcer`، وتكامل `model_adapter` للوصول إلى runtime المحلي.
  - حفظ لقطات السياق في `docs/context/` وملف التذاكر `analysis_tickets.json`.
  معيار الانتقال: مرور اختبارات التكامل المحلية وتشغيل سيناريو توليد مشروع بسيط.

Phase 2 — أدوات ونشر (بعد استقرار MVP)
- أهداف:
  - إعداد مكان مركزي للنماذج: `/var/lib/mithaly/models`، ووحدة systemd (`scripts/mithaly-llm.service`).
  - تحديث `scripts/start_llm.sh` لدعم `ollama pull/serve/run` تلقائيًا.
  - إضافة واجهة إدارية بسيطة (Web/CLI) لوسم التذاكر بالثقة (`trusted`).
  - CI: اختبارات مع mocking للـ model_adapter، وjob تحقق `docs` vs `src` sync.
  معيار الانتقال: قدرة النظام على الاستمرار كخدمة وتدفق عمل كامل من التوليد إلى كتابة KB الحقيقية بعد قبول تذاكر.

شروط عامة وسياسات
------------------
- خلال التطوير نحتفظ بـ `docs/` كمساحة staging؛ الترقية إلى `src/mithaly/governance` تتم فقط عندما يصبح الدستور نهائيًا.
- لا تخزن النماذج داخل المستودع؛ أضف مسارات النماذج إلى `.gitignore`.
- تأكد من أن `ollama` أو أي runtime آخر لا يُنقل يدوياً إن كان يُدار عبر مدير حزم.

روابط مفيدة
------------
- قائمة المهام الحالية: `docs/mithaly_todo.md`.
- تعليمات تشغيل LLM المحلية: `scripts/README_LLMS.md`.

إذا رغبت أبدأ الآن بتنفيذ بند واحد من Phase 0: إنشاء `src/mithaly/core/utils/model_adapter.py` بسيط يدعم `ollama` وHTTP fallback.
