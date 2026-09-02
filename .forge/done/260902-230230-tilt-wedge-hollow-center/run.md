<!-- forge-slug: tilt-wedge-hollow-center -->
# RUN — 틸트 웨지 가운데를 비워 출력 시간·필라멘트를 줄인다

실행일: 2026-09-02

## 이 실행의 성격 — 워크플로우를 세우지 않았다

슬라이스 4개가 S1→S2→S3 직렬 체인(S4만 독립)이라 병렬화 여지가 없고 단일 에이전트
규모다. fg-run의 비용 제약에 따라 Dynamic Workflow 없이 이 세션에서 직접, TDD
순서(red→구현→green)로 처리했다. 서브에이전트를 띄우지 않았다.

## 슬라이스별 결과

- S1 `verify_wedge_hollow.py` 작성 (TDD red) — ✅ 계획대로. 현재 STL에서 ①bbox·②핀은
  PASS, ③스킨·④부피는 FAIL, exit 1 — 완료 기준 그대로
- S2 `build_tilt_wedge()` 홀로우 Pocket + PARAMS 2종 — ✅ 계획대로. 헤드리스 완주
  (기존 Midplane deprecation 경고만, 이번 변경과 무관)
- S3 GUI 재생성 + STL 8개 + 스크린샷 2장 — ✅ 계획대로 (QTimer 예약 패턴, ~40초).
  ⚠ DoD 5의 "개구부 육안 확인"은 조립 뷰에서 불가능 — 아래 어긋남 1 참조
- S4 README 254행 접착 안내 보정 — ✅ 계획대로 (`grep -c` 0→1)

## 계획과 실제의 어긋남

### 1. DoD 5의 괄호 기대("웨지 상면 개구부가 보이는지")는 조립 뷰에서 성립하지 않는다

스크린샷 관례(iso/top, 전 부품 조립 배치)에서 웨지 상면은 바디 바닥에 가려 개구부가
보이지 않는다. 프레이밍 관례 유지는 확인했고(원본과 동일한 배치·흑색 팜레스트 관례),
개구부 존재는 대신 **9점 프로브 격자**로 객관 확인했다: 홀로우 영역 9점 전부 재료
두께 2.01mm(스킨), 좌/우 테두리 5.47, 뒤 테두리 8.89(솔리드), 앞 테두리 2.02는
웨지 자체가 얇은 구간의 정상 솔리드 두께다. 다음에 DoD에 "육안" 항목을 넣을 때는
그 시점의 뷰에서 실제로 보이는지부터 따질 것.

### 2. 절감이 추정(~33%)보다 컸다 — 실측 좌 −35.1% / 우 −38.7%, 합계 −60.2cm³

162.0cm³ → 101.8cm³. 추정은 평균 깊이를 보수적으로 잡은 탓이고 방향은 유리한 쪽.

### 3. 그 외는 계획대로

헤드리스 S2 검증이 FCStd GUI 데이터를 지우는 것까지 계획의 시퀀스대로였고(S3 GUI
재생성이 권위본 복원 — zip 892엔트리, `GuiDocument.xml`·썸네일 존재, ShapeAppearance
126, `Wedge_Hollow` 피처 18엔트리), 되돌림은 git에 커밋된 이전 산출물로 가능하다.

## DoD 결과 (기준선 → 실행 후)

| # | 검사 | 기준선(승격 시점) | 실행 후 |
| --- | --- | --- | --- |
| 1 | `python3 freecad/verify_no_support.py` | 4파트 PASS (웨지 bed 12278.1/16743.0, bridged 0.0) | 4파트 PASS — **수치 완전 동일** (스킨이 베드면이라 불변이 정상, 회귀 가드) |
| 2 | `FreeCAD -c verify_magnet_pockets.py` | `All checks passed` | `All checks passed` — 변화 없음 (회귀 가드) |
| 3 | `python3 freecad/verify_wedge_hollow.py` | 파일 없음 → 작성 후 red: ③④ FAIL, exit 1 | **8/8 PASS, exit 0** (부피 좌 44,501 ≤ 51,404 · 우 57,311 ≤ 70,087) |
| 4 | `grep -c '상단면 테두리' README.md` | 0 | **1** |
| 5 | 스크린샷 재촬영 + 육안 | — | iso·top 재촬영(1760×1000, White), 프레이밍 관례 유지 확인. 개구부는 프로브 격자로 대체 확인(어긋남 1) |

## 이번 실행이 바꾼 파일

- `freecad/create_keyboard_parametric.py` — PARAMS `WedgeHollowRimY`(12)·`WedgeHollowSkin`(2.0) 추가, `build_tilt_wedge()`에 내부 YZ 쿼드 + Midplane Pocket (X 테두리는 핀 인셋에서 유도: 15+2+3=20mm)
- `freecad/verify_wedge_hollow.py` — 신규 (STL 직독, FreeCAD 비의존)
- `freecad/keyboard_parametric.FCStd` — GUI 재생성 (GUI 데이터 보존)
- `freecad/parametric_stl/*.stl` 8개 — 재수출 (웨지 2개만 형상 변화)
- `image/freecad-iso.png`, `image/freecad-top.png` — 재촬영
- `README.md` — 254행 접착 안내 한 줄

## 코드 리뷰

수행하지 않았다. 인증·데이터 변경·공개 API·마이그레이션에 닿지 않는 형상 스크립트
+ 검증 스크립트 변경이고 규모가 작다 (조건부 리뷰 기준 미달).

## 남은 것 (계획의 비목표 — 별도)

- `split keyboard.3mf` 갱신 — 사용자가 직접
- 팜레스트 경량화 — 드롭된 별건, 원하면 새 fg-ask
- 상면 개구부 모서리 라운드 — 필요해지면 별도 작업
