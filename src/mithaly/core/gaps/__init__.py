"""
mithaly.core.gaps
طبقة الفجوات (layer): استكشاف، تحليل السبب الجذري، وترتيب الأولويات.
تحتوي هذه الطبقة على واجهات وملفات تنفيذية لـ:
- `GapAnalyzer`: اكتشاف الفجوات، تحليل الأسباب الجذرية، وترتيب الأولويات.

ملاحظة: نستخدم مصطلح "طبقات (layers)" عبر المشروع لوصف التقسيم المعماري.
"""

__all__ = [
    "GapAnalyzer",
]

try:
    from .gap_analyzer import GapAnalyzer  # noqa: F401
except Exception:
    GapAnalyzer = None
