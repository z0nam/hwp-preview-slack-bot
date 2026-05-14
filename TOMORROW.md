# 내일(2026-05-14) 출근하면 할 일

전제: 2026-05-13 밤까지 변환 백엔드(LibreOffice + H2Orestart) + 봇 코드 스캐폴딩 완료. 남은 건 **Slack 앱 생성 + 토큰 발급 + 한 채널에서 동작 확인**.

소요시간 약 15~25분.

---

## 1. Slack 앱 생성 (10분)

브라우저: https://api.slack.com/apps

1. **Create New App** → **From scratch**
   - App Name: `HWP Preview` (예시)
   - Workspace: 제주연구원 워크스페이스 선택

2. 왼쪽 메뉴 **Socket Mode**
   - **Enable Socket Mode** 토글 ON
   - 팝업에서 App-Level Token 이름 입력 (예: `socket-token`), Scope `connections:write` 자동 선택
   - **Generate** → 표시되는 `xapp-…` 토큰 복사해 두기 ⚠️ 다시 못 봄

3. **OAuth & Permissions**
   - **Bot Token Scopes** 에 아래 추가:
     - `files:read` — hwp 다운로드용
     - `files:write` — pdf 업로드용
     - `chat:write` — 에러/안내 메시지
     - `channels:history` — 공개 채널 파일 이벤트
     - `groups:history` — 비공개 채널 파일 이벤트 (필요 시)

4. **Event Subscriptions**
   - **Enable Events** ON
   - **Subscribe to bot events** → `file_shared` 추가

5. **Install App** (좌측 상단 Install to Workspace)
   - 권한 확인 → 허용
   - 표시되는 `xoxb-…` Bot Token 복사

(선택) **App Home** → Display Name 등 외양 다듬기.

---

## 2. 토큰 주입 (1분)

```bash
cd ~/dev/ji-slack-admin
cp .env.example .env
# .env 열어서 SLACK_BOT_TOKEN=xoxb-... / SLACK_APP_TOKEN=xapp-... 채우기
```

---

## 3. 테스트 채널 + 봇 초대 (2분)

Slack 클라이언트에서:

1. 테스트용 채널 생성 (예: `#test-hwp-bot`, 본인만 멤버)
2. 채널 우상단 ⚙ → **Add apps** → `HWP Preview` 추가

---

## 4. 봇 실행 + 동작 확인 (5분)

```bash
cd ~/dev/ji-slack-admin
uv sync          # 처음이면
./scripts/run_bot.sh
```

기대 로그:
```
… INFO hwp_pdf_bot hwp-pdf bot starting (socket mode)
… INFO slack_bolt.app.app A new session has been established
```

테스트 채널에서:
- `samples/sample-binary.hwp` 를 슬랙에 드래그
- 1~10초 후 같은 스레드(또는 채널)에 PDF 회신 떠야 함

로그에 `convert request file=… name=…` → `uploaded pdf file=…` 흐름 보이는지 확인.

---

## 5. (선택) 실사용 채널에 배포

동작 확인되면 실제로 hwp 가 오가는 채널들에 봇을 초대. 봇은 **초대된 채널에서만** 반응함 — 워크스페이스 전체에 풀지 말고 점진적으로.

---

## 6. (선택) 항시 실행 셋업

지금은 터미널을 닫으면 봇도 죽음. 항시 실행하려면:
- **launchd** plist 작성 → `~/Library/LaunchAgents/com.namun.hwp-pdf-bot.plist`
- 또는 `tmux` / `screen` 세션
- 또는 별도 리눅스 머신/VPS 로 이전 (LibreOffice + JDK + H2Orestart 동일 셋업)

이 단계는 봇이 잘 동작하는 걸 본 다음에 진행.

---

## 트러블슈팅

- **봇이 응답 안 함**: 봇이 채널 멤버인지 확인. `file_shared` 이벤트는 봇이 들어있는 채널에서만 수신.
- **변환 실패 메시지**: `~/Library/Application Support/LibreOffice/4/user/config/javasettings_MacOSX_AARCH64.xml` 의 `<enabled>` 가 `true` 인지 재확인. `./scripts/hwp2pdf.sh samples/sample-binary.hwp` 로컬에서 직접 변환되는지 먼저 확인.
- **토큰 invalid_auth**: `.env` 의 토큰 앞뒤 공백/줄바꿈, `xoxb-` / `xapp-` prefix 정상인지 확인.
- **이벤트 자체가 안 옴**: api.slack.com 의 앱 페이지 → Event Subscriptions 가 Enabled 인지, Socket Mode 가 ON 인지 둘 다 확인.
