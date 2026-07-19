# RUN — keyboard-plate 뒷쪽 부품 받침 낮추기 + 노출 홀 위치 연동 조정
slug: keyboard-plate-rear-mount-lower

## 실행 방식
Dynamic Workflow가 아니라 이 세션에서 Fusion MCP(`execute_python`)로 직접 순차 편집. 사유: 단일 Fusion 문서 상태를 공유하는 S1→S2→S3 순차 의존 작업이라 병렬화 이득이 없고, 중간 측정·판단이 필요해 워크플로우의 무인 실행과 맞지 않음(fg-run "Estimate cost first" 지침).

## 계획 대비 실제 (사전 조건)
- **ADR-0001의 전제가 실제와 다름**: "파라메트릭 스크립트 소실 → B-rep 직접 편집만 가능"이라고 서술되어 있으나, 실제 Fusion 타임라인에는 `LeftBody_rp_pad`/`rp_brace`/`tr_pad`/`tr_brace`/`ports` 등 계획 라벨과 대응하는 **명명된 스케치+익스트루드 피처가 온전히 남아있었음**. 이번 작업은 이 피처들을 파라메트릭 편집(익스트루드 거리 값 변경)으로 처리해 B-rep 직접 절삭보다 안전하게 수행함.
- **LeftBody와 RightBody가 비대칭**: RightBody에는 LeftBody의 `tr_brace`(TRRS 앞 정렬 리브)에 대응하는 피처가 존재하지 않음(RightBody 타임라인이 `tr_pad`/돌출8에서 끝남). 기존부터 있던 비대칭이며 이번 편집으로 발생한 것 아님.

## Work slices 결과

### S1. LeftBody 수정
- ①RP2040 패드(`rp_pad`), ②TRRS 받침(`tr_pad`), ③앞 정렬 리브(`rp_brace`, `tr_brace`) 4개 익스트루드 거리를 편집해 상면 z=4mm로 통일 (패드 2mm→1mm, 리브 5mm→1mm distance). 측정 확인: 4개 모두 z=[3,4]mm. **[완료]**
  - 판단 필요 지점: 계획서가 "①+②+③ 상면 z=4mm"로 셋을 묶어 서술해 리브(당시 z=8mm)도 패드와 같은 높이로 낮춰야 하는지 불명확 → 사용자에게 확인, "리브도 z=4mm로" 답변 받아 적용.
- ④뒷변 받침(떠있는 하우징 z=6~10mm) 재구성: **미실행(발산)**. 실제 지오메트리를 얼굴 스캔·point containment 전수 조사(전체 footprint, lump 수=1)로 확인한 결과, 계획서가 서술하는 "떠있는 하우징(z=6~10mm)" 구조가 LeftBody 어디에도 존재하지 않음. plan.md 작성 시점의 관찰이 부정확했거나 이전에 이미 해소된 것으로 추정. 사용자에게 보고 후 "건너뛰고 나머지 진행" 결정 받음.
- USB-C·TRRS 노출 홀(`ports` 스케치의 원+사각형 프로파일) 중심 z 8→7mm 이동. `Sketch.move()`의 변환축이 (로컬X, 로컬Y=평면 내 V축, 평면법선) 순서라는 걸 모르고 처음에 벽 안쪽으로 1mm 밀리는 실수(법선 방향 이동)를 했다가 즉시 발견해 보정. 최종 측정: z=[4,10]mm, 중심 7mm, y위치 원복 확인. **[완료]**
- 완료 기준(body 유효/단일 solid) 충족: lumps=1, isValid=True.

### S2. RightBody 미러 적용
- `rp_pad`/`rp_brace`/`tr_pad` 3개(해당 프로젝트에 tr_brace 없음) 동일하게 z=4mm로 편집. **[완료]**
- 포트 홀 이동: LeftBody에서 쓴 보정값(법선 방향 되돌리기 포함)을 그대로 복사 적용하다 RightBody는 애초에 그 오류가 없었으므로 벽면법선 방향으로 +1mm 밀리는 새로운 실수 발생 → 즉시 감지해 재보정. 최종 측정: z=[4,10]mm 중심 7mm, y=12.8748(원위치) 확인. **[완료]**

### S3. STL 재출력
- `fusion/left-body.stl`(44,284 bytes), `fusion/right-body.stl`(42,684 bytes) 재출력 완료, mtime 갱신 확인. Fusion 문서(`keyboard-plate v9`)도 저장함. **[완료]**

## 계획과의 발산(divergence) 요약
1. **[낮음]** 실행 방식: ADR-0001의 "B-rep 직접 편집" 전제와 달리 대부분 파라메트릭 피처 편집으로 처리(더 안전한 방법으로 대체, 목표 수치는 동일하게 달성).
2. **[중간]** S1의 ④ 뒷변 받침 항목 미완료: 대상 구조를 찾지 못해 건너뜀. Definition of Done 중 이 항목만 미충족.
3. **[낮음]** RightBody에 tr_brace 미존재(기존부터 있던 비대칭, 이번 작업 범위 밖).
4. 좌우 모두 포트 홀 이동 중 축 해석 실수가 있었으나 즉시 측정으로 발견·보정함 — 최종 산출물에는 영향 없음.

## 다음 회고에서 다룰 만한 점
- plan.md 작성 시 Fusion 라이브 관찰 없이(또는 오래된 관찰로) 서술된 것으로 보이는 ④ 항목의 정확성 — 향후 plan 작성 시 이런 지오메트리 세부사항은 실측 후 기술하거나, 불확실하면 "확인 필요"로 명시하는 게 나을 수 있음.
- `Sketch.move()`의 Matrix3D.translation 축이 (로컬X, 로컬Y, 평면법선) 순서라는 점 — Fusion MCP 작업 시 재사용 가능한 지식.
