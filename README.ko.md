# hwp-preview-slack-bot

Slack 채널에 올라온 한컴오피스 파일(`.hwp` / `.hwpx`)을 자동으로 PDF + DOCX로 변환해 같은 스레드에 회신하는 봇. 원본 hwp는 그대로 유지됨.

한컴오피스가 설치돼 있지 않은 멤버도 채널에서 바로 내용을 확인할 수 있고(PDF), 필요하면 워드/구글닥스/리브레오피스로 바로 편집할 수 있게(DOCX) 하는 게 목적. macOS/Linux 헤드리스 환경에서 LibreOffice + [H2Orestart](https://github.com/ebandal/H2Orestart) 확장으로 변환.

## 설치

### 의존성 (macOS arm64, 1회)

```bash
brew install --cask libreoffice
brew install openjdk@21
sudo ln -sfn /opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk \
  /Library/Java/JavaVirtualMachines/openjdk-21.jdk
xattr -dr com.apple.quarantine /Applications/LibreOffice.app

# LibreOffice가 처음 떴을 때 javasettings xml 생성되도록 한번 실행
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --terminate_after_init
# 생성된 ~/Library/Application Support/LibreOffice/4/user/config/javasettings_MacOSX_AARCH64.xml 에서
# <enabled xsi:nil="true"/>  →  <enabled xsi:nil="false">true</enabled>
# 로 수정 (LibreOffice가 JDK 인식은 자동, enabled 플립만 수동)

# H2Orestart 확장
unopkg add ./vendor/H2Orestart-v0.7.12.oxt
# "An error occurred while enabling … NoConnectException pipe" 가 떠도 실사용엔 문제 없음 (lazy 등록)
```

변환 단독 검증:

```bash
./scripts/hwp2x.sh pdf  samples/sample-binary.hwp
./scripts/hwp2x.sh docx samples/sample-binary.hwp
./scripts/hwp2x.sh pdf  samples/sample-xml.hwpx
```

### Slack 앱 셋업 (1회)

[api.slack.com/apps](https://api.slack.com/apps) → Create New App (From scratch) → Workspace 선택. 이후:

- **Socket Mode** ON → App-Level Token (`xapp-…`, scope `connections:write`) 발급
- **OAuth & Permissions** → Bot Token Scopes: `files:read`, `files:write`,
  `chat:write`, `channels:history`, `groups:history`, `im:history`, `mpim:history`
  (뒤의 두 개는 봇과의 DM/그룹 DM에서도 hwp 자동 변환이 되게 해주는 스코프. 채널에서만 쓸 거면 빼도 무방.)
- **Event Subscriptions** → Enable → Subscribe to bot events → `file_shared`
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

봇이 머무는(초대된) 채널에 누가 hwp를 올리면 1~10초 후 PDF + DOCX가 같은 스레드에 회신됨.

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

리눅스로 옮기려면 launchd plist 폐기 → 동일 구성요소(LibreOffice + JDK + H2Orestart)로 systemd unit 작성. 변환 백엔드는 동일하게 동작함.

## 디렉토리

```
src/hwp_preview_slack_bot/__main__.py  봇 본체 (Socket Mode, slack-bolt)
scripts/hwp2x.sh                       HWP/HWPX → PDF/DOCX (LibreOffice headless)
scripts/run_bot.sh                     봇 런처
scripts/make_icon.py                   Slack 앱 아이콘 생성기 (Pillow)
assets/icon.png                        Slack 앱 등록용 아이콘 (1024×1024)
samples/                               변환 검증용 (PDF/DOCX는 .gitignore)
vendor/H2Orestart-*.oxt                LibreOffice 확장
context.md                             내부 컨텍스트 (AI/신규합류자용)
```

## 충실도 정책

PDF / DOCX 변환 모두 "대충 읽히면 OK" / "DOCX는 편집 시작점으로 쓸 만하면 OK" 수준. 원본 hwp는 슬랙 첨부로 그대로 남아있으므로 회신본은 보조 자료. 폰트/표 정렬이 일부 깨져도 허용. 완전 실패할 때만 백엔드 교체 검토.

## 라이선스 / 출처 메모

- `vendor/H2Orestart-v0.7.12.oxt` — [ebandal/H2Orestart](https://github.com/ebandal/H2Orestart) (LGPL-2.1+) — LibreOffice 가 HWP/HWPX 를 읽도록 해주는 핵심 확장. 재배포 가능.
- `samples/` — 제주도청 정책기획관실 자문단 운영 문서 (정부 양식, 변환 충실도 검증용)

## 감사

- [**H2Orestart**](https://github.com/ebandal/H2Orestart) — HWP/HWPX 임포트 필터의 실질. 이거 없으면 이 봇은 성립 안 함.
- 초기 구현 / OSS 화 / 운영 셋업은 [**Claude Code**](https://claude.ai/code) (Anthropic) 과 페어로 작업.
