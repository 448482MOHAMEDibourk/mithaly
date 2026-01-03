#!/usr/bin/env python3
"""Admin utility to list and mark analysis tickets as trusted.

Usage:
  PYTHONPATH=src python scripts/trust_ticket.py --list
  PYTHONPATH=src python scripts/trust_ticket.py --trust err-1234567890

When a ticket is trusted, this script will set `trusted: True` on the ticket
in `docs/context/analysis_tickets.json` and attempt to persist it via
`FeedbackLoop.persist_to_kb()`.
"""
import json
from pathlib import Path
import argparse

TICKETS = Path("docs/context/analysis_tickets.json")


def _load_tickets():
    if not TICKETS.exists():
        return []
    try:
        with open(TICKETS, "r", encoding="utf-8") as f:
            return json.load(f) or []
    except Exception:
        return []


def _save_tickets(tickets):
    TICKETS.parent.mkdir(parents=True, exist_ok=True)
    with open(TICKETS, "w", encoding="utf-8") as f:
        json.dump(tickets, f, ensure_ascii=False, indent=2)


def list_tickets():
    tickets = _load_tickets()
    if not tickets:
        print("No analysis tickets found in docs/context/analysis_tickets.json")
        return
    for t in tickets:
        tid = t.get("ticket_id")
        rec = t.get("recommendation")
        trusted = t.get("trusted", False)
        ts = t.get("timestamp")
        print(f"{tid}  | trusted={trusted} | rec={rec} | ts={ts}")


def trust_ticket(ticket_id: str):
    tickets = _load_tickets()
    found = False
    for t in tickets:
        if t.get("ticket_id") == ticket_id:
            found = True
            if t.get("trusted"):
                print(f"Ticket {ticket_id} is already trusted.")
            else:
                t["trusted"] = True
                _save_tickets(tickets)
                print(f"Ticket {ticket_id} marked trusted. Attempting to persist to KB...")
                # Attempt to persist via FeedbackLoop
                try:
                    from mithaly.core.feedback.feedback_loop import FeedbackLoop as _FL
                except Exception:
                    try:
                        from src.mithaly.core.feedback.feedback_loop import FeedbackLoop as _FL
                    except Exception:
                        _FL = None
                if _FL is None:
                    print("FeedbackLoop not available in this environment. Ticket trusted but not delivered.")
                    return
                fl = _FL()
                ok = False
                try:
                    ok = bool(fl.persist_to_kb(t))
                except Exception as e:
                    print("persist_to_kb raised:", e)
                    ok = False
                if ok:
                    print("Persisted ticket to KB via FeedbackLoop.")
                else:
                    print("FeedbackLoop rejected the record (not persisted).")
    if not found:
        print(f"Ticket {ticket_id} not found.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--list", action="store_true", help="List analysis tickets")
    p.add_argument("--trust", help="Mark a ticket trusted and attempt persistence")
    args = p.parse_args()
    if args.list:
        list_tickets()
    elif args.trust:
        trust_ticket(args.trust)
    else:
        p.print_help()
