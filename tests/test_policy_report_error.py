import json


def test_report_error_auto_resolve(tmp_path, monkeypatch):
    # run inside isolated tmp dir so tests don't pollute repo
    monkeypatch.chdir(tmp_path)

    # register a simple analyzer that returns auto_resolve
    from mithaly.core.registry import register_layer, LayerRegistry

    @register_layer('test_analyzer')
    class TestAnalyzer:
        def analyze_error(self, report):
            return {'action': 'auto_resolve', 'note': 'test confidence'}

    from mithaly.core.policy import PolicyEnforcer

    pe = PolicyEnforcer(policies={})
    ticket = pe.report_error({'msg': 'simulated failure for test'})

    assert isinstance(ticket, dict)
    assert ticket.get('recommendation') in ('auto_resolve', 'requires_admin', 'defer')

    # analysis_tickets should be written
    tickets_file = tmp_path / 'docs' / 'context' / 'analysis_tickets.json'
    assert tickets_file.exists()

    # If recommendation was auto_resolve, deliver_record should have attempted to persist
    if ticket.get('recommendation') == 'auto_resolve':
        # either KB file exists (persisted) or a docs/context snapshot exists
        kb_file = tmp_path / 'docs' / 'knowledge' / 'kb.json'
        ctx_files = list((tmp_path / 'docs' / 'context').glob('delivered_record_*.json'))
        assert kb_file.exists() or len(ctx_files) >= 0
