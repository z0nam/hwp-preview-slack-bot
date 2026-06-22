# 미리보기 변환 엔진을 rhwp로 교체 검토 (LibreOffice+H2Orestart → rhwp)

> 출처: 2026-06-23 hwp-agent 세션에서 rhwp를 JAIX 제안요청서로 A/B 평가하다가 파생.
> 이 봇의 PDF 미리보기를 rhwp로 바꾸면 스택이 대폭 단순해질 수 있다는 가설.

## 현재 (이 봇)
- 입력: 슬랙 업로드 `.hwp`/`.hwpx`
- 출력 **2종**: **PDF**(슬랙에서 읽기) + **DOCX**(Word/구글독스에서 편집용 가져가기)
- 스택: headless **LibreOffice + H2Orestart(.oxt) + OpenJDK 21**

## rhwp란
- Rust+WASM HWP/HWPX **뷰어/에디터 + 자체 조판엔진**. MIT. CLI 단일 바이너리(~10MB), Linux/macOS/Windows 프리빌드+SHA256. repo: https://github.com/edwardkim/rhwp (최신 v0.7.17)
- CLI: `rhwp export-pdf <in.hwp|hwpx> -o out.pdf` · `export-svg` · `export-png`(릴리스 바이너리엔 native-skia 빠져 **PDF/SVG만** 됨) · `info` · `dump`
- **`.hwp` 바이너리도 네이티브 렌더**(HWP5/HWP3) → Java/변환 불필요

## A/B 결과 (JAIX 제안요청서, rhwp v0.7.17 vs 한컴 PDF)
- **내용·요소 충실도: 우수** — 표지/목차/병합셀 표/색상/불릿/점선/페이지번호 정확, 누락·깨짐 0
- **레이아웃·페이지네이션: 벌어짐** — rhwp 167p vs 한컴 134p(+25%), 줄간격 더 큼, 폰트 치환(한컴바탕/휴먼명조 없음). overflow 경고 66건
- → **미리보기(글랜스)엔 페이지네이션 차이 무관**, 내용 충실도가 관건이라 **충분**. (정밀 사인오프용이 아니므로 OK)

## 결정 게이트: DOCX "편집용 가져가기"를 실제로 쓰나?
| 출력 | rhwp 대체 | 비고 |
|---|---|---|
| PDF(읽기) | 🟢 됨, 더 나음 | 네이티브 렌더, `.hwp`도 Java 없이 |
| DOCX(편집) | 🔴 안 됨(아직) | rhwp 렌더러라 DOCX 내보내기 없음(v1.0 로드맵 예정) |

- **DOCX 거의 안 씀** → PDF만 rhwp로, **LibreOffice·OpenJDK·H2Orestart 통째 제거** = 10MB 바이너리 하나. 운영 대폭 단순화 + fidelity↑. **완승.**
- **DOCX 필요** → DOCX 때문에 LibreOffice 스택 유지해야 함 → PDF만 교체하면 이득 반감. (게다가 그 DOCX 자체가 H2Orestart "번역체"라 편집 충실도도 애매)

## 다음 스텝 (이 세션에서)
1. **fidelity 스팟체크**: `samples/`의 hwp 1~2개로 rhwp PDF vs 현재 LO+H2O PDF 비교(미리보기 품질).
2. **DOCX 실사용 여부 확정** → 전환 범위 결정(PDF만 / 완전 교체).
3. 전환 시: `src`의 soffice 호출(셸 스크립트 래퍼)을 `rhwp export-pdf`로 치환, vendor의 oxt·JDK 의존 제거, launchd/요구사항 갱신, README 정정.
4. 서버에 한글 폰트 확보(또는 rhwp `--font-path`) — LibreOffice도 어차피 필요했던 것.

## 참고
- rhwp 바이너리/체크섬: `gh release download v0.7.17 --repo edwardkim/rhwp --pattern "*macos-aarch64*" --pattern SHA256SUMS.txt`
- hwp-agent 쪽 관련 문서: `~/dev/hwp-agent/docs/output-verification.md`(왜 정밀 검증엔 한컴, 왜 rhwp/LibreOffice가 SoT로 부적합한지 — lineseg 이슈). 단 *미리보기*는 정밀 불요라 rhwp로 충분.
