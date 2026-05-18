# Security policy

## Reporting a vulnerability

If you find a security issue in this project, **please do not open a
public GitHub issue**. Instead:

1. Open a [private security advisory](https://github.com/z0nam/hwp-preview-slack-bot/security/advisories/new)
   on this repository, or
2. Email the maintainer directly (see the GitHub profile at
   [@z0nam](https://github.com/z0nam) for current contact info).

Please include:

- A short description of the issue.
- Steps to reproduce, or a minimal proof of concept.
- Your assessment of impact (data exposure, RCE, DoS, etc.).
- Any suggested mitigation.

You will get a first acknowledgement within a few business days. We
aim to confirm and (where applicable) ship a fix within two weeks for
high-severity issues; lower-severity issues may be batched.

## Scope

In scope:

- The bot code in `src/hwp_preview_slack_bot/`.
- The shell conversion wrapper `scripts/hwp2x.sh`.
- The launchd template in `examples/`.

Out of scope (please report upstream instead):

- LibreOffice / `soffice` bugs.
- H2Orestart bugs — file at [ebandal/H2Orestart](https://github.com/ebandal/H2Orestart).
- Slack platform bugs.
- Issues that require local code execution as the bot operator
  (e.g. "the operator could put a malicious script in `vendor/`").

## Operator hardening reminders

The bot inherently:

- Holds long-lived Slack tokens (`xoxb-…`, `xapp-…`) — keep `.env` off
  shared filesystems and out of version control.
- Downloads arbitrary files posted to channels it is in. Conversion runs
  in a fresh temporary directory and the only thing returned to Slack is
  the resulting PDF, but you are still feeding user content into
  LibreOffice. Keep your LibreOffice + H2Orestart up to date.
- Inherits the operator's filesystem permissions. Run the bot under a
  dedicated user account if you are nervous about this.
