#!/usr/bin/env python3
"""Check repository for files that use protected base names.

Exits with code 1 if any offending files are found. Intended for use in CI/pre-commit.
"""
import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__) + "/..")
PROTECTED_BASES = {"MITHALY_SOURCE_OF_TRUTH"}

def main():
    hits = []
    for dirpath, dirs, files in os.walk(ROOT):
        # skip .git and virtual envs
        if ".git" in dirpath.split(os.sep):
            continue
        for name in files + dirs:
            base = os.path.splitext(name)[0]
            if base in PROTECTED_BASES:
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, ROOT)
                # ignore the sacred no-extension file under docs/architecture
                if rel == os.path.join('docs','architecture','MITHALY_SOURCE_OF_TRUTH'):
                    continue
                hits.append(rel)

    if hits:
        print("Protected filename usage detected:")
        for p in hits:
            print(" -", p)
        print("\nNo files should be created with base name(s): {}".format(
            ", ".join(sorted(PROTECTED_BASES))
        ))
        print("If this is an allowed archival file, rename it to include an approved suffix, or add an approval record in docs/approvals/.")
        sys.exit(1)

    print("No protected filenames found.")

if __name__ == '__main__':
    main()
