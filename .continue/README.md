Continue.dev custom context provider: Mithaly Source-of-Truth
=========================================================

This folder contains a minimal provider that can be used by Continue.dev to
inject the project's `MITHALY_SOURCE_OF_TRUTH` content into the agent's working
context. It is intentionally opt-in and safe-by-default.

How it works
------------
- The provider script is `.continue/providers/mithaly_sot.py` and exposes
  `provide_context()` which returns a dict with the key `mithaly_source_of_truth`.
- The provider only returns data when the environment variable
  `ENABLE_CONTINUE_MITHALY_SOT` is set to `1`.
- The path to the Source-of-Truth file is taken from environment variable
  `MITHALY_SOURCE_OF_TRUTH`.

Security & governance
---------------------
- Do not enable `ENABLE_CONTINUE_MITHALY_SOT` in CI unless you intend to
  inject the SoT into agent requests. Prefer enabling locally for reviewers.
- Avoid storing secrets in the SoT. The provider only reads the file as plain
  text and does not transmit secrets intentionally.

Example
-------
```bash
export MITHALY_SOURCE_OF_TRUTH=/path/to/docs/architecture/MITHALY_SOURCE_OF_TRUTH_CANONICAL.md
export ENABLE_CONTINUE_MITHALY_SOT=1
# when Continue.dev runs the provider it will include the SoT in context
```
