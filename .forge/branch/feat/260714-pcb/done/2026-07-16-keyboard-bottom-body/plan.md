<!-- forge-slug: keyboard-bottom-body -->
<!-- task: 6 -->
<!-- tdd: off -->
# 키보드 하단 body(케이스) 생성

## 목표 (Goal)

좌·우 PCB DXF 기준으로 3D 프린트용 하단 케이스를 생성한다. 외부 높이 **17mm**, 바닥·벽 **3mm**. 상판을 상단 **lip 단턱**에 recess시켜 윗면 flush로 받고, PCB를 **둘레 선반**에 얹으며, 4 코너 **인서트 포스트**(Spredsert M3X5 열융착, 파일럿 Ø4.0)로 상판 코너 나사를 받는다. 좌·우 독립 생성.

## 원천 (Source of truth)

- ADR-0001 (PCB DXF 원천 좌표계), **ADR-0003** (body 외곽 = PCB 외곽 기준)
- 용어: CONTEXT.md — 하단 body, lip 단턱, PCB 선반, 인서트 포스트, 코너 고정 홀
- 기존 코드: `freecad/create_switch_plate.py` — `extract()`·`_rounded_rect()`·코너홀 추출 재사용

### Z 스택 (body 좌표, floor 밑면 z=0)

```
z=17   벽 상단 = 상판 윗면 (flush)
z=15.5 lip 단턱 (상판 바닥)      ┐ 상판 z[15.5,17]
z=12   PCB 상면                  ┘ 상판-PCB 간격 3.5 (MX plate-mount)
z=10   PCB 선반·포스트 top        PCB z[10,12]
z=3    바닥 top                  ┐ 하단 캐비티 7mm
z=0    바닥 밑면                 ┘ 바닥 3mm
```

### 파라미터

`BODY_H=17, WALL=3, FLOOR=3, PLATE_GAP=3.5, PCB_T=2, PLATE_T=1.5, LIP_CLEAR=0.3, PCB_CLEAR=0.4, SHELF_W=2.0, POST_OD=7.0, INSERT_HOLE_D=4.0, INSERT_HOLE_DEPTH=5.5, BODY_CORNER_R=5.0`

### 완료 정의 (Definition of Done)

- 좌·우 body 각 **단일 유효 솔리드**.
- 외부 높이 **17.0**, 벽·바닥 **3.0** 측정 확인.
- 4 코너 인서트홀 **Ø4.0**, 깊이 **5.5 블라인드**, 위치 = 코너 고정 홀과 일치.
- PCB 포켓이 PCB 외곽 수용(각 변 여유 ≥0), 선반 top **z=10**.
- lip 단턱 **z=15.5**, 상판 외곽(+여유)이 lip 개구에 들어감, lip 깊이 1.5.
- `left_body.stl/.step`, `right_body.stl/.step` export, FCStd 조립뷰(body+상판+PCB 중첩).

## 작업 슬라이스 (Work slices)

- **S1. `build_body(name)` 골격.** `extract()`로 PCB 외곽·코너홀 취득 → 외벽(PCB외곽 + WALL + PCB_CLEAR, R5) 솔리드 → 내부 캐비티(벽 3·바닥 3) cut. _완료기준_: 좌우 셸 솔리드, 외부높이 17·벽/바닥 3 측정.
- **S2. lip 단턱 + 상판 recess.** (depends: S1) 상단 z15.5~17 내벽을 상판외곽 + LIP_CLEAR 로 넓혀 lip 생성. _완료기준_: 상판 외곽이 lip 개구에 들어감, lip 깊이 1.5.
- **S3. PCB 선반 + 포켓.** (depends: S1) z=10에 둘레 선반(내벽에서 SHELF_W 안쪽), z10~15.5 포켓 = PCB외곽 + PCB_CLEAR. _완료기준_: PCB 외곽이 포켓 수용, 선반 top z=10.
- **S4. 코너 인서트 포스트.** (depends: S1) 코너홀 (x,y)에 OD 7 기둥 z3~10, 상단에서 Ø4.0 블라인드 홀 깊이 5.5. _완료기준_: 4 포스트, 홀 Ø4.0·깊이 5.5, 위치=코너 고정 홀 일치.
- **S5. `build_all` 통합 + 배치 + export.** (depends: S1–S4) build_all에 body 추가, 조립 Z 배치 갱신(PCB z[10,12]·상판 z[15.5,17]·body z[0,17]) — 조립뷰만 바뀌고 상판 STL/STEP은 원점 빌드라 불변. left/right_body.stl/.step export, FCStd 저장. _완료기준_: 4 파일 export, 조립뷰 중첩 정상.
- **S6. MCP 색상 + 검증 렌더.** (depends: S5) MCP(GUI)에서 색 입혀 저장, DoD 수치 + 렌더 검증. _완료기준_: DoD 수치 통과, 렌더로 lip·선반·포스트·PCB 안착 확인.

## 비목표 (Non-goals)

- **USB/USB-C 컷아웃, TRRS 잭 홀, 컨트롤러(RP2040-Zero) 마운트** — 후속 태스크(위치·방향 정보 확정 후).
- 상판·PCB 재설계 — 이미 봉인됨(task 5). 이번은 body만 신규.
- FDM 공차 미세튜닝 — 시험 출력 후 별도.
- 나사·인서트 실물 모델링 — 홀만 생성.
- 파일명 변경 — `create_switch_plate.py` 유지(churn 회피).
