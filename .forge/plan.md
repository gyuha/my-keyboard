<!-- forge-slug: stab-slot-offset-plus-0-2 -->
<!-- task: 7 -->
<!-- priority: high -->
<!-- tdd: off -->
# 스테빌라이저 슬롯을 DXF 규격 위치에서 0.2 mm 상향

## 목표 / 제외 범위
- 목표: `StabCutoutYOffset`를 `-0.5 mm`에서 `+0.2 mm`로 바꿔 좌 4개·우 6개 총 10개 스테빌라이저 슬롯을 원본 DXF 규격 위치보다 0.2 mm 위(Y+)에 놓고, 파라메트릭 모델과 두 스위치 플레이트 STL을 갱신한다.
- 목표: 하우징 선장착 → 플레이트 아래에서 철사 후결합 순서로 스테빌라이저 5세트를 조립해 2u 키가 끝까지 눌리고 정상 복귀함을 확인한다.
- 제외 범위: 슬롯 폭·세로 길이(3.30 × 14.20 mm), 키별 개별 오프셋, 플레이트 두께(4.0 mm), 철사 통과 슬롯 추가, 언더사이드 클립 릴리프(`StabClipPlateThickness` / `StabClipLedgeWidth`), 키보드 바디·팜레스트 형상 및 해당 STL은 건드리지 않는다.

## 근거
- 용어: `.forge/CONTEXT.md`의 **스테빌라이저 슬롯**, **스테빌라이저 철사**
- 관련 ADR: `.forge/adr/260812-224138-stab-wire-under-plate-assembly-order.md` — 철사는 플레이트 아래로 지나가며, 통과 슬롯 대신 조립 순서로 확보한다
- 기준값: 원본 DXF(`freecad/left-switch.dxf`, `freecad/right-switch.dxf`) 실측 결과 10개 슬롯이 전부 스위치 중심 대비 X `±11.900 mm`, Y `-0.650 mm`, 크기 `3.30 × 14.20 mm`로 동일하다. `StabCutoutYOffset = 0`이 이 DXF 규격 위치이며 `+0.2`는 그보다 0.2 mm 위다. 적용 후 슬롯 중심은 스위치 중심 대비 Y `-0.45 mm`가 된다.
- 직전 이력: `task 6`(`lower-all-stabilizer-slots`)이 `-0.5`로 내렸으나 실물 검증에 실패했다. 실패 원인은 오프셋 값이 아니라 철사가 플레이트 위에 갇혀 있던 조립 문제였고, 원인은 ADR에 별도 기록했다. 이번 작업은 그 오프셋을 규격 기준으로 되돌리는 정정이다.
- 알려진 리스크: 0.2 mm는 FDM 출력 위치 오차(±0.1~0.2 mm)와 같은 자릿수다. 철사가 플레이트 아래로 빠진 지금은 여유 폭 안의 미세 조정이므로 임계값은 아니지만, 이 값 자체를 재현성 있는 기준으로 삼지 않는다.
- 완료 조건: `freecad/keyboard_parametric.FCStd`와 생성 스크립트가 `+0.2 mm` 기준으로 일치하고, 좌 4개·우 6개 슬롯 중심이 스위치 중심 대비 Y `-0.45 mm`이며, 두 스위치 플레이트 STL이 다시 내보내지고, 사용자가 실물에서 2u 키의 정상 동작을 확인한다.

## 작업 단위
- [ ] S1. `freecad/create_keyboard_parametric.py`의 `StabCutoutYOffset`을 `+0.2`로 바꾸고 `shrink_stab_slots` 독스트링을 갱신한다 — 완료 조건: 파라미터가 `0.2`이고, 독스트링이 (a) DXF가 슬롯을 스위치 중심 0.65 mm 아래에 둔다는 사실, (b) `+0.2`가 그 규격 위치에서 0.2 mm 위라는 것, (c) 철사는 플레이트 아래를 지나며 조립 순서로 확보한다는 ADR 참조를 담고, 기존의 "1.5 mm 하향으로 철사 간섭을 피한다"는 잘못된 근거 서술이 남아 있지 않다.
- [ ] S2. FreeCAD GUI에서 파라메트릭 문서를 재생성하고 변경된 두 스위치 플레이트만 STL로 내보낸다 — 완료 조건: `freecad/keyboard_parametric.FCStd`, `freecad/parametric_stl/left_switch_plate.stl`, `freecad/parametric_stl/right_switch_plate.stl`이 갱신되고 바디·팜레스트 STL은 변경되지 않는다. (depends: S1)
- [ ] S3. 완성된 FCStd의 슬롯 좌표를 원본 DXF와 대조한다 — 완료 조건: 좌 4개·우 6개 슬롯 중심이 각자의 스위치 중심 대비 Y `-0.45 ± 0.01 mm`, X `±11.900 ± 0.01 mm`이고 슬롯 폭·세로 길이가 각각 약 3.30 mm·14.20 mm로 유지됨을 읽기 전용 검사로 확인한다. (depends: S2)
- [ ] S4. 실물 검증 — 완료 조건: 하우징을 먼저 플레이트에 끼우고 플레이트 아래쪽에서 철사를 건 순서로 좌 2세트·우 3세트를 조립했을 때, 모든 2u 키가 끝까지 눌리고 손을 떼면 정상 복귀한다. (depends: S3)
