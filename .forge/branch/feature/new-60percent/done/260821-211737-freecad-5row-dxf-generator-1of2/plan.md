<!-- forge-slug: freecad-5row-dxf-generator-1of2 -->
<!-- task: 10 -->
<!-- part: 1/2 -->
<!-- tdd: on -->
<!-- priority: high -->
# KLE에서 DXF를 생성해 배열 원천을 하나로 만든다 (FreeCAD 불필요)

## Goal / Non-goals

- Goal: 좌/우 KLE 분할본에서 스위치 플레이트 DXF를 생성하는 생성기를 만들고, 구 6행 KLE로 생성한 결과가 원본 6행 DXF와 일치함을 회귀 테스트로 증명한 뒤, 5행 DXF를 생성해 `freecad/left-switch.dxf`·`right-switch.dxf`를 교체한다. 순수 Python으로 끝나며 FreeCAD가 필요 없다.
- Non-goals:
  - FCStd 재생성·STL 내보내기·서포트/자석 검증은 하지 않는다. FreeCAD GUI 모드가 필요하므로 **2of2**가 담당한다.
  - 낡은 갈래(`create_keyboard_plates.py` · `keyboard_switch_plates.FCStd` · `create_techdraw_sheets.py`)는 손대지 않는다. 낡음 주석만 단다. 정리는 별개 관심사다.
  - `create_keyboard_parametric.py`의 로직을 바꾸지 않는다. 입력 DXF만 교체하며, `compute_layout`·`shrink_stab_slots`·`resize_keyholes` 체인은 검증된 상태로 그대로 둔다.
  - `image/` 이미지와 3mf 슬라이서 프로젝트는 건드리지 않는다.

## Source of truth

- Glossary terms: **키 컷아웃**, **스위치 컷아웃**, **스테빌라이저 슬롯**, **스테빌라이저 철사**, **펑션 행**, **65% 배열** — `.forge/branch/feature/new-60percent/CONTEXT.md` 및 최상위 `.forge/CONTEXT.md`
- Related ADRs:
  - `adr/260821-202939-kle-is-the-only-layout-source-dxf-generated.md` — 생성기 방식과 기준 픽스처를 택한 근거, 기각한 대안 3개
  - `adr/260821-171944-split-halves-are-the-layout-source.md` — 원천 선언과 그 2026-08-21 개정(DXF가 여섯 번째 원천이었다)
  - 최상위 `.forge/adr/260812-224138-stab-wire-under-plate-assembly-order.md` — 슬롯 위치가 세 번의 출력 실패를 거쳐 정착한 이력. 픽스처를 보관하는 이유다.
- 생성 규칙 (그릴링에서 코드 대조로 확정, 전부 실측 검증됨):
  - 1u = **19.05mm**. 키 중심 = KLE 누적 좌표, y는 반전(DXF는 위로 증가).
  - 평행이동 오프셋 **x +0.094 / y +0.434** 유지 — 형상에는 무관하나 픽스처 대조를 좌표 그대로 하게 한다.
  - 스위치 컷아웃: **14.0mm** 정사각(중심만 유효 — `KeyholeSize` 13.96으로 덮어써진다).
  - 스테빌라이저 슬롯: 폭 **2u 이상** 키의 중심에서 X **±11.9mm**, Y는 키 중심보다 **0.65mm 아래**, 크기 **3.3 × 14.201mm**(짧은 변만 유효 — 긴 변은 `StabCutoutHeight` 14.1로 덮어써진다).
  - 첫 루프(외곽선): 스위치 바운딩박스 + **2.5mm** 사각형. `compute_layout()`이 `loops[1:]`로 버리므로 형상 무관, 원본 관례만 따른다.
  - 엔티티는 **LINE만** 사용한다. `dxf_line_loops()`가 LINE만 읽고 루프를 끝점 연속으로 조립하므로, 각 사각형의 4선을 끝점이 이어지는 순서로 내야 한다.
- Definition of Done:
  1. `freecad/reference/` 에 기준 픽스처 4개가 있다 — 원본 6행 DXF 2개(`6row-left-switch.dxf`·`6row-right-switch.dxf`)와 구 6행 KLE 2개(`6row-keylayout-left.json`·`6row-keylayout-right.json`). `ls freecad/reference/ | wc -l` → **4** (착수 전 디렉토리 자체가 없음).
  2. `tools/gen_dxf.py` 가 존재하고 `tools/kle.py` 파서를 재사용한다.
  3. **회귀 테스트가 먼저 작성되고 통과한다** (TDD): `python3 tools/test_gen_dxf.py` → **exit 0** (착수 전 파일 없음). 검사 내용:
     - 구 6행 KLE로 생성한 DXF의 스위치 컷아웃 중심이 원본과 **좌 37 / 우 51개 전부** 일치 (허용 오차 **0.01mm** — 실측 편차는 0.0009mm였으므로 10배 여유).
     - 스테빌라이저 슬롯도 중심·짧은 변이 원본과 일치 (좌 4 / 우 6개).
     - 스위치/슬롯 **개수**가 원본과 정확히 일치 (개수 검사를 좌표 검사와 별도로 둔다 — 좌표만 보면 누락을 못 잡는다).
     - 생성한 DXF를 `create_keyboard_parametric.py`와 **같은 파서**(`dxf_line_loops` 동등 구현)로 되읽어 검사한다. 생성기 자신의 자료구조로 검사하면 파서 왕복을 증명하지 못한다.
  4. `freecad/left-switch.dxf` 가 **스위치 컷아웃 30개 + 슬롯 4개** (착수 전 37 + 4).
  5. `freecad/right-switch.dxf` 가 **스위치 컷아웃 42개 + 슬롯 6개** (착수 전 51 + 6).
  6. 5행 DXF의 y 범위가 펑션 행만큼 줄었다 — 행 y중심이 5개이고 최상단이 구 배열의 숫자행 위치(약 86.2mm)다. 착수 전에는 6개이고 최상단 110.0mm였다.
  7. `README.md` 의 STL 표에 경고가 붙는다: `grep -c 'DXF 는 이미 5행' README.md` → **1** (착수 전 0). 문구는 "⚠ 이 STL·FCStd 는 6행 구배열 기준 — DXF 는 이미 5행이므로 재생성이 필요하다(2of2)". 이 불일치 구간은 2of2가 지운다.
  8. 낡은 갈래 3개(`create_keyboard_plates.py` · `create_techdraw_sheets.py` 헤더 주석, README의 해당 언급)에 "6행 구배열 기준, 미사용 — 현행은 `create_keyboard_parametric.py`" 취지의 주석이 붙는다.
  9. **수량 카탈로그 재확인**(지난 회고의 재발 방지): `grep -nE '\b(88|37|51)\b' README.md freecad/*.py` 결과에 배열 키 수를 뜻하는 항목이 남지 않는다. 착수 전 조사에서 스크립트에는 하드코딩된 키 수가 없고 README의 `88`은 이미 이번 브랜치에서 단 낡음 주석뿐임을 확인했다 — 이 항목은 **회귀 가드**이며, 새로 생기지 않는지만 본다.

## Work slices

- [ ] S1. 기준 픽스처를 보관한다. 현재의 6행 `left-switch.dxf`·`right-switch.dxf`를 `freecad/reference/6row-*.dxf` 로 복사하고, `git show HEAD:keylayout-left.json`·`keylayout-right.json`(아직 6행)을 `freecad/reference/6row-keylayout-*.json` 으로 꺼내 둔다. 왜 보관하는지 한 줄 README 또는 헤더 주석을 남긴다 — 완료 기준: `freecad/reference/` 에 4개 파일이 있고, 6행 KLE 2개를 `tools/kle.py`로 파싱하면 각 6행(좌 37키 / 우 51키)이다.
- [ ] S2. **회귀 테스트를 먼저 쓴다** — `tools/test_gen_dxf.py`. DoD 3의 4개 검사를 담고, 이 시점에는 `gen_dxf.py`가 없으므로 **반드시 실패한다** — 완료 기준: 테스트를 실행하면 `gen_dxf` 부재로 실패하고(exit ≠ 0), 실패 메시지가 무엇이 없는지 알려준다. (depends: S1)
- [ ] S3. `tools/gen_dxf.py` 를 구현해 S2를 통과시킨다. 위 "생성 규칙" 6항을 그대로 따르고 `tools/kle.py`를 재사용한다 — 완료 기준: `python3 tools/test_gen_dxf.py` → exit 0, 즉 구 6행 KLE에서 생성한 DXF가 원본과 0.01mm 이내로 일치하고 개수도 같다. (depends: S2)
- [ ] S4. 현재 5행 KLE로 `freecad/left-switch.dxf`·`right-switch.dxf`를 생성해 교체한다 — 완료 기준: DoD 4·5·6이 성립하고, 교체된 DXF를 `dxf_line_loops` 동등 구현으로 되읽어 좌 34개(30+4)·우 48개(42+6) 키 컷아웃 루프가 나온다. (depends: S3)
- [ ] S5. 문서를 갱신한다 — README STL 표에 불일치 경고(DoD 7), 낡은 갈래 3곳에 주석(DoD 8), 그리고 "배열을 바꿀 때는 `keylayout-left/right.json`만 고치고 `tools/gen_dxf.py`를 다시 돌린다"는 절차 한 단락 — 완료 기준: DoD 7·8·9가 성립한다. (depends: S4)
