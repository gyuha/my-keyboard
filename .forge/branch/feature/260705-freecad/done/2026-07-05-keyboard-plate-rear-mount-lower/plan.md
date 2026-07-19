<!-- forge-slug: keyboard-plate-rear-mount-lower -->
<!-- task: 1 -->
<!-- tdd: off -->
# keyboard-plate 뒷쪽 부품 받침 낮추기 + 노출 홀 위치 연동 조정

## Goal / Non-goals
- Goal: Fusion 360 `keyboard-plate v9`의 좌우 Body 뒷쪽에서 부품(RP2040·TRRS)을 케이스 바닥에 밀착시키도록 부품 받침을 낮추고, 그에 맞춰 뒷변 받침과 USB-C·TRRS 노출 홀을 조정한다. 기존 B-rep body를 직접 편집한다(소스 스크립트 부재).
- Non-goals:
  - 상판(LeftPlate/RightPlate) 수정 안 함
  - 인서트 보스(코너 원통 ⑥), 좌우 코너 기둥(⑤) 건드리지 않음
  - 스위치 컷아웃·케이스 외형·틸트 등 나머지 형상 불변
  - 파라메트릭 생성 스크립트 복원/재생성 안 함 (ADR-0001)

## Source of truth
- Glossary terms: keyboard-plate, Body, 부품 받침, 뒷변 받침, 부품 노출 홀 — `.forge/CONTEXT.md`
- Related ADRs: `.forge/adr/0001-brep-direct-edit-no-source.md` (소스 부재 → B-rep 직접 편집)
- 기준: 모든 높이는 케이스 내부 바닥면(FLOOR 상면 z=3mm) 위 돌출 높이. 단위 cm(Fusion API), print()로 출력.
- Definition of Done: 좌우 Body 모두에서 아래 목표 z가 측정으로 확인되고, `fusion/left-body.stl`·`fusion/right-body.stl`이 갱신됨.
  - 부품 받침(RP2040 패드 ① + TRRS 받침 ② + 앞 정렬 리브 ③) 상면 z=4mm (바닥 위 1mm 돌출)
  - 뒷변 받침 ④: 떠있는 하우징(z=6~10) 제거 후 바닥 위 3mm 돌기(z=3~6)로 재정의
  - USB-C·TRRS 노출 홀 중심 z=8 → 7mm (보드 1mm 하강에 연동, 1mm 내림)

## Work slices
- [ ] S1. LeftBody 수정: 부품 받침 ①②③ 상면 z=4로 낮춤, 뒷변 받침 ④를 바닥 위 3mm 돌기(z=3~6)로 재구성, USB-C·TRRS 홀 중심 z=7로 이동 — 완료 기준: LeftBody 측정에서 받침 상면 z≈4, ④ z범위≈3~6, 두 홀 중심 z≈7, body 유효(단일 solid)
- [ ] S2. RightBody에 미러 대칭으로 동일 적용 (depends: S1) — 완료 기준: RightBody 측정에서 S1과 동일한 목표 z 확인, body 유효
- [ ] S3. body STL 재출력 (depends: S2) — 완료 기준: `fusion/left-body.stl`, `fusion/right-body.stl` 파일 mtime 갱신 및 정상 export
