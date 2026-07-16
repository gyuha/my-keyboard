# keyboard-plate (PCB 기반 세대)

분할 키보드 상판을 PCB 기준으로 재설계하는 브랜치. 손배선 시절 `switch.dxf`가 배열의 원천이었으나, 이제 PCB DXF export가 원천이다. 케이스 바디·하판·펌웨어 용어는 이전 세대 CONTEXT를 계승한다.

## Language

**상판 (switch plate)**:
스위치가 끼워지는 최상단 **4mm 판**(두껍게 — 소음 저감). PCB 상면에 바로 밀착하고(간격 0), body 위에 얹힌다. **원천이 `left-pcb.dxf`/`right-pcb.dxf`로 바뀌었다** — 키 위치는 PCB의 스위치 중심홀(Ø4)에서 추출하고, 외곽은 [[상판-외곽]] 규칙으로 생성한다. 이전 세대의 `switch.dxf` 기반 정의를 대체한다.
_Avoid_: 플레이트(단독), 탑플레이트

**상판 외곽 (plate outline)**:
**하단 body 외곽선과 동일하게** 도출한다 — PCB 외곽 bbox를 각 변 (PCB_CLEAR + WALL)만큼 확장하고 코너를 5R(BODY_CORNER_R)로 필렛한 둥근 사각. 상판과 body 가장자리가 flush해 **단차가 없다**. (초기 세대의 "키 배열에서 8mm 확장" 규칙(ADR-0002)은 이 결정으로 대체됨 — body보다 작아 단차가 생겼기 때문.)
_Avoid_: 케이스 외곽(별개), 스위치-중심 외곽(구세대)

**코너 보스 (corner boss)**:
상판 하면에서 코너 나사홀 주변만 국부적으로 두껍게 만든 돌기. 1.5mm 판에서 접시머리 카운터싱크 깊이를 확보하기 위한 것. 중앙부 홀에는 두지 않는다.
_Avoid_: 스탠드오프, 패드

**스위치 컷아웃 (switch cutout)**:
상판에서 MX 스위치가 통과하는 14.0mm 정사각 개구부. FDM 수축 보정을 위해 파라메트릭 오프셋으로 실개구부를 튜닝한다. 이번 세대는 노치를 포함하지 않는다.
_Avoid_: 스위치 홀

**컷아웃 오프셋 (cutout offset)**:
14.0mm 목표 개구부를 프린터별로 넓히거나 좁히는 파라미터. 스위치 물림을 맞춘다.

**스태빌라이저 홀 (stabilizer hole)**:
PCB 상의 Ø3 홀. 큰 키(스페이스바 등)의 스태빌라이저용이며 **나사홀이 아니다**. 상판·body 고정과 무관.
_Avoid_: 나사홀, 마운팅 홀

**코너 고정 홀 (corner mounting hole)**:
PCB 네 모퉁이의 원형 홀. 상판·PCB를 **하단 body에 고정**하는 용도. 지름은 PCB마다 다를 수 있다(좌 Ø5 / 우 Ø3.55). 지름이 아니라 보드 모퉁이 근접 위치로 식별하며, 상판의 코너 나사 위치와 일치한다.
_Avoid_: 스태빌라이저 홀

**하단 body (bottom body / case)**:
상판 아래에 오는 17mm 트레이형 케이스로, **채결(고정) 역할**을 한다. 바닥·벽 3mm. PCB를 최상단 선반(z=15)에 얹고, 상판(4mm)은 body 상단 rim(z=17) 위에 얹힌다(총 높이 21mm). 코너 인서트 포스트로 상판 나사를 받는다. 외곽은 PCB 외곽 기준으로 도출한다(ADR-0003). 좌·우 각 PCB에서 독립 생성.
_Avoid_: 하판, 베젤

**lip 단턱 (plate lip)** — *폐기*:
초기 세대에서 상판을 body 상단에 recess시키던 단턱. 현재 상판은 4mm로 두꺼워져 body 위에 얹히므로 lip 단턱은 **제거**됐다.
_Avoid_: 홈

**PCB 선반 (PCB shelf)**:
body 내벽에서 안쪽으로 돌출한 둘레 단. PCB가 여기 얹히고, 그 위 포켓(PCB 외곽+여유)이 PCB를 측면 고정한다. 현재 선반은 body **최상단(z=15)**에 있어 PCB 상면(z=17)이 rim과 flush하고, 그 위에 상판이 밀착(간격 0)한다. 사용자가 말한 "홈"이 이것.
_Avoid_: 홈(모호), 그루브

**인서트 포스트 (insert post)**:
body 코너에서 바닥부터 PCB 선반 높이까지 올라오는 기둥. 상단에 Spredsert M3X5 열융착 인서트를 매립해 상판 코너 나사를 받는다. 위치는 코너 고정 홀(=상판 코너 나사)과 일치한다. 상판의 [[코너 보스]](미적용)와는 다른, body 쪽 구조.
_Avoid_: 스탠드오프, 코너 보스

## Firmware (배선/펌웨어)

**배선 원천 (wiring source)**:
QMK 펌웨어의 키 매트릭스·핀 배치의 진실의 원천은 EasyEDA Pro 스키마(`pcb/split-keyboard.epro` 안 `SHEET/*.esch`)다. DXF는 넷 연결이 없고 README 핀 표는 낡았으므로 원천이 아니다(ADR 260716-15a). 기구(상판·body)의 배열 원천이 PCB DXF인 것과 구분된다 — 같은 `.epro`의 다른 export.
_Avoid_: DXF 배선, README 핀 표(파생 문서)

**키 매트릭스 (key matrix)**:
스위치를 스캔하는 논리적 행·열 격자. 물리적으로 **5행**(스키마 넷 ROW0~ROW4), 최대 **9열**(COL0~COL8), 다이오드 방향 COL2ROW. QMK에서는 분할이라 행이 두 배가 되어 `MATRIX_ROWS=10`(좌 rows0–4, 우 rows5–9), `MATRIX_COLS=9`. 좌측은 7열(COL0–6)만, 우측은 9열(COL0–8)을 쓴다.
_Avoid_: 6행(구세대 펌웨어 잔재), F키 전용 행

**ROW/COL 넷 (row/col net)**:
스키마에서 각 스위치를 GP핀에 잇는 넷 라벨. ROW0~ROW4는 행 스캔 핀, COL0~COL8은 열 판독 핀. 각 넷이 실제 어느 RP2040 GP핀인지는 스키마의 RP2040-Zero 모듈 핀↔넷 매핑에서 도출한다(README 핀 표가 아니라).

**시리얼 배선 (TRRS serial)**:
좌·우 보드를 잇는 TRRS 3.5mm 케이블의 데이터/전원 넷. 스키마 넷은 TX0·RX0·3V3·GND. README는 GP15 단선(half-duplex)이라 하나 스키마는 TX0·RX0 2선(full-duplex 가능성) — 실제 배선은 스키마에서 확정한다.
_Avoid_: GP15 단정(README 기준)

**가운데 B / 한영키 (middle B / Han-Yeong key)**:
분할 키보드 가운데에 추가한 키. 양쪽 안쪽에 B를 배치(한글 'ㅠ' 입력 편의), 우측 B 아래에 한/영키(스키마 지정자 `R.ALT`, 윈도우 한영=우Alt 매핑). README 도입부의 설계 의도가 이것.
