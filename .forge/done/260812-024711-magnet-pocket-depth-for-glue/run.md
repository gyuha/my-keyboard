# run — 자석 포켓 깊이를 접착제 부착 기준(2.2mm)으로 교정

slug: magnet-pocket-depth-for-glue · task: 5 · 실행일: 2026-08-12 · tdd: on

워크플로우를 쓰지 않고 직접 실행했다. S1→S4가 완전 직렬이고, S3·S4가 FreeCAD GUI MCP라는 단일 공유 자원을 요구해 병렬화 여지가 0이었다. 서브에이전트 팬아웃은 순수 오버헤드였을 것이다.

## 조각별 결과

- S1 헤드레스 검증 스크립트 `freecad/verify_magnet_pockets.py` 작성, 현재 모델에서 FAIL 확인 — ⚠ `sys.exit()`가 블록 버퍼 stdout을 비우지 않아 첫 실행에서 리포트 전체가 유실(exit 1만 남음). `say()` 헬퍼로 줄마다 명시적 플러시하도록 고쳤다.
- S2 `PARAMS["MagnetHoleDepth"]` 4.0 → 2.2, 주석 교정 — ⚠ 계획은 주석 1곳(`:54-58`)만 지목했으나, 보강 패드의 근거 주석(`:662-665`, "a 4mm pocket would breach the cavity")도 이 변경으로 거짓이 되어 함께 교정했다.
- S3 GUI(MCP)에서 `Parameters.B34` 4 → 2.2, recompute, 저장 — ✅ 계획대로. 포켓 4개 전부 2.2mm, 무효 객체 0, 6개 파트 ShapeColor 드리프트 0을 확인한 뒤에만 저장하도록 가드를 걸었다.
- S4 STL 4개 재내보내기 — ⚠ 계획에 없던 캘리브레이션을 먼저 넣었고, 계획에 없던 부작용이 하나 남았다(아래 참조).

## test-first가 실제로 값을 했다

S1 스크립트를 먼저 돌린 결과가 산술 예측과 정확히 일치해, 스크립트가 자재를 진짜로 재고 있다는 증거가 됐다.

| 항목 | 변경 전 실측 | 산술 예측 | 변경 후 실측 |
|---|---|---|---|
| 포켓 깊이 (원통 축방향 높이) | 4.0000mm | 2.2 | 2.2000mm |
| 바디 자석 뒷벽 잠여 | 2.0000mm (= 3.0+3.0−4.0) | 3.8 | 3.8000mm |

부수 확인: 실측 깊이가 `Pocket.Length`와 소수점까지 동일 → 스케치 평면이 결합면에 정확히 얹혀 있다. 기울어진 팜레스트 후면(웨지 틸트만큼 눕힌 면)도 마찬가지여서, 축 방향 측정과 Y축 측정이 갈리는 함정은 실재하지 않았다. 최종 실행은 22개 검사 전부 PASS, exit 0.

## 현장에서 내린 결정

- **워크플로우 미사용** (위 근거). fg-run의 "단일 에이전트로 충분한 규모면 건너뛴다" 조항.
- **저장 전 가드**: 포켓 길이·무효 객체·색상 드리프트를 먼저 검사하고, 하나라도 어긋나면 저장하지 않도록 했다. 메모리에 기록된 "헤드레스 저장 시 파트 색상 소실" 함정의 GUI판 방어.
- **STL 캘리브레이션**: 지난 커밋의 STL이 어떤 테셀레이션으로 나왔는지 스크립트에 기록이 없었다(내보내기 코드가 `create_keyboard_parametric.py`에 아예 없다). 그래서 **미변경 파트**인 `Left_Switch_Plate`를 임시 경로로 `Mesh.export`해 삼각형 수를 기존 커밋 파일과 비교했다 — 5960 = 5960 정확히 일치. 설정이 같음을 확인한 뒤에야 리포 파일을 덮었다.

## 미해결 — 사람의 판단이 필요함

**FCBak 회전.** FreeCAD 저장이 백업을 회전시켜, git이 추적 중이던 `freecad/keyboard_parametric.20260805-215727.FCBak`을 **삭제**하고 미추적 `freecad/keyboard_parametric.20260805-221333.FCBak`을 만들었다. 이 리포는 FCBak을 추적하는 상태다(`git ls-files`에 2개). 지난 커밋도 FCBak 교체를 그대로 커밋했으므로 같은 일이 저장마다 반복된다.

선택지: (a) 지난 커밋처럼 삭제+추가를 그대로 커밋, (b) `.gitignore`에 `*.FCBak`을 넣고 추적에서 빼기(1MB 바이너리가 저장마다 리포에 쌓이는 것을 막는다). 이번 작업 범위 밖이라 손대지 않았다.

## 산출물

- 수정: `freecad/create_keyboard_parametric.py` (PARAMS 1줄 + 주석 2곳)
- 수정: `freecad/keyboard_parametric.FCStd`
- 수정: `freecad/parametric_stl/{left,right}_palm_rest.stl`, `{left,right}_keyboard_body.stl`
- 신규: `freecad/verify_magnet_pockets.py`
- 불변(의도대로): `freecad/parametric_stl/{left,right}_switch_plate.stl`
- 커밋/PR은 계획의 비목표 — 하지 않았다.
