"""
mithaly.core.planning
طبقة التخطيط (layer): التخطيط المعرفي، التخطيط التكيفي، ومحاكاة التنفيذ.
واجهات مقترحة:
- `KnowledgePlanner`, `AdaptivePlanner`, `Simulator`.

ملاحظة: المصطلح الرسمي عبر المشروع هو "طبقة" (layer).
"""

__all__ = [
    "KnowledgePlanner",
    "AdaptivePlanner",
    "Simulator",
]

try:
    from .execution_planner import ExecutionPlanner  # noqa: F401
except Exception:
    ExecutionPlanner = None
