# RUN — RP2040-Zero 분할 키보드 QMK 펌웨어 포팅 (VIA 포함) — 재실행 (2026-07-11)
slug: rp2040-zero-split-firmware

> 이 작업은 2026-07-05 실행·검증 후 2026-07-07 봉인 완료된 작업의 **의도적 재실행**이다.
> 활성 슬롯에 봉인본과 동일한 plan/run 잔재가 남아 있음을 fg-run 재실행 가드가 감지했고,
> 사용자가 중복 실행 경고를 확인한 뒤 재실행을 선택했다. 전회 run 기록은
> `done/2026-07-07-rp2040-zero-split-firmware/run.md`에 보존되어 있다.

## 실행 방식
전회와 동일하게 Dynamic Workflow 없이 이 세션에서 직접 실행. 사유: 슬라이스가 S1→S5 완전
순차 의존인 데다, 코드베이스가 이미 포팅 완료 상태여서 실제 작업은 "각 슬라이스 완료 기준
재검증 + 최종 컴파일"뿐 — 병렬 서브에이전트를 띄울 규모가 아님 (fg-run "Estimate cost first").

## Work slices 결과 (재검증)

### S1. rules.mk·config.h RP2040용 갱신 — **이미 충족, 재확인 완료**
`MCU = RP2040` / `BOARD = GENERIC_RP_RP2040` / `BOOTLOADER = rp2040` / `SERIAL_DRIVER = vendor` /
`VIA_ENABLE = yes`, `MATRIX_ROW_PINS {GP0..GP5}` / `MATRIX_COL_PINS {GP6..GP14}` /
`SERIAL_USART_TX_PIN GP15` 모두 계획의 DoD와 일치.

### S2. gkey.h LAYOUT 매크로 — **이미 충족, 재확인 완료**
LAYOUT 매크로 인자 88개 확인 (스크립트로 파싱 검증).

### S3. keymap.c 3개 레이어 — **이미 충족, 재확인 완료**
`_QWERTY` / `_FN1` / `_FN2` 3개 레이어 모두 LAYOUT 매크로 사용, 컴파일로 인자 수 정합 확인.

### S4. VIA 지원 — **이미 충족, 재확인 완료**
`via.json` matrix 12×9, 키 위치 매핑 88개 확인.

### S5. 최종 컴파일 — **성공**
- `qmk compile -kb gkey -km default` 성공. 산출물 `~/qmk_firmware/.build/gkey_default.uf2`
  (84,480 bytes — 전회와 동일 크기, 코드 무변경이므로 예상된 결과).
- **미완료(하드웨어 필요, 전회와 동일)**: 실제 RP2040-Zero 2대 플래싱·키 입력 확인은 사용자 몫.

## 계획과의 발산(divergence) 요약
1. **[낮음]** 코드 발산 없음 — 모든 슬라이스가 이미 완료 기준을 충족한 상태였고, 이번 재실행은
   재검증으로 수렴함. 파일 수정 0건.
2. **[낮음]** 컴파일 환경 재구축 필요 — 전회 `/tmp`에 추출했던 ARM 툴체인이 사라졌고, PATH의
   Homebrew formula(`arm-none-eabi-gcc` 16.1.0)는 여전히 newlib 누락으로 컴파일 불가.
   Homebrew 캐시에 남아 있던 cask pkg(`arm-gnu-toolchain-15.2.rel1`)를 `pkgutil --expand-full`로
   sudo 없이 스크래치패드에 추출해 해결 (전회와 같은 우회, 리포지토리에 잔여물 없음).
3. **[낮음]** QMK 경고 4건(`MANUFACTURER` 등 config.h 정의가 info.json 방식 대비 deprecated) 및
   "LAYOUT macro should not be defined within .h files" 경고 — 빌드는 성공하나 향후 QMK 버전에서
   깨질 수 있는 예고. 필요 시 별도 태스크로 keyboard.json 이전 검토.

## 다음 회고에서 다룰 만한 점
- fg-done 봉인 후 활성 슬롯이 비워지지 않아(또는 git으로 복원되어) "반쯤 봉인" 상태가 생겼음 —
  봉인 시 슬롯 비움이 커밋까지 이어졌는지 확인하는 습관 필요.
- 세션 외부 임시 설치물(/tmp 툴체인)은 재실행 시 반드시 사라져 있다고 가정해야 함 — Homebrew
  캐시의 pkg를 추출하는 우회가 재현 가능한 복구 경로로 두 번째 검증됨.
