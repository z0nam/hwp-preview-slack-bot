# hwp-pdf-slack-bot

Slack 채널에 올라온 한컴오피스 파일(`.hwp` / `.hwpx`)을 자동으로 PDF로 변환해 같은 스레드에 미리보기로 회신하는 봇. 원본 hwp는 그대로 유지됨.

한컴오피스가 설치돼 있지 않은 멤버도 채널에서 바로 내용을 확인할 수 있게 하는 게 목적. macOS/Linux 헤드리스 환경에서 LibreOffice + [H2Orestart](https://github.com/ebandal/H2Orestart) 확장으로 변환.

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
./scripts/hwp2pdf.sh samples/sample-binary.hwp
./scripts/hwp2pdf.sh samples/sample-xml.hwpx
```

### Slack 앱 셋업 (1회)

[api.slack.com/apps](https://api.slack.com/apps) → Create New App (From scratch) → Workspace 선택. 이후:

- **Socket Mode** ON → App-Level Token (`xapp-…`, scope `connections:write`) 발급
- **OAuth & Permissions** → Bot Token Scopes: `files:read`, `files:write`,
  `chat:write`, `channels:history`, `groups:history`, `im:history`, `mpim:history`
  (뒤의 두 개는 봇과의 DM/그룹 DM에서도 hwp 자동 변환이 되게 해주는 스코프. 채널에서만 쓸 거면 빼도 무방.)
- **Event Subscriptions** → Enable → Subscribe to bot events → `file_shared`
- **Install to Workspace** → Bot Token (`xoxb-…`) 발급
- **Basic Information → Display Information**: App icon은 `assets/icon.png` 사용

## 실행

```bash
cp .env.example .env  # 토큰 채우기
uv sync
./scripts/run_bot.sh
```

봇이 머무는(초대된) 채널에 누가 hwp를 올리면 1~10초 후 PDF가 같은 스레드에 회신됨.

## 항시 실행 (launchd, macOS)

`~/Library/LaunchAgents/com.namun.hwp-pdf-bot.plist` 로 사용자 LaunchAgent 등록.
재부팅·로그인 시 자동 시작, 크래시 시 자동 재시작.

```bash
launchctl load -w ~/Library/LaunchAgents/com.namun.hwp-pdf-bot.plist

# 상태 / 로그
launchctl list | grep hwp-pdf
tail -f ~/Library/Logs/hwp-pdf-bot.err   # python logging 은 stderr 로 감

# 재시작 / 중지
launchctl kickstart -k gui/$(id -u)/com.namun.hwp-pdf-bot
launchctl unload ~/Library/LaunchAgents/com.namun.hwp-pdf-bot.plist
```

전제: 호스트 맥이 자동 로그인 + 잠자기 꺼져있을 것 (LaunchAgent는 GUI 세션에 의존).

리눅스로 옮기려면 launchd plist 폐기 → 동일 구성요소(LibreOffice + JDK + H2Orestart)로 systemd unit 작성. 변환 백엔드는 동일하게 동작함.

## 디렉토리

```
src/hwp_pdf_slack_bot/__main__.py    봇 본체 (Socket Mode, slack-bolt)
scripts/hwp2pdf.sh                   HWP/HWPX → PDF (LibreOffice headless)
scripts/run_bot.sh                   봇 런처
scripts/make_icon.py                 Slack 앱 아이콘 생성기 (Pillow)
assets/icon.png                      Slack 앱 등록용 아이콘 (1024×1024)
samples/                             변환 검증용 (PDF는 .gitignore)
vendor/H2Orestart-*.oxt              LibreOffice 확장
context.md                           내부 컨텍스트 (AI/신규합류자용)
```

## 충실도 정책

PDF 변환은 "대충 읽히면 OK" 수준. 원본 hwp는 슬랙 첨부로 그대로 남아있으므로 PDF는 미리보기 보조 자료. 폰트/표 정렬이 일부 깨져도 허용. 완전 실패할 때만 백엔드 교체 검토.

## 라이선스 / 출처 메모

- `vendor/H2Orestart-v0.7.12.oxt` — [ebandal/H2Orestart](https://github.com/ebandal/H2Orestart) (LGPL-2.1+) — LibreOffice 가 HWP/HWPX 를 읽도록 해주는 핵심 확장. 재배포 가능.
- `samples/` — 제주도청 정책기획관실 자문단 운영 문서 (정부 양식, 변환 충실도 검증용)
