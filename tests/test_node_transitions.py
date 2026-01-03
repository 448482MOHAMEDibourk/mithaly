import json
import os
import sys
import types
from pathlib import Path

# Provide lightweight mocks for langgraph and langchain_core to allow importing engine
sys.modules.setdefault('langgraph.graph', types.SimpleNamespace(StateGraph=lambda *a, **k: None, START='START', END='END'))
sys.modules.setdefault('langgraph.checkpoint.memory', types.SimpleNamespace(MemorySaver=lambda *a, **k: None))
sys.modules.setdefault('langchain_core.runnables', types.SimpleNamespace(RunnableConfig=dict))

from mithaly.core.engine import node_gaps, node_planning, node_execution, node_feedback


def clear_transitions():
    p = Path('docs') / 'context' / 'transitions.jsonl'
    if p.exists():
        p.unlink()


def read_transitions():
    p = Path('docs') / 'context' / 'transitions.jsonl'
    if not p.exists():
        return []
    with open(p, 'r', encoding='utf-8') as f:
        return [json.loads(l) for l in f]


def test_nodes_emit_transitions(tmp_path):
    os.makedirs('docs/context', exist_ok=True)
    clear_transitions()

    # Call nodes with minimal state/config
    g_out = node_gaps({'text': 'test input'}, {})
    p_out = node_planning({'gap_analysis': g_out.get('gap_analysis', {}), 'plan_retries': 0}, {})

    # Execution: ensure probe_results present for SafeExecutor
    exec_state = {'plan': p_out.get('plan', ['step1']), 'probe_results': {'summary': 'ok'}, 'non_interactive': True}
    e_out = node_execution(exec_state, {})

    f_out = node_feedback({'execution_results': e_out.get('execution_results'), 'simulation_result': p_out.get('simulation_result', {})})

    recs = read_transitions()
    from_layers = [r.get('from_layer') for r in recs]

    assert any(fl and fl.lower() == 'gaps' for fl in from_layers), 'Gaps transition missing'
    assert any(fl and fl.lower() == 'planning' for fl in from_layers), 'Planning transition missing'
    assert any(fl and fl.lower() == 'execution' for fl in from_layers), 'Execution transition missing'
    assert any(fl and fl.lower() == 'feedback' for fl in from_layers), 'Feedback transition missing'
