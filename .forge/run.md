# 실행 기록 — 스테빌라이저 슬롯을 DXF 규격 위치에서 0.2 mm 상향

## 작업 단위 결과
- S1 파라미터·독스트링 수정 — ✅ 계획대로: `StabCutoutYOffset`을 `-0.5`에서 `0.2`로 바꾸고, `shrink_stab_slots` 독스트링에서 "1.5 mm 하향으로 철사 간섭을 피한다"는 잘못된 근거를 지우고 DXF 규격 위치(0.65 mm 아래)·`+0.2`의 의미·철사가 플레이트 아래를 지난다는 ADR 참조로 교체했다.
- S2 GUI 재생성 및 플레이트 STL 내보내기 — ✅ 계획대로: `keyboard_parametric.FCStd`(23:01)와 좌·우 스위치 플레이트 STL(23:16)을 갱신했고, 바디·팜레스트 STL 4개는 02:43 그대로 유지됐다.
- S3 좌표 대조 — ⚠ 계획의 기준값 오류: 위치는 전부 통과했으나 계획이 세로 길이를 `14.20 mm`로 적었고 실제 모델값은 `14.10 mm`다.
- S4 실물 검증 — ⏳ 사용자 UAT 대기: 실제 부품 조립은 이 환경에서 수행할 수 없다.

## 계획과 실제 차이
- **계획의 S3 완료 조건에 잘못된 수치가 있었다.** 슬롯 세로 길이를 `약 14.20 mm`로 적었는데, 이는 원본 DXF의 값(14.201)이고 모델은 `StabCutoutHeight = 14.1`로 줄인다. 실측 14.100 mm가 정상이며, 계획을 쓸 때 DXF 값과 모델 값을 혼동한 것이다. 결과물에는 문제가 없고 계획의 기준값만 틀렸다.
- **Dynamic Workflow를 쓰지 않고 직접 실행했다.** 파라미터 1줄 + 독스트링 + 재생성 + 읽기 전용 검증 규모라 워크플로 오버헤드가 작업보다 컸다(fg-run의 비용 예외 조항).
- **FCStd 재생성과 STL 내보내기 사이에 사용자가 "STL이 안 바뀐 것 같다"고 지적했다.** 실제로 그 시점에는 FCStd만 갱신되고 STL은 `task 6` 시절 파일이었다. 지적이 정확했고, 두 단계 사이의 간격이 사용자에게 그대로 보였다.
- **`App.getDocument("Keyboard_Parametric")`이 실패했다.** 스크립트가 `saveAs`로 저장하면 문서 이름이 파일 basename인 `keyboard_parametric`으로 바뀐다. 생성 시 이름으로 조회하면 `NameError`가 난다.
- **셸 작업 디렉터리가 이전 `cd`로 옮겨져 상대 경로 조회가 한 번 실패했다.** 이후 절대 경로로 전환했다.
- FreeCAD가 백업을 순환시켜 `keyboard_parametric.20260805-221333.FCBak`이 사라지고 `keyboard_parametric.20260812-033404.FCBak`이 생겼다. 자동 동작이며 형상과 무관하다.

## 자동 검증
- `StabCutoutYOffset == 0.2`
- FCStd 상면 실측 — 좌 4개·우 6개 슬롯 전부: 스위치 중심 대비 `dX ±11.899~11.901`, `dY -0.450`, 폭 `3.299~3.301`, 세로 `14.100`
- 내보낸 `left_switch_plate.stl` 독립 검증 — 신규 슬롯 모서리 `Y 21.509 / 35.609` 존재, 이전 위치 `Y 20.809 / 34.909` 부재
- 변경 파일: `create_keyboard_parametric.py`, `keyboard_parametric.FCStd`, `parametric_stl/left_switch_plate.stl`(298,084 B), `parametric_stl/right_switch_plate.stl`(315,684 B). 바디·팜레스트 STL 미변경.
