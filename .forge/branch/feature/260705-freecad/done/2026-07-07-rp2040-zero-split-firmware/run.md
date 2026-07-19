# RUN — RP2040-Zero 분할 키보드 QMK 펌웨어 포팅 (VIA 포함)
slug: rp2040-zero-split-firmware

## 실행 방식
Dynamic Workflow가 아니라 이 세션에서 직접 순차 편집. 사유: 슬라이스가 S1→S2→S3→S4→S5 완전 순차 의존이고, 여러 파일(config.h/rules.mk/gkey.h/keymap.c) 간 정합성(매트릭스 핀 수·LAYOUT 인자 수)이 정확히 일치해야 해서 병렬 서브에이전트로 나누면 오히려 불일치 위험이 커짐(fg-run "Estimate cost first" 지침).

## 컴파일 검증 환경 구축 (계획에 없던 선행 작업)
이 세션에는 QMK CLI·`qmk_firmware`·ARM 툴체인이 전혀 없어 `qmk compile`을 바로 돌릴 수 없었음. 사용자에게 "지금 설치해서 직접 검증" vs "파일만 작성, 컴파일은 사용자 몫" 중 선택받아 **직접 검증**으로 진행:
- `pip install qmk` (QMK CLI)
- `qmk_firmware` 저장소 clone(`--depth 1`) + 필요한 서브모듈만 초기화(`lib/chibios`, `lib/chibios-contrib`, `lib/pico-sdk`, `lib/printf`, 이후 빠진 `lib/lufa` 추가)
- `arm-none-eabi-gcc`: Homebrew formula(`brew install arm-none-eabi-gcc`)는 newlib(`stdint.h` 등 표준 헤더)가 빠져 있어 컴파일 실패 — Homebrew cask(`gcc-arm-embedded`)는 시스템 설치라 sudo 필요(이 환경에서 불가) → 이미 다운로드된 cask의 `.pkg`를 `pkgutil --expand`+`cpio`로 sudo 없이 직접 풀어서 `/tmp/arm-toolchain-payload`에 완전한 툴체인 확보
- 이 환경 한정 임시 설치물이며 리포지토리에는 아무것도 남기지 않음. 사용자의 평소 개발 머신에는 README에 문서화된 대로 이미 `qmk_firmware`가 준비되어 있을 가능성이 높음.

## Work slices 결과

### S1. rules.mk·config.h RP2040용 갱신 — **완료**
- `rules.mk`: `MCU = atmega32u4` → `MCU = RP2040` + `BOARD = GENERIC_RP_RP2040`, `BOOTLOADER = atmel-dfu` → `BOOTLOADER = rp2040`, `SERIAL_DRIVER = vendor` 추가, `VIA_ENABLE = yes` 추가.
- `config.h`: `MATRIX_ROWS 10`→`12`, 확정된 GPIO로 `MATRIX_ROW_PINS`(GP0-GP5)·`MATRIX_COL_PINS`(GP6-GP14) 갱신, `SOFT_SERIAL_PIN` 제거 후 `SERIAL_USART_TX_PIN GP15`로 교체.
- **발산**: 계획에는 `SOFT_SERIAL_PIN` 방식으로 적었으나, 실제 컴파일/QMK 공식 문서 확인 결과 RP2040에서는 `SOFT_SERIAL_PIN`이 인식되지 않고(`SERIAL_USART_TX_PIN` 사용) `SERIAL_DRIVER = vendor`(PIO 기반) 조합이 필요함을 발견 — ADR-0002를 이 사실로 정정함.
- **발산**: `BOOTLOADER = rp2040` 필요, `BOARD = GENERIC_RP_RP2040` 미지정 시 Pro Micro RP2040 핀맵으로 기본 설정된다는 점을 컴파일 에러로 확인.
- **발산**: 최신 QMK CLI는 `info.json`이 아닌 `keyboard.json` 파일명만 키보드로 인식함(글롭 패턴 확인) — 기존 `gkey/info.json`을 `keyboard.json`으로 이름 변경하고, 새 LAYOUT 매크로(88개 인자: L00-L54/R00-R57)에 맞춰 좌표 목록도 재작성. (계획에는 없던 필수 작업)

### S2. gkey.h LAYOUT 매크로 재정의 — **완료**
좌 6행(7,7,6,6,6,5열)·우 6행(9,8,9,8,9,8열) 새 매트릭스로 재작성, 12×9 배열에 `KC_NO` 패딩. 컴파일 성공으로 인자 개수 정합성 확인.

### S3. keymap.c 재작성 — **완료**
- 베이스(`_QWERTY`) 레이어: `keylayout-left.json`/`keylayout-right.json`의 범례를 문자 그대로 옮김. F1~F6/Mute/Sleep 등이 이제 전용 물리 키가 되어 base 레이어 리터럴로 이동.
- `_FN1`/`_FN2` 레이어: "새로 삽입된 행0(F행)을 제외한 나머지 행은 구 레이아웃에서 행 번호만 +1씩 밀린 것과 정확히 일치"함을 발견(모든 행의 열 개수가 완벽히 대응) → 이 규칙으로 구 FN1/FN2 콘텐츠를 그대로 이식(기능 유지 요구사항 충족). 새로 생긴 행0은 전부 transparent 처리(F키류가 이미 base에 있어 오버레이 불필요).
- **판단이 필요했던 범례 해석**(런타임 확인 불가, 범례 텍스트만으로 추정 — 사용자 검토 필요):
  - 우측 base row0의 "SCR" → `KC_SCRL`(Scroll Lock)로 해석. Print Screen일 수도 있음.
  - 좌측 base row1 col0의 새 backtick(`) 키 → `KC_GRV`로 해석(구 레이아웃엔 이 위치에 키가 없었음, ESC가 새 row0으로 옮겨가며 생긴 자리).
  - 우측 base row5: 범례가 "한/영"·"Alt" 두 개의 서로 다른 키로 분리되어 있음(구 키맵은 `KC_RALT` 하나만 있었음) → "한/영"=`KC_RALT`(기존 관례 유지), 신규 "Alt"=`KC_LALT`로 배정.
  - 오타로 보이는 부분: 구 `keymap.c`의 우측 숫자행에 `KC_6`이 좌우 양쪽에 중복 출현(L06=R00=6)하는 버그가 있었는데, 새 범례 기반으로 다시 작성하며 자연히 해소됨(고치려 한 것이 아니라 새로 씀).
- 작성 중 실수: `_FN2` 마지막 줄(우측 row5)에서 인자 하나를 빠뜨려 `LAYOUT: requires 88 arguments, but only 87 given` 컴파일 에러 발생 → 즉시 발견해 수정.

### S4. VIA 지원 — **완료**
`gkey/via.json` 작성(matrix 12×9, 88개 키 위치 매핑, vendorId/productId는 `config.h`와 동일하게 0xFEED/0x4445). VIA 앱 공식 스펙 문서 기준으로 최소 구조 구성. `VIA_ENABLE = yes` 포함 컴파일 성공(`quantum/via.c` 정상 빌드).

### S5. 최종 컴파일 확인 — **부분 완료**
- `qmk compile -kb gkey -km default` **성공**. 산출물: `~/qmk_firmware/.build/gkey_default.uf2`(84,480 bytes).
- **미완료(하드웨어 필요)**: 실제 RP2040-Zero 2대에 플래싱 후 좌우 키 입력·레이어 전환 확인은 사용자가 직접 해야 함 — 이 세션에는 물리 하드웨어가 없음.

## 계획과의 발산(divergence) 요약
1. **[낮음]** 컴파일 검증을 위해 QMK 툴체인 전체(CLI·저장소·ARM GCC)를 이 세션에 새로 설치해야 했음(계획에는 예상되지 않았던 선행 작업). Homebrew의 `arm-none-eabi-gcc` formula가 newlib를 포함하지 않아 cask의 pkg를 sudo 없이 직접 추출하는 우회가 필요했음.
2. **[중간]** RP2040 분할 시리얼 설정이 계획 초안(`SOFT_SERIAL_PIN`)과 실제 필요 설정(`SERIAL_DRIVER=vendor` + `SERIAL_USART_TX_PIN`)이 달랐음 — ADR-0002 정정.
3. **[낮음]** `info.json`→`keyboard.json` 파일명 변경이 최신 QMK CLI에서 필수임을 컴파일 에러로 발견(계획에 없던 항목).
4. **[중간]** 새 6행 레이아웃의 일부 범례(SCR, 신규 backtick, 한/영·Alt 분리)는 명확한 근거 없이 문맥상 합리적으로 해석함 — 실제 사용자 의도와 다를 수 있어 하드웨어 테스트 시 확인 필요.
5. **[낮음]** `_QWERTY`/`_FN1`/`_FN2` 3개 레이어 모두 정확히 88개 인자로 컴파일 성공 — 작성 중 1건의 인자 누락 실수는 즉시 컴파일 에러로 잡아 수정함.

## 다음 회고에서 다룰 만한 점
- "새 물리 행이 위에 삽입되면 나머지 행은 정확히 +1 shift되고 열 개수도 그대로 대응한다"는 패턴을 발견해 FN1/FN2 이식에 활용함 — 유사한 레이아웃 개정 작업에서 재사용 가능한 방법론.
- RP2040 관련 QMK 설정(BOARD/BOOTLOADER/SERIAL_DRIVER)은 실제로 컴파일해보기 전에는 문서만으로 확신하기 어려운 부분이 있었음 — 공식 문서가 답을 주지 못한 지점(half-duplex 정확한 매크로)은 결국 컴파일 에러 메시지가 가장 정확한 근거였음.
- 범례 텍스트만으로 키맵 의도를 완전히 복원하기 어려운 지점이 여럿 있었음 — 향후 레이아웃 변경 시 애매한 키는 legend에 주석을 남기거나 사용자에게 직접 확인하는 편이 나을 수 있음.
