# ji-slack-admin context

> 이 문서는 프로젝트 외부에 공개하지 않는 내부 컨텍스트다. AI 어시스턴트가 작업을 이어받을 때 배경을 빠르게 파악하기 위한 용도.

## 목적

제주연구원 Slack 워크스페이스 운영/관리 작업을 Claude Code 안에서 처리하기 위한 작업 폴더. 운영자는 본인(조남운, `namun@ji.re.kr`, Slack user_id `U09M60HKY73`) — 워크스페이스 관리자.

자매 폴더: [`ji-google-workspace-admin`](../ji-google-workspace-admin), [`ji-monday-admin`](../ji-monday-admin), [`ji-calendar-monday-integration`](../ji-calendar-monday-integration).

## 사용 가능한 도구

claude.ai Slack MCP 가 전역으로 붙어있음 (`mcp__claude_ai_Slack__*`). 별도 SA/OAuth 셋업 불필요.

### Read (확인용)

- `slack_read_channel` — 채널 메시지
- `slack_read_thread` — 스레드
- `slack_search_public` / `slack_search_public_and_private` — 메시지 검색 (`from:`, `in:`, `before:`, `after:` 필터)
- `slack_search_channels` / `slack_search_users`
- `slack_read_user_profile` — 사용자 프로필
- `slack_read_canvas`

### Write (외부 가시 액션 — 실행 전 사용자 확인)

- `slack_send_message`
- `slack_send_message_draft`
- `slack_schedule_message`
- `slack_create_canvas` / `slack_update_canvas`

쓰기 도구는 모두 외부에 보이는 액션이므로 실행 전 항상 사용자 컨펌을 받는다.

## 작업 패턴 (예상)

- 채널/스레드 요약, 멘션·키워드 검색
- 정기 공지·리마인더 (스케줄 전송)
- Canvas 기반 운영 문서 관리
- Gmail / Google Calendar / monday.com MCP 와 조합 (예: Slack 스레드 → Gmail 초안, monday 보드 이벤트 → Slack 공지)

## 진행 중 작업

### HWP → PDF 자동 변환 봇 (2026-05-13 ~)

**문제**: 채널에 누군가 hwp 파일을 올리면 Slack에서 미리보기가 안 되어 다운로드받아 한컴으로 열어야 한다. 내부 문서 유통 속도가 느려짐.

**해결 방향**: 채널의 `file_shared` 이벤트를 감지 → hwp/hwpx면 PDF로 변환 → 동일 스레드에 PDF 회신 (원본 hwp는 유지).

**변환 백엔드 결정 (2026-05-13)**: **B안 = LibreOffice + H2Orestart 확장**.

- A안 (Windows + 한컴 COM, 기존 `~/dev/hwp2pdf` 재활용) 기각 사유:
  - Windows 머신 항시 가동 필요 → 봇 인프라로 부적합
  - 변환 도중 한컴 보안경고창이 떠서 비대화형 자동화 불가
- B안 선택 이유: 맥/리눅스 헤드리스 동작 가능, 클라우드 친화적, 봇 PoC 빠르게 가능. 충실도(복잡 레이아웃·폰트) 깨지면 그때 A/C 검토.

**작업 순서**:

1. ~~LibreOffice + H2Orestart 설치~~ ✅ (2026-05-13)
2. ~~변환 CLI 래퍼~~ ✅ `scripts/hwp2pdf.sh` (2026-05-13)
3. ~~샘플 hwp 변환 충실도 검증~~ ✅ "대충 읽히면 OK" 수준 합의 (2026-05-13, 사용자 시각 확인)
4. ~~Slack 봇 코드 스캐폴딩~~ ✅ `src/ji_slack_admin/hwp_pdf_bot.py` (Socket Mode, slack-bolt, 2026-05-13)
5. ⏭️ **Slack 앱 생성 + 토큰 발급 + 채널 동작 검증** — 사용자 작업, [TOMORROW.md](TOMORROW.md) 참조
6. ⏭️ 항시 실행 셋업 (launchd / 별도 호스트) — 검증 후

### 변환 백엔드 셋업 메모 (macOS arm64)

설치된 컴포넌트:

- LibreOffice 26.2.3.2 (`brew install --cask libreoffice`)
- OpenJDK 21.0.11 arm64 (`brew install openjdk@21`)
- `/Library/Java/JavaVirtualMachines/openjdk-21.jdk` 심볼릭 링크 (sudo 필요한 1회 작업, brew caveat 그대로)
- H2Orestart v0.7.12 (`vendor/H2Orestart-v0.7.12.oxt`, sha256 `7b5f6f24...76566`)
- `~/Library/Application Support/LibreOffice/4/user/config/javasettings_MacOSX_AARCH64.xml`: `<enabled xsi:nil="false">true</enabled>` 로 수동 활성화 (LibreOffice가 JDK는 자동 탐지하나 enabled 기본값 false)

알려진 무해 현상:

- `unopkg add` 시 "An error occurred while enabling: H2Orestart.jar: NoConnectException pipe" 에러가 나오나 확장은 실제로 등록되며 변환 시 정상 작동. soffice가 lazy하게 필터를 등록함.

변환 호출 패턴:

- `.hwp` (바이너리 HWP5): `--infilter='Hwp2002_File'` 명시 필요
- `.hwpx`: 자동 감지 OK
- 헤드리스: `soffice --headless --norestore --nologo --nofirststartwizard --convert-to pdf --outdir <out> <input>`

샘플 결과 (`samples/`):

- `sample-binary.hwp` 75KB → `sample-binary.pdf` 309KB
- `sample-xml.hwpx` 102KB → `sample-xml.pdf` 418KB
- 출처: 제주도청 정책기획관실 자문단 운영 문서 (정부 양식, 복잡 레이아웃 — 충실도 검증용)

### 봇 코드 메모

- 진입점: `python -m ji_slack_admin.hwp_pdf_bot` (또는 `./scripts/run_bot.sh`)
- 연결: Socket Mode (`slack-bolt` + `slack_sdk`, App-Level Token `xapp-…` + Bot Token `xoxb-…`)
- 트리거: `file_shared` 이벤트. 확장자 `.hwp` / `.hwpx` 만 처리, 그 외 무시.
- 처리 흐름: `files.info` → `url_private_download` 로 다운로드 → `scripts/hwp2pdf.sh` 호출 → `files.upload_v2` 로 동일 채널 스레드에 PDF 회신.
- 회신 실패/변환 실패는 `chat.postMessage` 로 :warning: 알림.
- `App(token=…)` 가 import 시점에 `auth.test` 부르므로 모듈 로드 사이드이펙트 방지 위해 `build_app()` 팩토리 패턴.
- 환경: `python-dotenv` 로 `.env` 자동 로드, 토큰은 거기서.

### 보안/운영 메모

- `.env` 는 `.gitignore` 처리. 토큰은 절대 커밋 금지.
- 봇은 **초대된 채널만** 보임 — 워크스페이스 전체 자동 처리 안 함. 안전망.
- 봇이 자신이 올린 PDF 에 다시 반응할 위험 없음 — `.pdf` 확장자는 필터에서 제외됨.
- 변환 timeout 180초. 대형 hwp 면 더 길어질 수 있으니 추후 조정.

## 상태

2026-05-13 마감 시점:

- 변환 백엔드 완료, 샘플 2건 변환 검증 OK
- 봇 코드 스캐폴딩 + 의존성 설치 (`uv sync`) 완료, 모듈 import 검증 통과
- 토큰만 채우면 즉시 실행 가능 상태
- 다음 단계 = [TOMORROW.md](TOMORROW.md) (사용자 직접 작업)
