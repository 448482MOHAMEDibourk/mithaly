"""
mithaly.core.execution
طبقة التنفيذ الآمن (layer): تنفيذ آمن مع رصد، تراجع، ووقف طارئ.
واجهة مقترحة:
- `SafeExecutor`

نستخدم مصطلح "طبقة" بشكل موحّد عبر الكود والوثائق.
"""

__all__ = [
    "SafeExecutor",
]

try:
    from .safe_executor import SafeExecutor  # noqa: F401
except Exception:
    SafeExecutor = None
