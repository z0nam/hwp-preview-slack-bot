# hwp-preview-slack-bot

Slack 채널에 올라온 한컴오피스 파일(`.hwp` / `.hwpx`)을 자동으로 **PDF**로 변환해 같은 스레드에 회신하는 봇. 원본 hwp는 그대로 유지됨.

한컴오피스가 설치돼 있지 않은 멤버도 채널에서 바로 내용을 확인할 수 있게 하는 게 목적. 변환은 [**rhwp**](https://github.com/edwardkim/rhwp) — 자체 HWP/HWPX 렌더 엔진을 가진 단일 바이너리 — 로 수행한다. **Java도 LibreOffice도 불필요**하고, 바이너리 `.hwp`(HWP5)와 `.hwpx`를 macOS/Linux에서 네이티브로 렌더한다.

## 설치

### rhwp 바이너리 받기 (1회)

```bash
# 플랫폼 감지 → 릴리스 바이너리 다운로드 + 체크섬 검증 → vendor/rhwp/ 에 설치
./scripts/fetch_rhwp.sh
```

(GitHub CLI `gh` 필요.)

변환 단독 검증:

```bash
./scripts/hwp2pdf.sh samples/sample-binary.hwp
./scripts/hwp2pdf.sh samples/sample-xml.hwpx
```

macOS는 시스템 폰트로 한글 렌더가 된다. 최소 구성 리눅스 서버라면 한글 폰트(예: `fonts-nanum`)를 설치하거나 `RHWP_FONT_PATH=/폰트/경로 ./scripts/hwp2pdf.sh …` 로 폰트 디렉토리를 지정한다.

### Slack 앱 셋업 (1회)

[api.slack.com/apps](https://api.slack.com/apps) → Create New App (From scratch) → Workspace 선택. 이후:

- **Socket Mode** ON → App-Level Token (`xapp-…`, scope `connections:write`) 발급
- **OAuth & Permissions** → Bot Token Scopes: `files:read`, `files:write`,
  `chat:write`, `channels:history`, `groups:history`, `im:history`, `mpim:history`
  (뒤의 두 개는 봇과의 DM/그룹 DM에서도 hwp 자동 변환이 되게 해주는 스코프. 채널에서만 쓸 거면 빼도 무방.)
  `scripts/join_all_public.py` 로 공개 채널 전체에 일괄 join 시키려면 `channels:read` + `channels:join` 추가 필요.
- **Event Subscriptions** → Enable → Subscribe to bot events → `file_shared`
  (원본 삭제 시 미리보기 답글도 같이 지우려면 `message.channels`,
  `message.groups`, `message.im`, `message.mpim` 도 추가 — 위 `*:history`
  스코프를 재사용하므로 새 스코프는 불필요, 저장 후 Slack이 요구하면 재설치.)
- **App Home → Messages Tab** → 토글 ON + "Allow users to send Slash commands and messages from the messages tab" 체크.
  이거 안 켜면 DM 입력창이 비활성화되고 "이 앱으로 메시지를 보내는 기능이 꺼져 있습니다" 표시됨. 위 스코프만으론 부족.
  채널에서만 쓸 거면 생략 가능.
- **Install to Workspace** → Bot Token (`xoxb-…`) 발급
- **Basic Information → Display Information**: App icon은 `assets/icon.png` 사용

## 실행

```bash
cp .env.example .env  # 토큰 채우기
uv sync
./scripts/run_bot.sh
```

봇이 머무는(초대된) 채널에 누가 hwp를 올리면 1~2초 후 PDF가 같은 스레드에 회신됨.

## 항시 실행 (launchd, macOS)

`~/Library/LaunchAgents/com.namun.hwp-preview-bot.plist` 로 사용자 LaunchAgent 등록.
재부팅·로그인 시 자동 시작, 크래시 시 자동 재시작.

```bash
launchctl load -w ~/Library/LaunchAgents/com.namun.hwp-preview-bot.plist

# 상태 / 로그
launchctl list | grep hwp-preview
tail -f ~/Library/Logs/hwp-preview-bot.err   # python logging 은 stderr 로 감

# 재시작 / 중지
launchctl kickstart -k gui/$(id -u)/com.namun.hwp-preview-bot
launchctl unload ~/Library/LaunchAgents/com.namun.hwp-preview-bot.plist
```

전제: 호스트 맥이 자동 로그인 + 잠자기 꺼져있을 것 (LaunchAgent는 GUI 세션에 의존).

리눅스로 옮기려면 launchd plist 폐기 → 동일 `scripts/run_bot.sh` 를 가리키는 systemd unit 작성. `scripts/fetch_rhwp.sh` 한 번 + 한글 폰트만 있으면 변환 백엔드는 동일하게 동작함.

## 디렉토리

```
src/hwp_preview_slack_bot/__main__.py  봇 본체 (Socket Mode, slack-bolt)
scripts/hwp2pdf.sh                     HWP/HWPX → PDF (rhwp)
scripts/fetch_rhwp.sh                  rhwp 바이너리 다운로드 + 체크섬 검증
scripts/run_bot.sh                     봇 런처
scripts/make_icon.py                   Slack 앱 아이콘 생성기 (Pillow)
assets/icon.png                        Slack 앱 등록용 아이콘 (1024×1024)
samples/                               변환 검증용 (PDF는 .gitignore)
vendor/rhwp/                           받아온 rhwp 바이너리 (gitignore)
context.md                             내부 컨텍스트 (AI/신규합류자용)
docs/rhwp-migration.md                 LibreOffice → rhwp 전환 배경
```

## 충실도 정책

PDF 변환은 "대충 읽히면 OK" 수준의 미리보기. 페이지네이션·줄간격은 한컴 렌더와 다를 수 있고, 호스트에 없는 폰트는 치환된다. 원본 hwp는 슬랙 첨부로 그대로 남아있으므로 회신본은 보조 자료다.

## 라이선스 / 출처 메모

- 변환 엔진 [**rhwp**](https://github.com/edwardkim/rhwp) (Edward Kim, MIT) — 레포에 커밋하지 않고 설치 시 `scripts/fetch_rhwp.sh` 로 받음(핀 버전 + 체크섬 검증).
- `samples/` — 제주도청 정책기획관실 자문단 운영 문서 (정부 양식, 변환 충실도 검증용)

## 감사

- [**rhwp**](https://github.com/edwardkim/rhwp) — HWP/HWPX 렌더의 실질. 이거 없으면 이 봇은 성립 안 함.
- 이전 엔진이었던 [**H2Orestart**](https://github.com/ebandal/H2Orestart) (Bandal) — 초기 릴리스를 떠받쳐줬다.
- 초기 구현 / OSS 화 / 운영 셋업은 [**Claude Code**](https://claude.ai/code) (Anthropic) 과 페어로 작업.
