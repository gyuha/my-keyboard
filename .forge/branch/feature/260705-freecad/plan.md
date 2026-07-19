<!-- forge-slug: fn-cmd-win-mac-swap --> <!-- task: 4 --> <!-- tdd: off --> <!-- retro-hint: optional -->
# Fn+Command 로 왼쪽 Alt↔Command 스왑 토글 (Windows/Mac 모드 전환)

## Goal / Non-goals
- Goal: `gkey` QMK 키맵에 **왼쪽 전용** modifier 스왑 토글을 추가한다. `MO(_FN2)`를 누른 상태에서 command 자리(L51)를 탭하면 **왼쪽 command(LGUI)와 왼쪽 alt(LALT)의 출력이 서로 맞바뀐다** — Windows 배열(`Ctrl-Win-Alt`)과 Mac 배열(`Ctrl-Option-Cmd`)을 오가는 물리 스위치. 토글 상태는 EEPROM에 저장되어 재부팅·재연결 후에도 유지된다.
- Non-goals:
  - **양쪽 스왑** — QMK 내장 `AG_TOGG`(양쪽 Alt/GUI)는 오른쪽 반쪽의 Alt 키(R50 RALT, R52)까지 GUI로 바꾸므로 쓰지 않는다. 왼쪽 클러스터만 스왑한다.
  - 오른쪽 반쪽 R52의 기존 `KC_LALT` 이상치 수정 — 이번 범위 밖(발견 사항으로만 기록, 그대로 둠).
  - VIA GUI 노출(via.json `customKeycodes` 등록) — 나중에 원하면 추가할 선택적 폴리시. 이번엔 keymap.c 기본 키맵에만 반영.
  - 전체 Mac 레이어 신설, 미디어/스크린샷 등 다른 Mac 전용 리맵.
  - LED/RGB 등 모드 표시 피드백(RGBLIGHT 비활성).
  - 오른쪽 Command(RGUI) 키 신설.

## Source of truth
- Glossary terms: half(반쪽) — `.forge/CONTEXT.md`(각 반쪽은 독립 RP2040 컨트롤러).
- Related ADRs: 없음(신규 ADR 불필요 — keymap 편집이라 되돌리기 쉽고, 좌측 전용 선택 이유는 코드 주석으로 충분).
- 현재 상태(참고):
  - `gkey/keymaps/default/keymap.c:20` — `_QWERTY` 왼쪽 엄지행: L50=`KC_LCTL`, L51=`KC_LGUI`(command), L52=`KC_LALT`, L53=`MO(_FN2)`, L54=`KC_SPC`.
  - `gkey/keymaps/default/keymap.c:34` — `_FN2` 왼쪽 엄지행 L51 자리는 현재 `_______`(비어 있음) → 여기에 토글 키코드 배치.
  - `gkey/rules.mk` — `MCU = RP2040`, `VIA_ENABLE = yes`, `MAGIC`은 기본 활성.
- 확정 설계 결정:
  - 스왑 범위 = **왼쪽 전용** (`keymap_config.swap_lalt_lgui` 비트만 토글).
  - 트리거 = `_FN2` 레이어의 **L51** 자리에 커스텀 토글 키코드 배치 → `MO(_FN2)`(L53) 홀드 + L51 탭.
  - 지속성 = 토글 시 `eeconfig_update_keymap(...)`로 EEPROM 저장(정확한 호출 시그니처는 설치된 QMK 버전에 맞춰 구현 시 확인 — 구버전 `keymap_config.raw` vs 신버전 포인터).
  - 기본 부팅 모드 = Windows(`swap_lalt_lgui` 기본 0).
  - 커스텀 키코드는 `SAFE_RANGE` enum으로 정의, `process_record_user`에서 처리.
- 빌드/검증 환경:
  - `qmk`(`~/.local/bin/qmk`)로 `~/qmk_firmware/keyboards/gkey`(심볼릭 링크) 컴파일: `qmk compile -kb gkey -km default`.
  - **ARM 공식 툴체인**으로 빌드(메모리 `qmk-arm-toolchain-broken`: brew arm-none-eabi-gcc는 newlib 누락).
  - RP2040 → `.uf2` 산출, BOOTSEL 모드에서 드래그 플래시.
  - **VIA EEPROM 함정** [높음]: VIA가 켜져 있어 실제 키맵은 EEPROM에서 로드됨. VIA로 키맵을 저장한 적이 있으면 플래시 후에도 기존 EEPROM 키맵이 남아 _FN2/L51 토글이 적용 안 될 수 있음 → **EEPROM 리셋(부트매직: 좌상단 키 홀드 후 연결)** 필요.
- Definition of Done:
  - `gkey/keymaps/default/keymap.c`에 커스텀 토글 키코드가 정의되고, `process_record_user`가 `keymap_config.swap_lalt_lgui`를 토글·EEPROM 저장하며, `_FN2` L51에 배치됨.
  - `qmk compile -kb gkey -km default`가 에러 없이 성공하고 `.uf2` 산출.
  - (수동, 하드웨어 필요) 아래 UAT 항목 전부 통과.

## Work slices
- [ ] S1. keymap.c에 왼쪽 전용 스왑 토글 구현 — `SAFE_RANGE` 커스텀 키코드 정의, `process_record_user`에서 `keymap_config.swap_lalt_lgui ^= 1` + EEPROM 저장, `_FN2` 레이어 L51의 `_______`를 이 키코드로 교체, 좌측 전용 선택 이유 주석 추가 — 완료 기준: `qmk compile -kb gkey -km default`가 ARM 공식 툴체인으로 성공하고 `.uf2` 생성.
- [ ] S2. (수동, 하드웨어) 플래싱 후 UAT (depends: S1) — 완료 기준: 사용자가 실제 보드에서 다음을 확인:
  1. 기본 모드에서 왼쪽 command=Win/GUI, 왼쪽 alt=Alt.
  2. `MO(_FN2)` 홀드 + L51 탭 → 왼쪽 command 자리가 Alt, 왼쪽 alt 자리가 Cmd(GUI)로 스왑.
  3. 다시 토글 → Windows 모드 복귀.
  4. USB 재연결/재부팅 후 마지막 모드 유지(EEPROM 지속성).
  5. 오른쪽 Alt 키(R50, R52)는 두 모드 모두에서 Alt 유지(좌측 전용 확인).
