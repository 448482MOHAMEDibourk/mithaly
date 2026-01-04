Local LLM runtime — تشغيل محلي للنماذج
=====================================

هذا الدليل يشرح كيفية تشغيل نموذج محلي (LLM) لخدمات Mithaly.

1) متغيرات بيئة مُوصى بها

- `MITHALY_MODELS_PATH` — مسار المجلد الذي يحتوي النماذج (افتراضي: `~/.local/share/mithaly/models`).
- `MITHALY_LLM_RUNTIME` — مسار بايناري/سيرفر runtime (إن كنت لا تستخدم Docker).
- `LLM_DOCKER_IMAGE` — صورة Docker المراد استخدامها (الافتراضي في السكربت هو `ollama/ollama:latest`).

2) أوامر سريعة

لتشغيل باستخدام Docker (موصى به للعزل):

```bash
export MITHALY_MODELS_PATH=~/.local/share/mithaly/models
export LLM_DOCKER_IMAGE=ollama/ollama:latest   # عدّل حسب الحاجة
scripts/start_llm.sh docker
```

لتشغيل باستخدام بايناري محلي:

```bash
export MITHALY_MODELS_PATH=~/.local/share/mithaly/models
export MITHALY_LLM_RUNTIME=/opt/mithaly/llm/bin/serve
scripts/start_llm.sh runtime
```

3) ملاحظات أمنية وعملياتية

- استمع على `127.0.0.1` في البيئات المحلية؛ لا تفتح الخدمة دون إعداد auth وreverse-proxy.
- عند الاستخدام على الخادم، أنشئ وحدة systemd لتشغيل الخدمة كمستخدم مقيد.
- تخصيص الموارد (memory/cpu/gpu) يعتمد على runtime المستخدم.

أمثلة `systemd` موجودة داخل `docs/` عند الطلب.
