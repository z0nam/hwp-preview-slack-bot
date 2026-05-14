# hwp-pdf-slack-bot context

> 프로젝트 내부 컨텍스트. AI 어시스턴트가 작업을 이어받을 때 배경을 빠르게 파악하기 위한 용도.

## 목적

채널에 누군가 hwp 파일을 올리면 Slack 에서 미리보기가 안 되어 다운로드받아 한컴오피스로 열어야 한다. 내부 문서 유통 속도가 느려짐 — 이걸 해결하기 위한 봇.

**해결 방향**: 채널의 `file_shared` 이벤트를 감지 → hwp/hwpx면 PDF로 변환 → 동일 스레드에 PDF 회신 (원본 hwp는 유지).

원래 [`ji-slack-admin`](../ji-slack-admin) (제주연구원 Slack 운영 폴더) 안에서 한 잡일로 시작했으나, 잘 풀려서 2026-05-14에 독립 프로젝트로 분리.

운영자: 조남운 (`namun@ji.re.kr`).

## 변환 백엔드 결정 (2026-05-13)

**B안 = LibreOffice + H2Orestart 확장** 선택.

- A안 (Windows + 한컴 COM, 기존 `~/dev/hwp2pdf` 재활용) 기각 사유:
  - Windows 머신 항시 가동 필요 → 봇 인프라로 부적합
  - 변환 도중 한컴 보안경고창이 떠서 비대화형 자동화 불가
- B안 선택 이유: 맥/리눅스 헤드리스 동작 가능, 클라우드 친화적, 봇 PoC 빠르게 가능. 충실도(복잡 레이아웃·폰트) 깨지면 그때 A/C 검토.

## 변환 백엔드 셋업 메모 (macOS arm64)

설치된 컴포넌트:

- LibreOffice 26.2.3.2 (`brew install --cask libreoffice`)
- OpenJDK 21.0.11 arm64 (`brew install openjdk@21`)
- `/Library/Java/JavaVirtualMachines/openjdk-21.jdk` 심볼릭 링크 (sudo 필요한 1회 작업, brew caveat 그대로)
- H2Orestart v0.7.12 (`vendor/H2Orestart-v0.7.12.oxt`)
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

## 봇 코드 메모

- 진입점: `python -m hwp_pdf_slack_bot` (= `src/hwp_pdf_slack_bot/__main__.py`, 또는 `./scripts/run_bot.sh`)
- 연결: Socket Mode (`slack-bolt` + `slack_sdk`, App-Level Token `xapp-…` + Bot Token `xoxb-…`)
- 트리거: `file_shared` 이벤트. 확장자 `.hwp` / `.hwpx` 만 처리, 그 외 무시.
- 처리 흐름: `files.info` → `url_private_download` 로 다운로드 → `scripts/hwp2pdf.sh` 호출 → `files.upload_v2` 로 동일 채널 스레드에 PDF 회신.
- 회신 실패/변환 실패는 `chat.postMessage` 로 :warning: 알림.
- `App(token=…)` 가 import 시점에 `auth.test` 부르므로 모듈 로드 사이드이펙트 방지 위해 `build_app()` 팩토리 패턴.
- 환경: `python-dotenv` 로 `.env` 자동 로드, 토큰은 거기서.

## 보안/운영 메모

- `.env` 는 `.gitignore` 처리. 토큰은 절대 커밋 금지.
- 봇은 **초대된 채널만** 보임 — 워크스페이스 전체 자동 처리 안 함. 안전망.
- 봇이 자신이 올린 PDF 에 다시 반응할 위험 없음 — `.pdf` 확장자는 필터에서 제외됨.
- 변환 timeout 180초. 대형 hwp 면 더 길어질 수 있으니 추후 조정.

## 운영 셋업 (macOS launchd, 2026-05-14~)

호스트: 본인 맥미니. LaunchAgent (사용자 세션) 로 등록 — 자동 로그인 ON 전제.

- plist: `~/Library/LaunchAgents/com.namun.hwp-pdf-bot.plist` (레포 밖, 호스트 종속)
- 로그: `~/Library/Logs/hwp-pdf-bot.{log,err}` (실로그는 stderr 쪽)
- KeepAlive=true, ThrottleInterval=10 — 크래시 시 자동 재시작
- PATH 환경변수에 `/Users/namun/.local/bin`(uv), `/opt/homebrew/bin`(soffice) 명시
- 토큰 회전 시 `.env` 수정 후 `launchctl kickstart -k gui/$(id -u)/com.namun.hwp-pdf-bot`
- 클라우드/리눅스 이전 시 plist 폐기 후 systemd unit 으로 교체 (LibreOffice + JDK + H2Orestart 셋업은 거의 동일하게 재현됨)

## Slack 앱 아이콘

`assets/icon.png` (1024×1024, Pillow 로 생성). `scripts/make_icon.py` 에서 색/크기/라벨 조정 후 재생성 가능. Slack 앱 페이지 → Basic Information → Display Information 에 업로드해서 사용.

## 상태

2026-05-14:

- 변환 백엔드 완료, 샘플 2건 변환 검증 OK
- Slack 앱 등록 완료, 토큰 발급/주입 완료
- 테스트 채널에서 hwp → PDF 변환 동작 확인됨 (사용자 시각 검증)
- launchd LaunchAgent 로 항시 실행 중
- 독립 레포로 분리, 버전 `2026.05.14.1` 태그
- 실사용 채널로의 점진적 배포는 사용자 페이스로 진행

## 향후 개선 후보 (낙서)

- 변환 충실도가 부족한 hwp 패턴 식별 → H2Orestart 옵션 튜닝 또는 백엔드 교체
- `.docx`, `.xlsx` 등 다른 한컴/오피스 포맷도 처리 (Slack 미리보기 안 되는 케이스 있는지 확인 필요)
- 변환 timeout 동적 조정 (파일 크기 기반)
- 메트릭 / 알림 (실패율, 평균 변환 시간)
- 리눅스 / Docker 이미지로 호스트 이전
