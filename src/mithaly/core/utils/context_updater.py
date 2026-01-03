import json
import os
from datetime import datetime, timezone
from pathlib import Path


class ContextUpdateRequiresConfirmation(Exception):
    pass


def _read_constitution(path: str = "docs/MITHALY_CONSTITUTION.md") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _is_phase_permitted(phase_name: str) -> bool:
    """Naive check: if the phase name appears in the constitution text,
    consider it permitted. This is intentionally conservative: absence means
    "requires confirmation".
    """
    text = _read_constitution()
    if not text:
        return False
    return phase_name in text


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def snapshot_context(phase_name: str, payload: dict, docs_dir: str = "docs/context") -> dict:
    """Write a snapshot of `payload` to `docs/context/current_context.json` and
    a timestamped snapshot file. Append an entry to `docs/context/history.md`.

    Behavior:
    - Always write non-destructive snapshots.
    - If the constitution does not explicitly permit the phase, the function
      returns `{'requires_confirmation': True}` and records that in the history.

    Returns a dict with keys `ok` or `requires_confirmation` and metadata.
    """
    base = Path(docs_dir)
    _ensure_dir(base)

    ts = datetime.now(timezone.utc).isoformat()
    current = {
        "phase": phase_name,
        "timestamp": ts,
        "payload": payload,
    }

    current_path = base / "current_context.json"
    snapshot_path = base / f"snapshot_{phase_name}_{ts.replace(':','-')}.json"

    # Write current context (overwrites safely)
    with open(current_path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    # Write a timestamped snapshot for audit/history
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    permitted = _is_phase_permitted(phase_name)

    history_path = base / "history.md"
    entry_lines = [
        f"- **{ts}** — Phase: **{phase_name}**",
        f"  - permitted: {str(permitted)}",
        f"  - snapshot: {snapshot_path.name}",
        "",
    ]
    with open(history_path, "a", encoding="utf-8") as h:
        h.write("\n".join(entry_lines) + "\n")

    if not permitted:
        return {"requires_confirmation": True, "snapshot": str(snapshot_path), "current": str(current_path)}

    return {"ok": True, "snapshot": str(snapshot_path), "current": str(current_path)}


def deliver_record(record: dict, prefer_feedback: bool = True) -> dict:
    """Attempt to deliver `record` permanently via `FeedbackLoop.persist_to_kb`.

    If `prefer_feedback` is True, try to import and call FeedbackLoop.persist_to_kb.
    On failure, fall back to writing the record as a snapshot under `docs/context`.

    Returns a dict describing the outcome: `{'delivered': bool, 'via': 'feedback'|'docs/context', ...}`
    """
    if prefer_feedback:
        try:
            try:
                from mithaly.core.feedback.feedback_loop import FeedbackLoop as _FL
            except Exception:
                from src.mithaly.core.feedback.feedback_loop import FeedbackLoop as _FL
            fl = _FL()
            ok = False
            try:
                ok = bool(fl.persist_to_kb(record))
            except Exception:
                ok = False
            if ok:
                return {'delivered': True, 'via': 'feedback'}
        except Exception:
            # feedback not available or failed — fall through to docs/context
            pass

    # fallback: write to docs/context as a timestamped snapshot
    base = Path("docs/context")
    _ensure_dir(base)
    ts = datetime.now(timezone.utc).isoformat()
    snapshot_path = base / f"delivered_record_{ts.replace(':','-')}.json"
    try:
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump({'timestamp': ts, 'record': record}, f, ensure_ascii=False, indent=2)
        return {'delivered': False, 'via': 'docs/context', 'snapshot': str(snapshot_path)}
    except Exception as e:
        return {'delivered': False, 'via': 'error', 'error': str(e)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Snapshot runtime context to docs/context")
    parser.add_argument("phase", help="Name of the engine phase (e.g. gaps, planning)")
    parser.add_argument("payload_file", nargs="?", help="Optional JSON file with payload to snapshot")
    args = parser.parse_args()

    payload = {}
    if args.payload_file:
        try:
            with open(args.payload_file, "r", encoding="utf-8") as pf:
                payload = json.load(pf)
        except Exception:
            payload = {"error": "failed to load payload file"}

    result = snapshot_context(args.phase, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
