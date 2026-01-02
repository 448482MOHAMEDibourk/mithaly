#!/usr/bin/env python3
"""Find duplicate files by content hash under the workspace root.

Moved from tools/scripts; ROOT adjusted.
"""
import os
import sys
import hashlib
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # skip .git and virtual environments
        if '.git' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            yield os.path.join(dirpath, fn)


def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
    except Exception:
        return None
    return h.hexdigest()


def main():
    root = ROOT
    files_by_size = {}
    for p in iter_files(root):
        try:
            s = os.path.getsize(p)
        except Exception:
            continue
        files_by_size.setdefault(s, []).append(p)

    candidate_files = [p for size, files in files_by_size.items() if len(files) > 1 for p in files]

    hashes = {}
    for p in candidate_files:
        h = sha256_file(p)
        if not h:
            continue
        hashes.setdefault(h, []).append(p)

    dup_groups = [g for g in hashes.values() if len(g) > 1]

    report = {
        'root': root,
        'total_files_scanned': sum(len(v) for v in files_by_size.values()),
        'duplicate_groups': dup_groups,
        'duplicate_count': sum(len(g) for g in dup_groups),
    }

    if '--json' in sys.argv:
        print(json.dumps(report, indent=2))
        return

    print('Scanned root:', report['root'])
    print('Total files scanned:', report['total_files_scanned'])
    print('Duplicate groups found:', len(report['duplicate_groups']))
    print('Duplicate files total:', report['duplicate_count'])
    print('')
    for i, g in enumerate(report['duplicate_groups'], 1):
        print(f'Group {i} (count={len(g)}):')
        for fp in g:
            print('  -', fp)
        print('')

    print('To delete duplicates keep one per group, run with --json and then remove files manually or use the provided script with confirmation.')


if __name__ == '__main__':
    main()
