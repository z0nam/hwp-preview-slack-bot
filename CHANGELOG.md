# Changelog

This project follows **CalVer**: `YYYY.0M.0D.N` where `N` increments
for multiple releases on the same date.

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
