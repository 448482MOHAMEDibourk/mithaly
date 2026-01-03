"""
mithaly.core.feedback
طبقة التغذية الراجعة (layer): تسجيل النتائج، تحديث المعرفة، والنسخ الاحتياطي الذكي.
واجهات مقترحة:
- `FeedbackManager`

تأكيد: 'طبقة' هو المصطلح المعتمد لوصف التقسيم المعماري.
"""

__all__ = [
    "FeedbackManager",
]

try:
    from .feedback_loop import FeedbackLoop  # noqa: F401
except Exception:
    FeedbackLoop = None
