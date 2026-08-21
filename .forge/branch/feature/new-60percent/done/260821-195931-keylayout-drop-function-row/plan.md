<!-- forge-slug: keylayout-drop-function-row -->
<!-- task: 9 -->
<!-- tdd: off -->
<!-- priority: high -->
# 펑션 행을 없앤 5행 65% 배열을 설계하고 펌웨어에 반영한다

## Goal / Non-goals

- Goal: 물리 펑션 행을 제거해 반쪽당 6행 → 5행(총 88키 → 72키, 좌 30 / 우 42) 배열을 확정하고, 최상단 좌측 `` ` `` 자리를 `QK_GESC`로 바꾼다. 좌/우 분할본을 배열의 원천으로 세우고 통합본·README 인라인을 생성물로 내린 뒤, `gkey/` 펌웨어 5곳을 5행으로 재작성해 컴파일까지 통과시킨다.
- Non-goals:
  - 스위치 플레이트 DXF·FreeCAD 케이스·PCB 매트릭스는 손대지 않는다. 5행 실물 하드웨어는 별도 후속 작업이다.
  - `image/` 아래 이미지(배열 그림·배선도·써머리)는 재생성하지 않는다. 배선도는 5행 실물이 확정되기 전에는 정확해질 수 없으므로 낡음만 명시한다.
  - 내비 열(`Home`/`End`/`PgUp`/`PgDn`)·엄지 영역·가운데 `B`/`한/영`은 재배치하지 않는다. 펑션 행 제거 외의 배열 변경은 없다.
  - 레이어 구조(`_QWERTY`/`_FN1`/`_FN2`)와 그 내용은 행 삭제에 따른 시프트 외에 바꾸지 않는다.
  - `gkey/`를 리비전 구조(`rev1`/`rev2`)로 나누지 않는다. 6행 펌웨어는 `main` 브랜치와 git 히스토리에 남는다.

## Source of truth

- Glossary terms: **펑션 행**, **Fn 키**, **F1~F12**, **65% 배열** — `.forge/branch/feature/new-60percent/CONTEXT.md`
- Related ADRs:
  - `.forge/branch/feature/new-60percent/adr/260821-171943-drop-function-row-grave-as-esc.md` — 펑션 행 제거와 `QK_GESC`, `GRAVE_ESC_*` 예외 설정의 근거
  - `.forge/branch/feature/new-60percent/adr/260821-171944-split-halves-are-the-layout-source.md` — 좌/우 분할본을 원천으로 정한 근거와 8.25u 결합 규칙
- 확정된 배열 (그릴링에서 승인된 최종 모양):

```
R0  |ESC| 1 | 2 | 3 | 4 | 5 | 6 |        | 7 | 8 | 9 | 0 | - | = |  BSpc |Hom|
R1  | Tab | Q | W | E | R | T |        | Y | U | I | O | P | [ | ] |  \  |End|
R2  | Fn1  | A | S | D | F | G |        | H | J | K | L | ; | ' | Enter  |PgU|
R3  |  Shft  | Z | X | C | V | B |    | B | N | M | , | . | / | Shft | Up|PgD|
R4  |Ctl |Win |Alt |Fn2 | Space  |    |H/E|  Space   |Fn1|Ins|Del|Lft| Dn|Rgt|
```

  행별 열 수는 좌 `[7,6,6,6,5]`, 우 `[8,9,8,9,8]`. 우 반쪽은 5개 행 모두 9.75u로 폭이 같다.

- Definition of Done (각 항목은 열거된 사이트 전체를 가리킨다):
  1. `keylayout-left.json`·`keylayout-right.json`이 각각 5행이고, 키 수가 좌 30 / 우 42다.
     `python3 -c "..."` 로 두 파일의 줄 수 → **각 5** (착수 전 각 6).
  2. 최상단 좌측 첫 키 레전드가 `"~\nESC\n\n\`"` 다 — 위=`~`(Shift) / 아래=`ESC`(단독) / 우=`` ` ``(Fn1). 기존 숫자키 관용(`"!\n1\n\nF1"`)과 동형.
  3. `keylayout.json`이 `tools/gen_keylayout.py`의 생성물로 교체되고, `keylayout-with-function.json`이 삭제된다.
     `ls keylayout-with-function.json` → **없음** (착수 전 1개).
  4. `gkey/config.h`: `grep -c 'define MATRIX_ROWS 10'` → **1**, `grep -c 'MATRIX_ROW_PINS { GP0, GP1, GP2, GP3, GP4 }'` → **1**, `grep -c 'BOOTMAGIC_ROW_RIGHT     5'` → **1** (모두 착수 전 0).
  5. `gkey/config.h`: `grep -cE 'GRAVE_ESC_(ALT|CTRL)_OVERRIDE'` → **2** (착수 전 0). 그리고 `grep -cE 'GRAVE_ESC_(GUI|SHIFT)_OVERRIDE'` → **0** — 이 항목은 **회귀 가드**로, 착수 전에도 0이며 끝까지 0이어야 한다(GUI를 켜면 macOS `Cmd+\``를 잃고, SHIFT를 켜면 `~`를 잃는다).
  6. `gkey/gkey.h`의 `LAYOUT` 매크로 인자가 **72개**이고 매트릭스 초기화가 **10행**이다. 2u 키(Backspace·Enter·Space) 뒤 열을 `KC_NO`로 건너뛰는 기존 배선 패턴이 그대로 시프트돼야 한다 — 구 `{R10..R16, KC_NO, R17}` → 신 `{R00..R06, KC_NO, R07}` 꼴.
  7. `gkey/keyboard.json`의 `layouts.LAYOUT.layout` 항목 수가 **72** (착수 전 88).
  8. `gkey/keymaps/default/keymap.c`가 3개 레이어 × 5행이고 `grep -c 'QK_GESC'` → **1** (착수 전 0). `_FN1`의 최상단 첫 키는 `KC_GRV`를 유지한다(순수 백틱 경로 — 이게 없으면 배열이 성립하지 않는다).
  9. `gkey/via.json`: `grep -c '"rows": 10'` → **1** (착수 전 0), `layouts.keymap` 행 수 **5** (착수 전 6).
  10. `tools/verify_keylayout.py`가 존재하고 `python3 tools/verify_keylayout.py` 가 **exit 0**. 이 스크립트는 5곳 — `keylayout-left/right.json` · `keyboard.json` · `gkey.h` · `keymap.c` · `via.json` — 의 행·열·키 개수 일치를 검사한다.
  11. QMK 컴파일 통과:
      `cd ~/qmk_firmware && PATH="/Applications/ArmGNUToolchain/15.2.rel1/arm-none-eabi/bin:$PATH" qmk compile -kb gkey -km default` 가 **exit 0**.
      착수 전 6행 기준선으로 이 명령이 exit 0임을 이미 확인했으므로, 실패는 이번 변경 탓임이 확정된다. Homebrew의 `arm-none-eabi-gcc`는 newlib이 없어 쓸 수 없다 — PATH 지정이 필수다.
  12. `README.md`: 31~51행 인라인 KLE 데이터가 생성기 산출물로 교체되고, `grep -c '펑션키' README.md` → **0** (착수 전 1줄에 2회). 13행의 혼용 문장이 용어집 기준(**Fn 키** / **F1~F12**)으로 고쳐지고, `image/` 아래 배열 그림·배선도에 "6행 구배열 기준 — 5행 실물 확정 후 갱신" 주석이 붙는다.

## Work slices

- [ ] S1. `keylayout-left.json`·`keylayout-right.json`을 5행으로 재작성한다. 기존 행0(펑션 행)을 삭제하고, 구 행1의 `{y:0.25}` 갭(펑션 행과의 간격)을 제거하되 `a:4` 정렬은 유지한다. 좌측 첫 키를 `"~\nESC\n\n\`"` 로 바꾼다. 우측 각 행의 자체 `x` 오프셋(0.75 / 0.25 / 0.5 / 0 / 0)은 그대로 옮긴다 — 완료 기준: 두 파일 모두 5행이고 좌 30키 / 우 42키이며, 우 반쪽 5개 행의 폭이 모두 9.75u로 계산된다.
- [ ] S2. `tools/gen_keylayout.py`를 작성해 좌/우 분할본에서 통합본 `keylayout.json`과 README 인라인 블록을 생성한다. 결합 규칙은 우측 첫 키 앞 `x = 8.25 − 좌측행폭 + 우측행 자체 x`. `keylayout-with-function.json`을 삭제한다 — 완료 기준: 생성된 `keylayout.json`이 5행이고 각 행의 우측 첫 키 앞 `x`가 좌측 행폭에서 역산한 값과 일치하며, `keylayout-with-function.json`이 존재하지 않는다. (depends: S1)
- [ ] S3. `gkey/` 펌웨어 5곳을 5행으로 재작성한다 — `config.h`(`MATRIX_ROWS 10`, `MATRIX_ROW_PINS { GP0..GP4 }`, `BOOTMAGIC_ROW_RIGHT 5`, `GRAVE_ESC_ALT_OVERRIDE`·`GRAVE_ESC_CTRL_OVERRIDE` 추가), `gkey.h`(`LAYOUT` 매크로), `keyboard.json`(`layouts`), `keymaps/default/keymap.c`(3레이어, 최상단 좌측을 `QK_GESC`로), `via.json`(`rows: 10` + `keymap` 5행). GP5는 미사용으로 남고, 기존 `BOOTMAGIC_*` 주석은 새 좌표를 반영해 갱신한다 — 완료 기준: DoD 4~9가 모두 성립하고 `qmk compile -kb gkey -km default`가 exit 0. (depends: S1)
- [ ] S4. `tools/verify_keylayout.py`를 작성해 5곳의 행·열·키 개수 일치를 검사한다. `gkey.h`의 `LAYOUT` 매크로가 손으로 정의돼 있고 `keyboard.json`에 `matrix` 좌표가 없어 중복이 자동 해소되지 않으므로, 이 검사가 유일한 방어선이다 — 완료 기준: `python3 tools/verify_keylayout.py`가 exit 0이고, 어느 한 곳의 키를 일부러 하나 지우면 exit 0이 아니게 된다. (depends: S1, S3)
- [ ] S5. `README.md`를 갱신한다 — 31~51행 인라인 KLE를 S2 생성기 산출물로 교체, 13행의 "펑션키" 혼용 문장을 용어집 기준으로 재작성, `image/` 배열 그림·배선도에 낡음 주석 추가 — 완료 기준: `grep -c '펑션키' README.md` → 0, README 인라인 좌/우 블록이 각 5행, 이미지 참조 3곳에 주석이 붙어 있다. (depends: S2)
