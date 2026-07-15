<!-- forge-slug: keyboard-bottom-body -->
# 실행 기록 — 키보드 하단 body(케이스) 생성

> 2026-07-16 개정: 사용자 요청으로 상판을 4mm로 두껍게 하고(소음 저감), PCB에 밀착시키고(간격 0), body는 채결 역할로 단순화(상판이 body 위에 얹힘, lip recess 제거).

## 산출물
- `freecad/create_switch_plate.py` — `build_body(name, r)` + body 파라미터 + `build_all` 통합(body 생성·조립·export).
- `freecad/left_body.stl` / `.step`, `freecad/right_body.stl` / `.step`.
- `freecad/left_switch_plate.stl` / `.step`, `freecad/right_switch_plate.stl` / `.step` (두께 4mm로 재생성).
- `freecad/switch_plates.FCStd` — body(오렌지 반투명)+상판(파랑, 4mm)+PCB(초록) 조립 뷰(색상 포함).

## 계획대로 된 것 (현재 설계)
- 상판 두께 **4.0mm**(PLATE_T), 상판 바닥 = PCB 상면 **밀착**(PLATE_GAP=0).
- 좌·우 body 각 **단일 유효 솔리드**, 외부 높이 **17.0**, 벽·바닥 **3.0**.
- 계단형 캐비티(하부 shelf-inner → 상부 PCB포켓)로 PCB 선반 top **z=15**. lip recess 없음 — 상판은 body 상단 rim(z=17) **위에 얹힘**.
- 조립 스택: body z[0,17] · PCB z[15,17](최상단 선반 안착, 상면=rim) · 상판 z[17,21](PCB 위 밀착). 총 높이 **21mm**. 하단 캐비티 12mm(컨트롤러 여유).
- 4 코너 인서트 포스트(바닥 z=3 → top z=15) + Ø4.0 블라인드 홀(깊이 5.5, z9.5~15). 채결: 상판 상면 접시머리 → 나사 → PCB 코너홀 → body 포스트 인서트.
- body 외곽 = PCB 외곽 + (벽3 + 여유0.4), R5 (ADR-0003).

## 발산(Divergences)
1. **[중간] 설계 변경(이번 개정)**: 초기 계획(상판 1.5mm recess·상판-PCB 3.5mm 간격·lip 단턱 z15.5·선반 z10)에서, 사용자 요청으로 **상판 4mm·간격 0·상판 body 위에 얹힘**으로 전환. lip recess 제거, PCB 선반이 body 최상단(z15)으로 이동, 총 높이 17→21mm. plan.md의 DoD 일부(lip z=15.5·선반 z=10·PLATE_GAP 3.5)는 이 개정으로 대체됨.
2. **[중간] 검증 방법**: `Shape.isInside`/`section` 신뢰 불가 → **common 볼륨 프로브**로 확정 검증. 우측 body는 `.Shape`가 조립 오프셋(x+230) 적용 상태로 반환되므로 프로브 좌표에 +230 보정. 좌·우 동일하게 통과.
3. **[낮음] 상판 안착 rim/베젤 폭 얇음**: body가 plate보다 각 변 ~2mm만 크므로(ADR-0003) 상판이 얹히는 rim 폭이 좁다. 기능상 OK.
4. **[낮음] 색상은 MCP에서만 적용**: 스크립트는 색 미설정(freecadcmd는 색 손실), MCP(GUI)에서 색 입혀 저장. 스크립트 미변경.
5. **[낮음] 실행 방식**: 워크플로 생략, 메인 세션 직접 실행(단일 파일·순차 지오메트리·대화형 MCP 렌더).

## 비목표 준수
- USB/TRRS/컨트롤러 컷아웃 미포함(후속). FDM 공차 미세튜닝·나사 실물 모델링 없음. 파일명 유지.

## 검증(UAT)
- 수치(common 볼륨 프로브): 좌·우 상판 두께 4.0, 상판-PCB 간격 0.00, body 단일 유효 솔리드 H17·벽3·바닥3, PCB z[15,17]·상판 z[17,21], 4 인서트 포스트(Ø4 블라인드 5.5), 선반 z=15, floor SOLID·cavity VOID·post·insert-hole 정상.
- 시각: MCP 아이소메트릭 렌더로 두꺼운 파란 상판이 body(오렌지 반투명) 위에 얹히고 PCB(초록)가 그 아래 밀착된 조립 확인.
