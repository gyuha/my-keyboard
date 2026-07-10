<!-- forge-slug: rp2040-zero-split-firmware -->
<!-- task: 2 -->
<!-- tdd: off -->
# RP2040-Zero 분할 키보드 QMK 펌웨어 포팅 (VIA 포함)

## Goal / Non-goals
- Goal: 기존 `gkey/` QMK 키보드(ATmega32u4/Pro Micro 대상)를 RP2040-Zero 2개(좌우 각 1개)로 포팅한다. 최근 재배선된 6행 매트릭스(좌 6행×7열, 우 6행×9열)에 맞춰 매트릭스 핀·LAYOUT 매크로를 재정의하고, `keylayout-left.json`/`keylayout-right.json`의 새 레이아웃(ESC+F행, 양쪽 B키, 한/영 재배치, Caps→Fn 진입키)을 반영한 base 레이어를 새로 작성하며, 기존 FN1(방향키·미디어·기능키)·FN2(넘패드) 레이어 기능은 새 매트릭스 위치에 그대로 재배치한다. VIA 지원을 추가한다.
- Non-goals:
  - PCB 재설계(`pcb/*.epro`)
  - 파라메트릭 케이스 작업(다른 브랜치의 범위)
  - 리셋 스위치 물리 배선 유지 — RP2040-Zero 온보드 BOOTSEL 버튼으로 대체(기존 파츠리스트의 리셋 스위치는 이번 작업 범위 밖)
  - 2선 full-duplex 시리얼 전환 — 1선 half-duplex 유지 (ADR-0002)
  - RGB LED(GP16 온보드 WS2812)·인코더 등 사용하지 않는 기능 추가
  - GP26-29 예비 핀 활용(향후 확장용으로 비워둠)

## Source of truth
- Glossary terms: half(반쪽) — `.forge/CONTEXT.md`("각 반쪽은 독립된... 자체 RP2040 컨트롤러를 가지며, TRRS 시리얼로 연결된다")
- Related ADRs: `.forge/adr/0002-split-serial-half-duplex.md`(1선 half-duplex 선택 이유)
- 참고 자료(비-소스오브트루스, 레이아웃 범례용): `keylayout-left.json`/`keylayout-right.json`(새 6행 물리 키 배치·범례), `image/wiring-left.png`/`wiring-right.png`(새 6행 논리 행/열 연결)
- 확정된 GPIO 핀 배치:
  - Row pins(좌·우 공통, 6개): GP0 GP1 GP2 GP3 GP4 GP5
  - Left col pins(7개): GP6 GP7 GP8 GP9 GP10 GP11 GP12
  - Right col pins(9개): GP6 GP7 GP8 GP9 GP10 GP11 GP12 GP13 GP14
  - Serial(TRRS, half-duplex, 좌·우 공통): GP15
  - Diode direction: COL2ROW(기존 `gkey/config.h` 값 유지 가정 — 재배선 시 실제와 다르면 바로잡을 것)
- Definition of Done:
  - `gkey/rules.mk`: `MCU = RP2040`, `BOARD = GENERIC_RP_RP2040`, 적절한 `BOOTLOADER` 정의, `VIA_ENABLE = yes` 반영
  - `gkey/config.h`: 위 GPIO 핀 배치로 `MATRIX_ROW_PINS`/`MATRIX_COL_PINS`(좌·우 각각)·`SOFT_SERIAL_PIN GP15` 갱신
  - `gkey/gkey.h`의 `LAYOUT` 매크로가 좌 6행×7열/우 6행×9열 새 물리 키 배치를 반영
  - `gkey/keymaps/default/keymap.c`: `_QWERTY` 베이스 레이어가 `keylayout-left.json`/`keylayout-right.json` 범례(ESC+F행, 양쪽 B키, 한/영 재배치, Caps→Fn)를 따르고, 기존 `_FN1`/`_FN2` 레이어 기능이 새 위치에 보존됨
  - `qmk compile -kb gkey -km default` 성공, `.uf2` 산출물 생성 확인
  - `gkey/keymaps/via/` 또는 VIA Design 탭용 `via.json` 키보드 정의 작성, 매트릭스/레이어 수가 실제 키맵과 일치
  - (수동, 하드웨어 필요) 사용자가 실제 RP2040-Zero 2대에 플래싱 후 좌우 모든 키·레이어 전환 동작을 확인

## Work slices
- [ ] S1. `gkey/rules.mk`·`gkey/config.h`를 RP2040용으로 갱신 — MCU/BOARD/BOOTLOADER 설정, 확정된 GPIO 핀 배치로 매트릭스·시리얼 핀 정의, `VIA_ENABLE = yes` 추가 — 완료 기준: `qmk compile -kb gkey -km default`가 에러 없이 성공하고 `.uf2` 생성(이 시점 keymap.c는 임시로 매트릭스 크기만 맞춘 상태여도 무방)
- [ ] S2. `gkey/gkey.h`의 `LAYOUT` 매크로를 좌 6행×7열/우 6행×9열 새 매트릭스로 재정의 (depends: S1) — 완료 기준: 매크로 인자 개수가 새 물리 키 개수와 일치하고 컴파일 성공
- [ ] S3. `gkey/keymaps/default/keymap.c` 재작성 — `_QWERTY`는 `keylayout-left.json`/`keylayout-right.json` 범례를 따르고, `_FN1`·`_FN2`는 기존 기능을 새 위치에 재배치 (depends: S2) — 완료 기준: 3개 레이어 모두 새 `LAYOUT` 매크로 인자 개수와 일치, 컴파일 성공
- [ ] S4. VIA 지원 추가 — `via.json` 키보드 정의 작성(VIA 스펙 https://www.caniusevia.com/docs/specification 준수) (depends: S3) — 완료 기준: `via.json`의 매트릭스 크기·레이어 수가 실제 키맵과 일치, VIA 앱 Design 탭 로드 시 파싱 에러 없음
- [ ] S5. 최종 컴파일 확인 및 하드웨어 플래싱 안내 (depends: S4) — 완료 기준: `qmk compile` 최종 성공; 사용자가 실제 보드 2대에 플래싱 후 키 입력·레이어 전환을 확인(수동 UAT)
