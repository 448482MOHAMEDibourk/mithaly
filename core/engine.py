"""Thin runner: delegate to package engine in `src/mithaly/core`.

Per project policy, the canonical engine implementation lives inside the
package (`src/mithaly/core/engine.py`). This root-level file is a thin
runner that imports that implementation and invokes it. Keep the runner
small so it acts only as an entrypoint for CLI/tools.
"""
from importlib import import_module


def main():
    try:
        pkg_engine = import_module('mithaly.core.engine')
        BuildEngine = getattr(pkg_engine, 'BuildEngine')
    except Exception:
        # Fallback: try direct src import path
        try:
            pkg_engine = import_module('src.mithaly.core.engine')
            BuildEngine = getattr(pkg_engine, 'BuildEngine')
        except Exception as e:
            raise RuntimeError('Could not import package engine: ' + str(e))

    engine = BuildEngine(plan={}, project_path='.')
    engine.run_lifecycle({'text': 'اختبار دورة Mithaly'})


if __name__ == '__main__':
    main()

