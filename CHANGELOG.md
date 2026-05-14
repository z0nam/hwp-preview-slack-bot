# Changelog

This project follows **CalVer**: `YYYY.0M.0D.N` where `N` increments
for multiple releases on the same date.

## 2026.05.14.3 — 2026-05-14

- **Fix**: silent conversion failure when two HWPs were uploaded close
  together in the same channel. slack-bolt's thread pool was firing two
  `file_shared` handlers in parallel; the two `soffice --headless`
  invocations contended on LibreOffice's shared user profile and one PDF
  would not be written (process exited 0, no output). Conversion is now
  serialized inside the bot with a `threading.Lock`.
- Recommend two additional bot scopes (`im:history`, `mpim:history`) so
  the bot also responds to HWPs uploaded in DMs and group DMs with it.
  Required only if you want that behavior; pure channel usage is
  unchanged. Adding the scopes requires reinstalling the app to the
  workspace.

## 2026.05.14.2 — 2026-05-14

First public release.

- Open-sourced under Apache License 2.0.
- Generalized for use outside the original organization:
  - English `README.md` (Korean preserved as `README.ko.md`).
  - `pyproject.toml` description, authors, classifiers, project URLs.
  - launchd plist moved out of the operator's home directory and into
    `examples/launchd.template.plist` with `__USER__` / `__PROJECT_PATH__`
    placeholders.
- Added `LICENSE`, `NOTICE` (third-party attribution), `CONTRIBUTING.md`,
  `SECURITY.md`, `CHANGELOG.md`.

## 2026.05.14.1 — 2026-05-14

Initial standalone release after extraction from the internal
`ji-slack-admin` working folder.

- Python package renamed from `ji_slack_admin` to `hwp_pdf_slack_bot`.
- Entry point moved to `__main__.py`; invocation is now
  `python -m hwp_pdf_slack_bot`.
- Bot verified operational against a real Slack workspace and put under
  macOS launchd keep-alive.
- Conversion backend (LibreOffice + H2Orestart) validated against two
  real-world government-formatting samples in `samples/`.
