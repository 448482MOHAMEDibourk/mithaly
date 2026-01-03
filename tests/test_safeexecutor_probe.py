import pytest

from mithaly.core.execution.safe_executor import SafeExecutor


def test_safeexecutor_requires_probe_results():
    se = SafeExecutor()
    # missing probe_results and non_interactive False should raise
    with pytest.raises(RuntimeError):
        se.process({'text': 'do something', 'non_interactive': False})


def test_safeexecutor_allows_non_interactive_without_probe():
    se = SafeExecutor()
    # non_interactive True should not raise
    out = se.process({'text': 'do something', 'non_interactive': True})
    assert out.get('layer') == 'execution'
