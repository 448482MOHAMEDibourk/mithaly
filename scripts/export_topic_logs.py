"""Export Topic Logs - Generate readable views from the Knowledge Ledger."""
import json
import argparse
import os
from datetime import datetime

LEDGER_PATH = "docs/context/knowledge.jsonl"
EXPORT_DIR = "docs/context/exports"

def export_logs(target_topic: str = None):
    if not os.path.exists(LEDGER_PATH):
        print(f"No ledger found at {LEDGER_PATH}")
        return

    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    entries = []
    print(f"Reading ledger...")
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                entries.append(data)
            except:
                continue

    filtered = []
    for e in entries:
        if not target_topic:
            filtered.append(e)
            continue
            
        # Check topics list
        if target_topic.lower() in [t.lower() for t in e.get('topics', [])]:
            filtered.append(e)
            continue
            
        # Also check content? No, strictly topics for now.

    # Sort by timestamp descending
    filtered.sort(key=lambda x: x['ts'], reverse=True)

    filename = f"topic_{target_topic}.md" if target_topic else "all_knowledge.md"
    out_path = os.path.join(EXPORT_DIR, filename)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"# Knowledge Log: {target_topic or 'ALL'}\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        
        for e in filtered:
            f.write(f"## {e.get('ts')} | ID: {e.get('id')[:8]}\n")
            f.write(f"**Topics**: {', '.join(e.get('topics', []))} | **Trusted**: {e.get('trusted')}\n\n")
            f.write(f"{e.get('content')}\n\n")
            f.write("---\n")

    print(f"Exported {len(filtered)} records to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, help="Topic to filter by")
    args = parser.parse_args()
    
    export_logs(args.topic)
