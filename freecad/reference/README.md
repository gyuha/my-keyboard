# 기준 픽스처 (6행 구배열)

`tools/gen_dxf.py` 의 회귀 테스트용 기준이다. **손으로 고치지 않는다.**

여기 있는 6행 DXF 는 단순한 좌표 파일이 아니라 세 번의 출력 실패를 거쳐 정착한
물리적 기준이다 (스테빌라이저 슬롯 이력: `.forge/adr/260812-224138-stab-wire-under-plate-assembly-order.md`).
5행 DXF 로 덮어쓰면 그 기준이 작업 트리에서 사라지므로 여기에 남긴다.

`tools/test_gen_dxf.py` 가 하는 일: **6행 KLE → 생성 → 6행 DXF 와 대조.**
생성된 5행 DXF 를 5행 KLE 와 대조하는 왕복 검증으로는 부족하다 — 그것은 생성기가
자기 규칙에 일관됨만 보이고, 규칙 자체가 틀렸는지는 원본 대조만이 잡는다.

| 파일 | 내용 |
| --- | --- |
| `6row-left-switch.dxf` | 원본 좌측 DXF — 스위치 컷아웃 37 + 스테빌라이저 슬롯 4 |
| `6row-right-switch.dxf` | 원본 우측 DXF — 스위치 컷아웃 51 + 스테빌라이저 슬롯 6 |
| `6row-keylayout-left.json` | 펑션 행이 있던 좌측 KLE (6행 37키) |
| `6row-keylayout-right.json` | 펑션 행이 있던 우측 KLE (6행 51키) |

근거: `.forge/branch/feature/new-60percent/adr/260821-202939-kle-is-the-only-layout-source-dxf-generated.md`
