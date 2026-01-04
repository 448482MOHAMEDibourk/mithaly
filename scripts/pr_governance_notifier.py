#!/usr/bin/env python3
"""Post a governance failure comment to the PR when checks fail.

Behavior:
- Re-runs `scripts/check_protected_names.py` and `scripts/ci_validate_env_and_approvals.py`.
- If any check fails, composes a Markdown message summarizing failures and posts it to the
  pull request (when running inside a PR via GitHub Actions). Otherwise prints the summary.

This script uses `GITHUB_TOKEN` and `GITHUB_EVENT_PATH` when available.
"""
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

ROOT = os.path.abspath(os.path.dirname(__file__) + '/..')

CHECKS = [
    (os.path.join('scripts', 'check_protected_names.py'), 'Protected filename check'),
    (os.path.join('scripts', 'ci_validate_env_and_approvals.py'), 'Restricted env var approvals check'),
]

def run_check(path):
    cmd = [sys.executable, path]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        return p.returncode, p.stdout + p.stderr
    except Exception as e:
        return 2, f'Exception running {path}: {e}'

def compose_comment(results):
    lines = []
    lines.append('## Governance checks — automated report')
    lines.append('The repository governance checks ran and found the following:')
    lines.append('')
    any_fail = False
    for name, (rc, out) in results.items():
        status = '✅ Passed' if rc == 0 else '❌ Failed'
        if rc != 0:
            any_fail = True
        lines.append(f'- **{name}**: {status}')
    lines.append('')
    if any_fail:
        lines.append('### Failure details')
        for name, (rc, out) in results.items():
            if rc != 0:
                lines.append(f'#### {name}')
                lines.append('```')
                # truncate long output
                excerpt = out.strip()
                if len(excerpt) > 8000:
                    excerpt = excerpt[:8000] + '\n... (truncated)'
                lines.append(excerpt)
                lines.append('```')
        lines.append('')
        lines.append('Please see [docs/approvals/README.md](docs/approvals/README.md) for how to add an approval, or rename offending files to avoid the `MITHALY_SOURCE_OF_TRUTH` basename.')
    else:
        lines.append('All checks passed — no action required.')

    return '\n'.join(lines), any_fail

def post_comment(repo, pr_number, token, body):
    url = f'https://api.github.com/repos/{repo}/issues/{pr_number}/comments'
    data = json.dumps({'body': body}).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'token {token}')
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode('utf-8')
            print('Posted comment to PR', pr_number)
            return True, resp_body
    except urllib.error.HTTPError as e:
        print('Failed to post comment:', e.code, e.read().decode('utf-8'))
        return False, None
    except Exception as e:
        print('Failed to post comment:', e)
        return False, None

def find_pr_number():
    evpath = os.environ.get('GITHUB_EVENT_PATH')
    if not evpath or not os.path.exists(evpath):
        return None
    try:
        with open(evpath, 'r') as f:
            ev = json.load(f)
        pr = ev.get('pull_request', {})
        return pr.get('number')
    except Exception:
        return None

def main():
    results = {}
    for path, title in CHECKS:
        rc, out = run_check(os.path.join(ROOT, path))
        results[title] = (rc, out)

    comment, any_fail = compose_comment(results)

    # If running in a PR inside GH Actions, post the comment
    pr_number = find_pr_number()
    repo = os.environ.get('GITHUB_REPOSITORY')
    token = os.environ.get('GITHUB_TOKEN')
    if any_fail and pr_number and repo and token:
        ok, resp = post_comment(repo, pr_number, token, comment)
        if not ok:
            print('Failed to post PR comment.')
            print(comment)
            sys.exit(1)
        else:
            print('Notifier completed.')
            return

    # Not in PR or no failures — print the message for CI log visibility
    print(comment)
    if any_fail:
        sys.exit(1)

if __name__ == '__main__':
    main()
