<!-- forge-slug: split-master-left -->
<!-- task: 16 -->
<!-- tdd: off -->
<!-- priority: high -->
<!-- retro-hint: optional -->
# PC 연결 반쪽을 좌측으로 바꾼다 (MASTER_LEFT)

## Goal / Non-goals
- Goal: 우측 호스트 USB-C 가 케이스 뒷벽에 닿지 않으므로 `MASTER_RIGHT` → `MASTER_LEFT` 로 바꾸고, 그 전제에 기대던 주석을 정정한다.
- Non-goals: 케이스 형상을 건드리지 않는다(3of4). README 를 고치지 않는다(4of4). 키맵·배열·핀 정의를 건드리지 않는다.

## Source of truth
- Glossary terms: aux 보드 · 분할 링크 (`.forge/CONTEXT.md`)
- Related ADRs: `.forge/adr/260824-003937-usb-host-is-the-left-half.md`
- Definition of Done:
  1. `grep -c "^#define MASTER_LEFT" gkey/keymaps/default/config.h` → 1 이고 `grep -c "^#define MASTER_RIGHT" gkey/keymaps/default/config.h` → 0. **사전 상태: 각각 0 / 1 → 전진 검사.**
  2. `PATH=/Applications/ArmGNUToolchain/15.2.rel1/arm-none-eabi/bin:$PATH qmk compile -kb gkey -km default` 가 exit 0. **사전 상태: exit 0 → 회귀 방지 검사.**
  3. `python3 tools/verify_pcb_matrix.py` 와 `python3 tools/verify_keylayout.py` 가 둘 다 exit 0. **사전 상태: 둘 다 exit 0 → 회귀 방지 검사.**
  4. `firmware/gkey_default.uf2` 가 갱신되고 빌드 산출물과 바이트 일치. **사전 상태: `645b3be2ae978878f1a9bd6b988a0e35` → 소스가 바뀌면 반드시 달라지므로 전진 검사.**

## Work slices
- [ ] S1. `gkey/keymaps/default/config.h` 에서 `MASTER_RIGHT` → `MASTER_LEFT` — 완료 기준: DoD 1.
- [ ] S2. `gkey/config.h` 의 BOOTMAGIC 주석 정정 — 현재 주석이 "USB 가 우측에 있으므로(MASTER_RIGHT) 마스터는 자기 행 5~9 만 읽는다"를 근거로 `_RIGHT` 쌍의 존재를 설명한다. 마스터가 좌측이 되면 `BOOTMAGIC_ROW/COLUMN`(0,0 = 좌측 ESC)이 마스터가 직접 읽는 자리가 되므로 그 설명이 뒤집힌다. `_RIGHT` 쌍(5,0 = 우측 `6`) 자체는 유효하니 값은 그대로 두고 근거만 고친다 — 완료 기준: 주석에 `MASTER_RIGHT` 라는 전제가 남아 있지 않다(`grep -c "MASTER_RIGHT" gkey/config.h` → 0).
- [ ] S3. 빌드 후 `firmware/gkey_default.uf2` 갱신 — 완료 기준: DoD 2·4. (depends: S1)
