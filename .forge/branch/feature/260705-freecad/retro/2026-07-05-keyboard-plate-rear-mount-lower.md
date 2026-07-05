# 2026-07-05 — keyboard-plate 뒷쪽 부품 받침 낮추기 + 노출 홀 위치 연동 조정

## Plan vs actual
- What went as planned:
  - 좌우 Body 부품 받침(①RP2040 패드·②TRRS 받침·③앞 정렬 리브) 상면 z=4mm로 통일 — 측정 확인.
  - USB-C·TRRS 노출 홀 중심 z 8→7mm 이동 — 좌우 모두 측정 확인.
  - `fusion/left-body.stl`·`fusion/right-body.stl` 재출력 및 문서 저장.
- Divergences:
  - **[중간]** ④ 뒷변 받침(떠있는 하우징 z=6~10mm) 재구성이 미실행됨 — 실제 지오메트리를 전수 조사한 결과 계획서가 서술한 구조 자체가 존재하지 않았음. plan.md 작성 시점의 관찰이 부정확했거나 이미 해소된 것으로 추정. 사용자 승인을 받아 건너뜀.
  - **[낮음]** ADR-0001의 "B-rep 직접 편집만 가능" 전제와 달리, 대부분 명명된 파라메트릭 피처(`rp_pad`/`rp_brace`/`tr_pad`/`tr_brace`/`ports`)가 타임라인에 남아있어 그 피처 편집으로 더 안전하게 처리함.
  - **[낮음]** RightBody에 LeftBody의 `tr_brace`에 대응하는 피처가 없음(기존부터 있던 비대칭, 이번 작업 범위 밖).
  - 포트 홀 이동 중 `Sketch.move()`의 변환축 순서를 착각해 좌우 각각 다른 방향으로 1mm 밀리는 실수가 있었으나 즉시 측정으로 발견·보정 — 최종 산출물에는 영향 없음.

## Learnings
- Do differently next time:
  - plan.md에 지오메트리 세부사항(예: "떠있는 하우징 z=6~10mm")을 서술할 때는 Fusion 라이브 관찰로 확인 후 적거나, 불확실하면 "확인 필요"로 명시할 것 — 이번처럼 부정확한 서술이 DoD 항목 하나를 무효화시킬 수 있음.
  - Fusion `Sketch.move()`의 `Matrix3D.translation` 축 순서는 (로컬X, 로컬Y=평면 내 V축, 평면법선) — 다음에 유사 이동 작업 시 재확인 없이 바로 적용 가능.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none (ADR-0001에 "2026-07-05 개정" 노트 추가 — 소스 부재 전제는 유효하나, 범위 내 일부 피처는 파라메트릭 편집 가능함을 기록)
