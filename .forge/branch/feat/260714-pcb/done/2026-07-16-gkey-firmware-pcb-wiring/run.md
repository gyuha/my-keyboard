<!-- forge-slug: gkey-firmware-pcb-wiring -->
# 실행 기록 — gkey 펌웨어를 v3 PCB 스키마 배선에 맞춰 업데이트

## 산출물
- `gkey/config.h` — `MATRIX_ROWS 10`, ROW 핀 `{GP2..GP6}`, COL 핀 `{GP7..GP15}`, `COL2ROW`, 시리얼 full-duplex(`SERIAL_USART_FULL_DUPLEX` + TX=GP0/RX=GP1).
- `gkey/gkey.h` — 5행 LAYOUT 매크로(좌 rows0–4/cols0–6, 우 rows5–9/cols0–8, 갭 KC_NO) + 10×9 매트릭스 초기화.
- `gkey/keymaps/default/keymap.c` — 3레이어(_QWERTY/_FN1/_FN2) 재구성, WINMAC·DP_SLEP 보존.
- `gkey/keyboard.json`, `gkey/via.json` — 73키 레이아웃, 매트릭스 10×9로 갱신.
- `README.md` — 핀 표·시리얼 설명 스키마 기준 정정.
- (도구, scratchpad) `extract_wiring.py`(스키마 넷 추출기), `gen_firmware.py`(파일 생성기), `wiring.json`(확정 배선 표).

## 계획대로 된 것
- **S1 스키마 넷 추출**: `pcb/split-keyboard.epro`를 파싱(부품 배치 변환→절대 핀 좌표→와이어/넷라벨 union-find→다이오드 트레이싱)해 좌30·우43=73 스위치의 (ROW,COL), GP핀↔넷, TRRS 배선을 도출. **자기정합 통과**(미해결 0·중복 셀 0, 좌우 GP 매핑 동일).
- **S2~S6**: 단일 생성기(`gen_firmware.py`)로 파일을 일관 생성 → spec↔스키마 정합 OK.
- **S7 검증**: 파일 간 정합성(keyboard.json·gkey.h·via.json·keymap.c 3레이어 전부 73셀·10×9·완전 일치, 중복/누락 0) + `qmk compile -kb gkey -km default` **성공**(`gkey_default.uf2` 83968B 생성, ARM 15.2.rel1).

## 발산(Divergences)
1. **[중간] 실행 방식**: 계획은 fg-run Dynamic Workflow였으나, 직렬 의존 체인(S1이 전부 게이트)·정확성-critical·파일 간 강결합이라 **메인 세션 직접 처리**(fg-run 소규모 허용). 워크플로 스크립트 승인 벽 없음.
2. **[높음·핵심] 실제 배선이 README/구펌웨어와 전면 상이 — 스키마 기준으로 전면 교정**:
   - ROW0~4 = **GP2~GP6**(구: GP0~GP5), COL0~8 = **GP7~GP15**(구: GP6~GP14).
   - 시리얼 = **GP0(TX0)/GP1(RX0) full-duplex**(구: GP15 half-duplex).
   - 전원 = TRRS **3V3**(구 README: 5V).
   - `MATRIX_ROWS` **12→10**(6행→5행). F키 전용 최상단 행 제거, F키는 레이어(Fn+숫자)로만.
3. **[중간·하드웨어 검증 필요] full-duplex 크로싱**: 스키마가 좌·우 모두 conductor를 TX0/RX0로 straight-through 라벨. full-duplex UART는 한쪽 TX↔반대쪽 RX가 교차해야 동작 — 케이블/PCB에서 실제 교차하는지 **실물 테스트로 확인 필요**. 미교차 시 크로스오버 케이블 또는 TX/RX 핀 스왑이 필요할 수 있음. (스키마가 원천이라 그대로 반영; firmware는 TX=GP0/RX=GP1.)
4. **[중간] PCB 실크스크린 designator ≠ README KLE 일부**: 우측 하단행에 PCB는 **Ins**(README KLE엔 Alt) → 물리 라벨(PCB) 우선해 `KC_INS`. 셀 갭 2곳(우 row7 c7, row9 c2)=KC_NO. **"6"·"B"가 좌·우 중복**(가운데 키 설계).
5. **[낮음] 키맵 이식**: 베이스는 PCB designator(≈README KLE), _FN1/_FN2·WINMAC·DP_SLEP은 **의미 키(designator) 기준으로 구 keymap에서 이식**. 좌측은 행 이동으로 정연히, 우측은 구조 변화(열 삽입)로 designator 매칭 이식. 신규 키 우측"6"→F6/KP6(좌"6"과 동일), "Ins"→FN 투명.

## 비목표 준수
- 실물 플래시·타이핑 테스트 없음(보드 없음). FreeCAD·PCB 재설계 미변경. 키맵 기능 추가 없음.

## 검증(UAT)
- 정합성: keyboard.json 73 · gkey.h LAYOUT 73/매트릭스 10×9 73셀(중복0·누락0) · via.json 73셀·dims10×9(gkey.h와 완전 일치) · keymap.c 3레이어 각 73.
- 빌드: `qmk compile -kb gkey -km default` → `gkey_default.uf2`(83968B) 생성.
- **한계**: 컴파일+정합성까지만(합의된 기준). 실제 키 입력·시리얼 링크는 하드웨어 검증 필요(특히 발산 #3).
