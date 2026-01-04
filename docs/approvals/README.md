# Approvals: Purpose and Process

This folder holds explicit human approvals required to enable sensitive agent features
or to make exceptions to the repository's Source-of-Truth protections.

Why approvals exist
- Prevent automation from silently altering the project's Source-of-Truth.
- Avoid "automation laziness" where reviewers rely on tools instead of human judgment.
- Ensure a human decision (with rationale and scope) exists before granting broad LLM powers.

What is enforced by CI
- Files whose base name equals `MITHALY_SOURCE_OF_TRUTH` are blocked by `scripts/check_protected_names.py`.
- Environment variables `ENABLE_CONTINUE_MITHALY_SOT` and `ENABLE_CURSORRULES` are blocked in CI unless
  a corresponding approval file exists in this folder.

How to approve
1. Create a file in `docs/approvals/` named `APPROVAL_<FEATURE>.md` (for example
   `APPROVAL_ENABLE_CURSORRULES.md`) or add a single `APPROVALS.md` that lists approvals.
2. Use the template `APPROVAL_TEMPLATE.md` as a starting point. At minimum include:
   - Requester, date, scope (which branches/PRs or env vars), rationale, approvers.
3. Commit the approval file on a branch and open a PR, or add it directly on a branch with
   explicit maintainer consent.

Suggested minimal contents
- **Requested by:** GitHub handle
- **Date:** YYYY-MM-DD
- **Scope:** `ENABLE_CURSORRULES` on branch `feature/secure-test` until YYYY-MM-DD
- **Rationale:** Short explanation of need and mitigations
- **Approvers:** list of maintainers who signed off

Auditing and expiry
- Prefer timeboxed approvals. Include an expiry date when possible.
- When an approval is no longer needed, remove or archive it and record the change in the PR.

CI behavior and developer experience
- When CI detects an enabled restricted env var without an approval file, the job will fail
  with instructions on how to add an approval file.
- When a protected filename is detected, CI fails and indicates which file(s) must be renamed
  or approved.

Questions or exceptions
- Contact repository maintainers or open an issue/PR to discuss exceptional cases.
