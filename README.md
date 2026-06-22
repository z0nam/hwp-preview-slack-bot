# hwp-preview-slack-bot

> 한국어 안내: [README.ko.md](README.ko.md)

A Slack bot that auto-converts uploaded **HWP / HWPX** files (the
Korean Hancom Office formats) into a **PDF** preview and posts it back
into the same thread, so teammates without Hancom Office installed can
read the document right in Slack. The original `.hwp` upload is left
untouched.

Conversion runs on [**rhwp**](https://github.com/edwardkim/rhwp), a single
self-contained binary with its own HWP/HWPX render engine — **no Java, no
LibreOffice, no Hancom dependency**. Binary `.hwp` (HWP5) and `.hwpx` are
both rendered natively, on macOS or Linux.

## Features

- Listens for Slack `file_shared` events; processes only `.hwp` / `.hwpx`.
- Replies in the same channel & thread with the generated PDF.
- Deletes its own preview reply when the original upload is deleted, so a
  non-admin uploader isn't left with an orphaned preview they can't remove.
- Runs as a long-lived Socket Mode bot — no public HTTPS endpoint needed.
- Self-contained: a single Python module + a shell script wrapping `rhwp`.
- macOS launchd template included for keep-alive operation.

## Requirements

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) for dependency management
- [GitHub CLI](https://cli.github.com/) (`gh`) to fetch the rhwp release binary
- A Slack workspace where you can install a custom app (Pro plan or higher
  for Socket Mode; works on any non-free plan)

No system conversion stack is needed — `scripts/fetch_rhwp.sh` downloads the
~10 MB rhwp binary (checksum-verified) into `vendor/rhwp/`.

## Install

```bash
# Fetch + verify the rhwp binary for this platform (macOS arm64/x86_64, Linux x86_64)
./scripts/fetch_rhwp.sh
```

Sanity-check the conversion pipeline by itself:

```bash
./scripts/hwp2pdf.sh samples/sample-binary.hwp
./scripts/hwp2pdf.sh samples/sample-xml.hwpx
```

On macOS the system fonts are enough to render Korean documents. On a minimal
Linux server, install Korean fonts (e.g. `fonts-nanum`) or point rhwp at a font
directory with `RHWP_FONT_PATH=/path/to/fonts ./scripts/hwp2pdf.sh …`.

## Slack app setup (one-off)

At [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → From scratch →
choose your workspace. Then:

- **Socket Mode** — enable, generate an App-Level Token with `connections:write`
  (this is your `xapp-…` token).
- **OAuth & Permissions → Bot Token Scopes**: `files:read`, `files:write`,
  `chat:write`, `channels:history`, `groups:history`, `im:history`, `mpim:history`.
  (`im:history` / `mpim:history` are what let the bot also respond to HWPs
  uploaded in direct messages and group DMs with it; drop them if you only
  want channel use.) Add `channels:read` + `channels:join` if you want to use
  `scripts/join_all_public.py` to bulk-join every public channel.
- **Event Subscriptions** — enable; under **Subscribe to bot events** add
  `file_shared`. For the delete-with-original behavior also add
  `message.channels`, `message.groups`, `message.im`, `message.mpim` (these
  reuse the `*:history` scopes above — no new scopes, but save and reinstall
  if Slack prompts). Without them the bot still posts previews; it just can't
  clean them up when the original is deleted.
- **App Home → Messages Tab** — turn the *Messages Tab* on, then tick
  *"Allow users to send Slash commands and messages from the messages tab"*.
  Without this the DM input is greyed out and users see "Sending messages
  to this app has been turned off", even with the scopes above. Skip this
  step if you only want channel use.
- **Install to Workspace** to mint your Bot Token (`xoxb-…`).
- **Basic Information → Display Information** — optionally upload
  `assets/icon.png` as the app icon.

## Configure and run

```bash
cp .env.example .env       # then fill in SLACK_BOT_TOKEN / SLACK_APP_TOKEN
uv sync
./scripts/run_bot.sh
```

Invite the bot to any channel where you want HWP previews (`/invite @<bot-name>`).
Upload a `.hwp` or `.hwpx` — a PDF reply lands in the same thread within a
second or two.

## Keep-alive on macOS (launchd)

A template plist lives at [`examples/launchd.template.plist`](examples/launchd.template.plist).
Copy it to `~/Library/LaunchAgents/`, substitute the `__…__` placeholders for
your username and project path, then:

```bash
launchctl load -w ~/Library/LaunchAgents/com.<you>.hwp-preview-bot.plist

# operations
launchctl list | grep hwp-preview
tail -f ~/Library/Logs/hwp-preview-bot.err   # python logging goes to stderr
launchctl kickstart -k gui/$(id -u)/com.<you>.hwp-preview-bot
launchctl unload     ~/Library/LaunchAgents/com.<you>.hwp-preview-bot.plist
```

Assumptions: the host Mac is set to auto-login and to not sleep — LaunchAgents
run inside a GUI user session.

For Linux deployments, write a systemd unit pointing at the same
`scripts/run_bot.sh`; the conversion stack behaves identically (run
`scripts/fetch_rhwp.sh` once to get the Linux binary).

## Repository layout

```
src/hwp_preview_slack_bot/__main__.py  Bot entry point (Socket Mode)
scripts/hwp2pdf.sh                     HWP/HWPX → PDF via rhwp
scripts/fetch_rhwp.sh                  Download + checksum-verify the rhwp binary
scripts/run_bot.sh                     Convenience launcher
scripts/make_icon.py                   Regenerates assets/icon.png (Pillow)
assets/icon.png                        Slack app icon, 1024×1024
samples/                               Conversion-fidelity test inputs
vendor/rhwp/                           Fetched rhwp binary (gitignored)
examples/launchd.template.plist        macOS keep-alive template
context.md                             Project / decision notes (Korean)
docs/rhwp-migration.md                 Why the engine moved from LibreOffice to rhwp
```

## Fidelity policy

The PDF output is intended as a "good-enough-to-read" preview, not a
pixel-faithful substitute for the source document. Pagination and line
spacing can differ from Hancom's own rendering, and fonts the host lacks
are substituted. The original HWP stays attached to the Slack message, so
anyone who needs faithful rendering can still download it.

## Versioning

This project uses **CalVer** (`YYYY.0M.0D.N`). Release `2026.05.14.2`
was the first public release (then under the name `hwp-pdf-slack-bot`);
see [CHANGELOG.md](CHANGELOG.md).

## License & attribution

Licensed under **Apache License 2.0** — see [LICENSE](LICENSE).

The conversion engine, [**rhwp**](https://github.com/edwardkim/rhwp) by
Edward Kim, is fetched at install time (not vendored in this repo) and is
distributed under the **MIT License**. Full third-party attribution is in
[NOTICE](NOTICE).

## Contributing & security

- General contributions: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security issues: [SECURITY.md](SECURITY.md)

## Acknowledgments

- [**rhwp**](https://github.com/edwardkim/rhwp) by Edward Kim — the Rust HWP/HWPX
  render engine that does the actual conversion work. This bot would not be
  possible without it.
- This bot previously ran on [**H2Orestart**](https://github.com/ebandal/H2Orestart)
  by Bandal (a LibreOffice import filter); thanks to that project for carrying
  the early releases.
- The initial implementation, OSS-ification, and operational hardening of this
  bot were paired with [**Claude Code**](https://claude.ai/code) by Anthropic.
