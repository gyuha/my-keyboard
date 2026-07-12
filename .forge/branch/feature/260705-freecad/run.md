# run — Fn+Command 왼쪽 Alt↔Command 스왑 토글

실행일: 2026-07-13 · slug: fn-cmd-win-mac-swap

## 계획대로 된 것
- **S1 (코드 편집): 완료.** `gkey/keymaps/default/keymap.c` 3곳 수정:
  - `enum custom_keycodes { WINMAC = SAFE_RANGE }` 추가.
  - `process_record_user`에서 `WINMAC` 처리 — `keymap_config.swap_lalt_lgui ^= 1` 후 `eeconfig_update_keymap(&keymap_config)`로 EEPROM 저장, `return false`.
  - `_FN2` 레이어 L51의 `_______`를 `WINMAC`으로 교체.
  - 좌측 전용 선택 이유(오른쪽 반쪽에 GUI 키 없음, AG_TOGG 미사용) 주석 추가.
- **컴파일: 성공.** `.build/gkey_default.uf2`(84,480 bytes) 생성, 리포지토리 `firmware/gkey_default.uf2`에 반영.
- **Non-goals 준수:** 양쪽 스왑(AG_TOGG) 미사용, 오른쪽 R52 `KC_LALT` 이상치 미수정, via.json customKeycodes 미등록, Mac 레이어/LED 피드백 미추가.

## 진행 중 결정 (계획 대비 소소한 조정)
- **키코드 이름 `WINMAC`** — 계획 미리보기의 `KB_AGSWAP` 대신 사용. QMK 내장 `AG_*` 네임스페이스와의 혼동을 피하고 의미를 명확히 하기 위함. 동작 동일.
- **`eeconfig_update_keymap(&keymap_config)` (포인터 형)** — 설치된 QMK 헤더(`quantum/eeconfig.h`)가 신버전 시그니처 `void eeconfig_update_keymap(const keymap_config_t *)`였음. 계획에서 "버전에 따라 확인" 표시했던 부분을 실제 헤더로 확정.

## 막혔던 곳 (환경 divergence — 중요)
- **툴체인 파손.** brew `arm-none-eabi-gcc`가 16.1.0(GCC 16, newlib 미포함)으로 올라와, `qmk compile`이 `gkey.c` 첫 파일에서 `stdint.h: No such file or directory`로 실패. (내 코드 변경을 되돌린 상태에서도 동일하게 실패함을 확인 — 코드 무관, 순수 환경 문제.)
- **해결:** ARM 공식 툴체인 `gcc-arm-embedded` 15.2.rel1 캐스크 설치(sudo 필요해 사용자가 직접 설치) 후, `/Applications/ArmGNUToolchain/15.2.rel1/arm-none-eabi/bin`을 PATH 앞에 두고 컴파일 → 성공. brew 16.1.0은 제거하지 않음.
- 이는 기존 메모리 `qmk-arm-toolchain-broken`을 재확인·구체화함 (공식 툴체인 실제 설치 경로 확보).

## 검증 상태
- 소프트웨어 측(빌드) DoD: **충족** — `qmk compile -kb gkey -km default` 성공(공식 툴체인), `.uf2` 생성.
- 동작 측(S2, 하드웨어 UAT): **미완 — 사용자 플래싱·수동 확인 필요** (이 세션엔 하드웨어 없음). verified: pending.
