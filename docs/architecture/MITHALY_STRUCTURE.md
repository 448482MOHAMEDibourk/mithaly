Project structure — بنية المشروع (موجز)
=====================================

جذر المشروع: `/home/eburk/Documents/mithaly`

- `src/`  : حزمة المصدرية (`src/mithaly`)
  - `src/mithaly/core/` : طبقات النظام والمحرّك المرجعي (`gaps`, `planning`, `execution`, `feedback`, `engine`, `policy`, `registry`).

- `core/` : واجهة/runner على مستوى الجذر (رينّر خفيف يستدعي `src` engine).
- `project-generator/` : مولد المشاريع وملفّات القوالب الخاصة بالتوليد.
- `tools/` : أدوات مساعدة (linters, helpers, scripts).
- `docs/` : توثيق المشروع ومرجع المعرفة (`MITHALY_CONSTITUTION.md`, `knowledge/`, `USAGE.md`).
- `Raw_Artifact/` : أرشيف المشاريع القديمة/الفاشلة.
- `GitHub Copilot/` : سجلات ومساعدات وكيل Copilot وملفات سياق المحادثة.

ممارسات مُوصى بها:
- لا تضع منطق الحزمة في ملفات على مستوى الجذر؛ احتفظ بمنطق التنفيذ في `src/mithaly` ورنّرات خفيفة في الجذر.
- ضع السياسات والأنماط في `docs/knowledge/` لتكون مرجعًا للعاملين والآلات.
