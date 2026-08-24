<!-- forge-slug: pcb-align-4of4 -->
<!-- task: 15 -->
<!-- part: 4/4 -->
<!-- tdd: off -->
<!-- priority: low -->
# 문서를 PCB 기준으로 다시 쓰고 손배선 자료를 걷어낸다

## Goal / Non-goals
- Goal: README의 핀 배치 표와 부품 표를 PCB 기준으로 재작성하고, PCB로 대체돼 이제 **틀린 정보**가 된 손배선 자료를 제거하고, 매트릭스 배선 표를 파서로 자동 생성해 삽입한다.
- Non-goals: `.worktree/pcb`의 `image/left-wire.png`·`right-wire.png`를 **가져오지 않는다**(그것도 kbfirmware 손배선도라 같은 이유로 폐기 대상). EasyEDA에서 회로도 이미지를 export하지 않는다(수동 작업이며 epro가 원천). 손배선 섹션을 "구버전 기록"으로 남기지 않고 삭제한다 — git 이력에 남는다.

## Source of truth
- Glossary terms: 메인 PCB · aux 보드 · 분할 링크 · AuxStack (`.forge/CONTEXT.md`)
- Related ADRs: `.forge/adr/260824-001947-epro-is-the-source-of-pcb-geometry.md`, `.forge/adr/260824-001950-split-link-is-usb-c-three-wire-half-duplex.md`, `.forge/adr/260824-001948-case-wraps-the-pcb-not-skinned-by-it.md`
- Definition of Done (대상 파일은 `README.md` 단일):
  1. 핀 표가 PCB 기준이다: `grep -c "GP2 *| *ROW 0" README.md` ≥ 1 이고 `grep -c "TRRS" README.md` → 0. **사전 상태: 지금 표는 `ROW 0~5 = GP0~GP5`, `GP15 = TRRS 시리얼`, `5V = TRRS VCC`로 행 수·핀·커넥터·전원이 모두 틀리다 → 전진 검사.**
  2. `grep -c "wiring-left.png\|wiring-right.png" README.md` → 0. **사전 상태: 2 → 전진 검사.**
  3. `grep -c "kbfirmware" README.md` → 0. **사전 상태: 1 → 전진 검사.**
  4. `grep -c "스트레오 컨넥트" README.md` → 0. **사전 상태: 1 → 전진 검사.**
  5. 부품 표에 `USB-C` 브레이크아웃 · 저상형 16핀 소켓 · `8x2` 자석 · `SOD-323` 항목이 각각 1행 이상 있고, 3.5mm 잭/TRRS 케이블/랩핑와이어 행이 없다. **사전 상태: 자석이 `5x2mm`로 적혀 있어 `PARAMS`(당시 ⌀10)와 이미 어긋나 있었다 → 전진 검사.**
  6. 매트릭스 표가 `tools/`의 생성기 산출물이며, 재실행 후 `git diff`가 비어 있다.

## Work slices
- [ ] S1. 핀 배치 표 재작성 — `ROW0~4 = GP2~GP6`, `COL0~8 = GP7~GP15`(좌는 COL6까지), `GP0 = 분할 링크 half-duplex`, `3V3`·`GND`. "이 표의 원천은 `pcb/split-keyboard.epro`" 명시. 행 수를 6 → 5로, 커넥터를 TRRS → USB-C로 정정 — 완료 기준: DoD 1.
- [ ] S2. 손배선 자료 제거 — 배선도 이미지 2개 참조, "스트레오 컨넥트 연결 핀" 섹션, kbfirmware 문구 — 완료 기준: DoD 2·3·4.
- [ ] S3. 부품 표 갱신 — 추가: USB-C 브레이크아웃 2, 저상형 1×16 소켓 2 + 1×16 남성 헤더 2(메인 PCB용), 다이오드 1N4148WS(SOD-323) 73, 메인 PCB 2 + aux 보드 2. 변경: 자석 `5x2mm` → `8x2mm` 4개, 나사 M3×10 → M3×12. 삭제: 3.5mm 잭 · TRRS 케이블 · 전선/랩핑와이어 — 완료 기준: DoD 5.
- [ ] S4. 매트릭스 표 생성기 — 1of4의 파서로 좌/우 "키 ↔ ROW/COL" 표를 만들어 README에 삽입하는 생성기를 `tools/`에 추가(`gen_keylayout.py`가 인라인 KLE 블록을 갱신하는 방식과 같은 마커 방식) — 완료 기준: DoD 6.
- [ ] S5. 조립 문서 갱신 — 케이스 치수(좌 156.06×113.95×14 / 우 208.45×113.95×14), 조립 스택(플레이트 → PCB → aux 보드), 스위치가 납땜이므로 플레이트를 먼저 끼우고 납땜해야 한다는 순서, USB-C 포트 2개의 구별(분할 링크 포트에 PC를 꽂으면 안 된다는 경고) — 완료 기준: 위 네 항목이 각각 한 문단 이상으로 존재.
