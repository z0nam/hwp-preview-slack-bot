# Contributing

Thanks for thinking about contributing. This project is small and focused —
HWP/HWPX previews in Slack — and PRs that keep it that way are most welcome.

## Setting up a dev environment

```bash
git clone git@github.com:z0nam/hwp-preview-slack-bot.git
cd hwp-preview-slack-bot

# system deps (macOS arm64 example — see README for full setup)
brew install --cask libreoffice
brew install openjdk@21
unopkg add ./vendor/H2Orestart-v0.7.12.oxt

# python deps
uv sync
```

Run the conversion script standalone to confirm the LibreOffice +
H2Orestart toolchain works on your machine:

```bash
./scripts/hwp2x.sh pdf  samples/sample-binary.hwp /tmp/
./scripts/hwp2x.sh docx samples/sample-binary.hwp /tmp/
```

To run the bot itself you need a Slack workspace and two tokens — see
the README's "Slack app setup" and "Configure and run" sections.

## What we welcome

- Bug fixes (conversion edge cases, Slack event handling).
- Linux setup walkthroughs verified end-to-end.
- A `Dockerfile` / `docker-compose.yml` that bundles LibreOffice + JDK +
  H2Orestart and runs the bot.
- Tests for `scripts/hwp2x.sh` and the event handler in
  `src/hwp_preview_slack_bot/__main__.py`.
- Better fidelity: tuning `soffice` flags, alternative HWP backends,
  font handling improvements.
- Operational extras: metrics, structured logging, channel topic-based
  opt-in / opt-out.

## What we'd rather not add (without strong reason)

- New triggers beyond `file_shared` for HWP/HWPX inputs — keep the bot scope small.
- Heavy web-app surface (dashboards, admin UI). Bot stays Socket Mode.
- Input formats outside the HWP family. The bot is specifically a
  HWP/HWPX → preview tool; if you need Word / Excel / etc. previews,
  Slack already renders most of them natively or it's worth its own project.

## Workflow

1. Open an issue first for anything non-trivial so we can sanity-check
   direction before you spend time.
2. One logical change per PR — easier to review and revert.
3. Keep commit messages focused on the *why* of the change.
4. Run the bot end-to-end against a real Slack workspace before
   requesting review on anything that touches event handling or token
   plumbing.

## Style

- Python: keep it boring and standard library where reasonable. The bot
  is intentionally a single small module.
- Shell scripts: `set -euo pipefail`, `shellcheck`-clean.
- Error messages and Slack `chat.postMessage` text may be Korean —
  the bot's primary audience speaks Korean.

## Code of conduct

Be excellent to each other. Toxicity, harassment, or aggressive bad-faith
behavior won't be tolerated. Substantive technical disagreement is fine
and welcome.
