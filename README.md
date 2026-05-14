# hwp-pdf-slack-bot

> 한국어 안내: [README.ko.md](README.ko.md)

A Slack bot that auto-converts uploaded **HWP / HWPX** files (the
Korean Hancom Office formats) into PDF previews and posts them back
into the same thread, so teammates without Hancom Office installed
can read the document right in Slack. The original `.hwp` upload is
left untouched.

Conversion runs entirely on a headless **LibreOffice + [H2Orestart](https://github.com/ebandal/H2Orestart)**
stack, so the bot is happy on macOS or Linux without any Windows /
Hancom dependency.

## Features

- Listens for Slack `file_shared` events; processes only `.hwp` / `.hwpx`.
- Replies in the same channel & thread with the generated PDF.
- Runs as a long-lived Socket Mode bot — no public HTTPS endpoint needed.
- Self-contained: a single Python module + a shell script wrapping `soffice`.
- macOS launchd template included for keep-alive operation.

## Requirements

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) for dependency management
- LibreOffice (CLI: `soffice`)
- OpenJDK 21 (required by H2Orestart at conversion time)
- The bundled H2Orestart extension at `vendor/H2Orestart-v0.7.12.oxt`
- A Slack workspace where you can install a custom app (Pro plan or higher
  for Socket Mode; works on any non-free plan)

## Install (macOS arm64 example)

```bash
brew install --cask libreoffice
brew install openjdk@21
sudo ln -sfn /opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk \
  /Library/Java/JavaVirtualMachines/openjdk-21.jdk
xattr -dr com.apple.quarantine /Applications/LibreOffice.app

# Initialize LibreOffice's user profile so the Java config file gets created
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --terminate_after_init

# Then flip "enabled" to true in:
#   ~/Library/Application Support/LibreOffice/4/user/config/javasettings_MacOSX_AARCH64.xml
# (change <enabled xsi:nil="true"/> to <enabled xsi:nil="false">true</enabled>)
# LibreOffice auto-detects the JDK; only this enabled flag needs the flip.

# Register the H2Orestart extension
unopkg add ./vendor/H2Orestart-v0.7.12.oxt
# A "NoConnectException pipe" error is benign — the extension still registers.
```

Linux is structurally the same: install LibreOffice + OpenJDK from your
package manager, then `unopkg add ./vendor/H2Orestart-v0.7.12.oxt`. PRs
with a tested Linux setup walkthrough welcome.

Sanity-check the conversion pipeline by itself:

```bash
./scripts/hwp2pdf.sh samples/sample-binary.hwp
./scripts/hwp2pdf.sh samples/sample-xml.hwpx
```

## Slack app setup (one-off)

At [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → From scratch →
choose your workspace. Then:

- **Socket Mode** — enable, generate an App-Level Token with `connections:write`
  (this is your `xapp-…` token).
- **OAuth & Permissions → Bot Token Scopes**: `files:read`, `files:write`,
  `chat:write`, `channels:history`, `groups:history`, `im:history`, `mpim:history`.
  (`im:history` / `mpim:history` are what let the bot also respond to HWPs
  uploaded in direct messages and group DMs with it; drop them if you only
  want channel use.)
- **Event Subscriptions** — enable; under **Subscribe to bot events** add
  `file_shared`.
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
Upload a `.hwp` or `.hwpx` — a PDF reply lands in the same thread within
seconds to a few tens of seconds depending on document size.

## Keep-alive on macOS (launchd)

A template plist lives at [`examples/launchd.template.plist`](examples/launchd.template.plist).
Copy it to `~/Library/LaunchAgents/`, substitute the `__…__` placeholders for
your username and project path, then:

```bash
launchctl load -w ~/Library/LaunchAgents/com.<you>.hwp-pdf-bot.plist

# operations
launchctl list | grep hwp-pdf
tail -f ~/Library/Logs/hwp-pdf-bot.err     # python logging goes to stderr
launchctl kickstart -k gui/$(id -u)/com.<you>.hwp-pdf-bot
launchctl unload     ~/Library/LaunchAgents/com.<you>.hwp-pdf-bot.plist
```

Assumptions: the host Mac is set to auto-login and to not sleep — LaunchAgents
run inside a GUI user session.

For Linux deployments, write a systemd unit pointing at the same
`scripts/run_bot.sh`; the conversion stack behaves identically.

## Repository layout

```
src/hwp_pdf_slack_bot/__main__.py     Bot entry point (Socket Mode)
scripts/hwp2pdf.sh                    HWP/HWPX → PDF via headless soffice
scripts/run_bot.sh                    Convenience launcher
scripts/make_icon.py                  Regenerates assets/icon.png (Pillow)
assets/icon.png                       Slack app icon, 1024×1024
samples/                              Conversion-fidelity test inputs
vendor/H2Orestart-*.oxt               LibreOffice import-filter extension
examples/launchd.template.plist       macOS keep-alive template
context.md                            Project / decision notes (Korean)
```

## Fidelity policy

The PDF is intended as a "good-enough-to-read" preview, not a substitute
for the source document. Some font / table-alignment quirks are expected
on heavily-formatted government templates. The original HWP stays attached
to the Slack message, so anyone who needs pixel-faithful rendering can
still download it. Only a complete conversion failure justifies swapping
out the backend.

## Versioning

This project uses **CalVer** (`YYYY.0M.0D.N`). Release `2026.05.14.2`
is the first public release; see [CHANGELOG.md](CHANGELOG.md).

## License & attribution

Licensed under **Apache License 2.0** — see [LICENSE](LICENSE).

The bundled `vendor/H2Orestart-v0.7.12.oxt` is the upstream **H2Orestart**
LibreOffice extension by Bandal, distributed under **LGPL-2.1-or-later**.
You may replace it with any other build of H2Orestart at any time.
Full third-party attribution is in [NOTICE](NOTICE).

## Contributing & security

- General contributions: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security issues: [SECURITY.md](SECURITY.md)

## Acknowledgments

- [**H2Orestart**](https://github.com/ebandal/H2Orestart) by Bandal — the LibreOffice
  extension that does the actual HWP/HWPX import work. This bot would not be
  possible without it.
- The initial implementation, OSS-ification, and operational hardening of this
  bot were paired with [**Claude Code**](https://claude.ai/code) by Anthropic.
