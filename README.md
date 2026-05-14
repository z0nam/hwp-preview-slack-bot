# ji-slack-admin

제주연구원 Slack 워크스페이스 운영/관리 도구.

현재 포함:

- **HWP→PDF 미리보기 봇** (`src/ji_slack_admin/hwp_pdf_bot.py`) — 채널에 `.hwp` / `.hwpx` 파일이 올라오면 자동으로 PDF로 변환해 동일 채널에 회신. 원본 hwp는 그대로 유지.

## HWP→PDF 봇

### 의존 설치 (macOS arm64, 1회)

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

검증:
```bash
./scripts/hwp2pdf.sh samples/sample-binary.hwp
./scripts/hwp2pdf.sh samples/sample-xml.hwpx
```

### Slack 앱 셋업 (1회)

`TOMORROW.md` 참조.

### 실행

```bash
cp .env.example .env  # 토큰 채우기
uv sync
./scripts/run_bot.sh
```

Bot 이 머무는 채널에 누가 hwp를 올리면 1~10초 후 PDF가 같은 스레드에 회신됨.

## 디렉토리

```
src/ji_slack_admin/hwp_pdf_bot.py   봇 본체 (Socket Mode)
scripts/hwp2pdf.sh                  HWP/HWPX → PDF (LibreOffice headless)
scripts/run_bot.sh                  봇 런처
samples/                            변환 검증용 (PDF는 .gitignore)
vendor/H2Orestart-*.oxt             LibreOffice 확장
context.md                          내부 컨텍스트 (AI/신규합류자용)
```

## 충실도 정책

PDF 변환은 "대충 읽히면 OK" 수준. 원본 hwp는 슬랙 첨부로 그대로 남아있으므로 PDF는 미리보기 보조 자료. 폰트/표 정렬이 일부 깨져도 허용. 완전 실패할 때만 백엔드 교체 검토.
