<!-- forge-slug: tilt-wedge-hollow-center -->
<!-- task: 18 -->
<!-- tdd: on -->
# 틸트 웨지 가운데를 비워 출력 시간·필라멘트를 줄인다

## 목표 / 비목표

- **목표:** 좌·우 [[틸트-웨지]]의 가운데를 상면(접착면)에서 파내되, 경사 밑면을 따라 **균일한 2mm 스킨**을 남긴다(사용자 결정 — 관통 아님). 겉 실루엣·정렬 핀·베드 접촉면은 그대로 유지해 서포트 0 출력성을 지킨다. 목표 절감은 웨지 부피 25% 이상(추정 ~33%, 좌우 합계 ~54cm³).
- **비목표:**
  - **팜레스트 경량화** — 별건. 사용자가 이전 그릴링을 드롭했다(2026-09-02). 다시 원하면 새 작업.
  - **`split keyboard.3mf` 갱신** — 사용자가 직접 한다(지난 작업들과 동일).
  - **상면 개구부 모서리 라운드** — 이미지의 라운드 윤곽은 주석으로 해석한다. YZ 단면 Pocket 방식이라 XY 모서리는 직각이 되며, 내부라 보이지 않고 출력에도 무관. 라운드가 필요해지면 별도 작업.
  - **`verify_no_support.py` 커버리지 확대(4/8 파트)** — 지난 회고 F3의 사각지대. 웨지는 이미 대상이라 이번 작업엔 충분하다.

## 원천

- **용어집:** [[틸트-웨지]], [[결합면]] — `.forge/CONTEXT.md`
- **관련 ADR:** `.forge/adr/260819-204944-tilt-wedge-as-separate-glued-part.md` — 웨지가 별도 접착 부품인 경위, 핀 정렬·출력 자세(경사 밑면을 베드에)의 원천
- **설계 결정(그릴링 합의):**
  - **파는 방식:** 웨지와 같은 관용구 — 안쪽으로 오프셋한 YZ 단면 쿼드를 Midplane 대칭 Pocket. 단면의 아랫변을 경사 밑면과 평행하게 2mm 위에 두면 스킨이 한 연산으로 균일하게 남는다. 윗변은 z_base+0.5로 상면을 뚫고 나가게 해 개구부를 깨끗이 연다.
  - **테두리 폭 (파라미터 신설):** X 양옆은 핀에서 유도 — `WedgeAlignPinInset(15) + 핀 반경(2) + 여유(3) = 20mm` (핀이 움직이면 따라간다). 앞뒤는 `WedgeHollowRimY = 12mm` (뒤 70° 슬랜트·R3 필렛 영역과 8mm 이상 거리). 스킨은 `WedgeHollowSkin = 2.0mm`. 기존 PARAMS·스프레드시트 표현식 관용구를 따른다.
  - **출력성 근거:** 스킨이 베드면이므로 베드 접촉 불변(기준 12278.1/16743.0mm²), 포켓 벽은 인쇄 자세에서 ~85° — 브리지·서포트 없음. 개구부가 위로 열려 천장도 없다.
  - **접착 영향:** 접착면이 테두리(12~20mm 링)로 줄지만 핀 2개 + 링 면적으로 충분. README 조립 안내만 한 줄 보정.
- **기준선 (2026-09-02 실측):** 부피 좌 68,538 / 우 93,450 mm³ · bbox 좌 144.1×90.8×10.2 / 우 196.5×90.8×10.2 mm (핀 1.3 포함)

- **완료 기준 (Definition of Done).** 아래 명령은 전부 저장소 루트에서 그대로 실행되며, 계획 작성 시점에 한 번씩 돌려 사전 상태를 기록했다.

  **회귀 가드 — 지금도 통과한다. 통과 유지가 정상이다:**
  1. `python3 freecad/verify_no_support.py` → 4파트 PASS, support 0.0 *(현재 통과. 웨지 bed 12278.1/16743.0 · bridged 0.0 이 유지돼야 한다 — 스킨이 베드면이라 불변이 정상)*
  2. `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD -c freecad/verify_magnet_pockets.py` → `All checks passed` *(현재 통과. 자석 포켓은 건드리지 않지만 전체 재생성이 다른 파트를 흔들지 않았다는 가드)*

  **전진 검사 — 지금은 실패한다. 실행 후 통과로 뒤집힌다:**
  3. `python3 freecad/verify_wedge_hollow.py` → 전항목 PASS, exit 0 *(파일이 없어 현재 실패. S1에서 작성 — 검사 항목은 S1 참조)*
  4. `grep -c '상단면 테두리' README.md` → `1` *(현재 0. S4가 254행 접착 안내를 보정한다. '상단면 테두리'라는 문구는 현재 README에 없어 0→1 이 이 슬라이스만의 몫이다)*
  5. 스크린샷 `image/freecad-iso.png`·`freecad-top.png` 재촬영(1760×1000, 기존 프레이밍 관례) 후 육안 확인 *(수동 항목 — 웨지 상면 개구부가 보이는지)*

## 작업 슬라이스

- [ ] **S1. `freecad/verify_wedge_hollow.py` 를 먼저 쓴다 (TDD red).** 지난 회고 교훈 6에 따라 FreeCAD 비의존 — STL 바이너리를 직접 읽는다(이 저장소의 부피·bbox 계산 방식 재사용). 검사 항목, 좌우 각각: ① bbox가 기준선(위 원천 참조)과 ±0.1mm 일치(겉 실루엣 불변) ② 핀 2개 존재 — 핀 중심 XY에서 z 최대값이 상면+1.3 ③ 홀로우 중앙 프로브에서 Z방향 재료 두께 = 스킨 2.0 ± 0.3mm ④ 부피 ≤ 기준선 × 0.75 — **완료 기준:** 현재 STL에 대해 ③·④가 FAIL로 보고되고 exit ≠ 0 (①·②는 현재도 참이어야 정상)
- [ ] **S2. `create_keyboard_parametric.py` 의 `build_tilt_wedge()` 에 홀로우 Pocket 을 추가한다.** PARAMS 신설(`WedgeHollowRimY`, `WedgeHollowSkin`; X 테두리는 핀 인셋에서 유도) + 내부 YZ 쿼드 스케치 + Midplane 대칭 Pocket. 스프레드시트 표현식 관용구 유지 — **완료 기준:** `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD -c freecad/create_keyboard_parametric.py` 가 오류 없이 완주 (depends: S1)
- [ ] **S3. GUI 재생성 + STL 8개 재수출 + 스크린샷 2장 재촬영.** 헤드리스 재생성 금지(GUI 데이터 파괴 — task 17 회고). MCP로는 `QTimer.singleShot` 예약 + 파일 플래그 관찰 패턴(~40초). 스크린샷은 `viewIsometric()`+`ViewFit`+`saveImage(1760×1000, White)` 관례 — **완료 기준:** DoD 1·2·3 전부 통과 + FCStd에 `GuiDocument.xml` 존재 (depends: S2)
- [ ] **S4. README 조립 안내 한 줄 보정.** 254행 "웨지 상단면에 접착제를 바르고" → 가운데가 비었으므로 "웨지 상단면 테두리에 접착제를 바르고"로 — **완료 기준:** DoD 4 (`grep -c` → 1)
