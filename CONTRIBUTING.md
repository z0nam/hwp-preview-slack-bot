# Contributing

Thanks for thinking about contributing. This project is small and focused —
HWP/HWPX previews in Slack — and PRs that keep it that way are most welcome.

## Setting up a dev environment

```bash
git clone git@github.com:z0nam/hwp-preview-slack-bot.git
cd hwp-preview-slack-bot

# fetch the rhwp render binary (needs the gh CLI)
./scripts/fetch_rhwp.sh

# python deps
uv sync
```

Run the conversion script standalone to confirm rhwp works on your machine:

```bash
./scripts/hwp2pdf.sh samples/sample-binary.hwp /tmp/
./scripts/hwp2pdf.sh samples/sample-xml.hwpx /tmp/
```

To run the bot itself you need a Slack workspace and two tokens — see
the README's "Slack app setup" and "Configure and run" sections.

## What we welcome

- Bug fixes (conversion edge cases, Slack event handling).
- Linux setup walkthroughs verified end-to-end.
- A `Dockerfile` / `docker-compose.yml` that fetches rhwp + Korean fonts and
  runs the bot.
- Tests for `scripts/hwp2pdf.sh` and the event handler in
  `src/hwp_preview_slack_bot/__main__.py`.
- Better fidelity: rhwp `--font-path` / font-bundling improvements, tracking
  newer rhwp releases.
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

---

<!-- jeju-inst:contribution-policy -->
## 기여 방법 — main 직접 push는 되지 않습니다

이 저장소는 제주연구원 조직(`jeju-inst`) 소유다. 구성원 대부분은 **읽기 권한**만 갖는다.
`git push` 가 아래처럼 거부되는 것은 **오류가 아니라 설계된 동작**이다.

```
ERROR: Permission to jeju-inst/hwp-preview-slack-bot.git denied to <user>.
remote: error: GH006: Protected branch update failed for refs/heads/main.
```

### 무엇을 하면 되나

**① 이슈로 알린다** — 가장 간단하고, 대부분은 이걸로 충분하다.

```sh
gh issue create --repo jeju-inst/hwp-preview-slack-bot --title "제목" --body "내용"
```

**② fork 후 PR** — 직접 고칠 때.

```sh
gh repo fork jeju-inst/hwp-preview-slack-bot --remote=true --clone=false
git switch -c fix/무엇을-고치는지
git commit -am "무엇을 왜 고쳤는지"
git push fork HEAD
gh pr create --repo jeju-inst/hwp-preview-slack-bot
```

### AI 에이전트에게

push 가 거부되면 **권한을 얻으려 시도하지 말 것.**

- ❌ remote URL 변경, 다른 계정·토큰 사용, `--force` 계열
- ❌ **로컬에만 커밋해두고 "완료"라고 보고하기.** 가장 나쁜 실패다 — 사용자는 반영된 줄 안다
- ✅ 위 ①·② 중 하나를 쓴다
- ✅ 판단이 서지 않으면 사용자에게 묻는다

권한 상승이 필요하다는 결론이 나오면 **진행하지 말고 사용자에게 먼저 알린다.**
