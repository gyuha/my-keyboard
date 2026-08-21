#!/usr/bin/env python3
"""gen_dxf.py 회귀 테스트 — 6행 KLE 로 생성한 DXF 가 원본 6행 DXF 와 같은가.

이것이 생성 규칙 자체의 정확성을 증명하는 유일한 검사다. 생성한 5행 DXF 를 5행 KLE 와
대조하는 왕복 검증은 생성기가 자기 규칙에 일관됨만 보이고, 규칙이 틀렸는지는 못 잡는다.
근거: adr/260821-202939-kle-is-the-only-layout-source-dxf-generated.md

실행: python3 tools/test_gen_dxf.py   (통과 시 exit 0)
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dxf
import gen_dxf                      # S3 에서 구현된다 — 없으면 여기서 실패한다

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "freecad" / "reference"
TOL = 0.01                          # 실측 편차 0.0009mm 의 10배 여유
SLOT_MAX_W = 5.0                    # StabCutoutMaxWidth — 스위치/슬롯 경계

failures = []


def check(label, ok, detail=""):
    if not ok:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def split_cutouts(loops):
    """키 컷아웃을 스위치와 스테빌라이저 슬롯으로 가른다 (첫 루프=외곽선 제외)."""
    switches, slots = [], []
    for loop in loops[1:]:
        w, h = dxf.size(loop)
        (switches if min(w, h) > SLOT_MAX_W else slots).append(loop)
    return switches, slots


def match_by_centre(generated, original, label):
    """중심 좌표로 1:1 짝지어 편차를 확인한다. 개수는 별도 검사이므로 여기선 짝만 본다."""
    gen = sorted(dxf.centre(l) for l in generated)
    org = sorted(dxf.centre(l) for l in original)
    if len(gen) != len(org):
        return
    worst = 0.0
    for (gx, gy), (ox, oy) in zip(gen, org):
        worst = max(worst, abs(gx - ox), abs(gy - oy))
    check(f"{label} 중심 편차", worst <= TOL, f"최대 {worst:.4f}mm (허용 {TOL})")
    return worst


for side, ref_dxf, ref_kle, n_switch, n_slot in (
    ("좌", "6row-left-switch.dxf",  "6row-keylayout-left.json",  37, 4),
    ("우", "6row-right-switch.dxf", "6row-keylayout-right.json", 51, 6),
):
    original = dxf.read_loops(REF / ref_dxf)
    org_sw, org_sl = split_cutouts(original)

    # 기준 픽스처 자체가 기대와 맞는지 먼저 확인한다 — 픽스처가 바뀌면 테스트 의미가 사라진다
    check(f"{side} 픽스처 스위치 수", len(org_sw) == n_switch, f"{len(org_sw)} (기대 {n_switch})")
    check(f"{side} 픽스처 슬롯 수", len(org_sl) == n_slot, f"{len(org_sl)} (기대 {n_slot})")

    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        out = Path(tmp.name)
    gen_dxf.generate(REF / ref_kle, out)

    # 생성물은 parametric.py 와 동등한 파서로 되읽는다 — 파서 왕복까지 증명해야 한다
    generated = dxf.read_loops(out)
    gen_sw, gen_sl = split_cutouts(generated)

    check(f"{side} 생성 스위치 수", len(gen_sw) == n_switch, f"{len(gen_sw)} (기대 {n_switch})")
    check(f"{side} 생성 슬롯 수", len(gen_sl) == n_slot, f"{len(gen_sl)} (기대 {n_slot})")
    check(f"{side} 외곽선 존재", len(generated) == n_switch + n_slot + 1,
          f"루프 {len(generated)} (기대 {n_switch + n_slot + 1})")

    sw_dev = match_by_centre(gen_sw, org_sw, f"{side} 스위치")
    sl_dev = match_by_centre(gen_sl, org_sl, f"{side} 슬롯")

    # 슬롯은 짧은 변이 최종 형상에 남는다 (긴 변은 StabCutoutHeight 로 덮어써짐)
    if len(gen_sl) == len(org_sl):
        gen_short = sorted(min(dxf.size(l)) for l in gen_sl)
        org_short = sorted(min(dxf.size(l)) for l in org_sl)
        worst = max((abs(a - b) for a, b in zip(gen_short, org_short)), default=0.0)
        check(f"{side} 슬롯 짧은 변", worst <= TOL, f"최대 편차 {worst:.4f}mm")

    out.unlink()
    if sw_dev is not None and sl_dev is not None:
        print(f"{side}측: 스위치 {len(gen_sw)}개 (편차 {sw_dev:.4f}mm) · "
              f"슬롯 {len(gen_sl)}개 (편차 {sl_dev:.4f}mm)")

if failures:
    print(f"\n불일치 {len(failures)}건:")
    for f in failures:
        print("  ✗", f)
    sys.exit(1)
print("\n생성기가 원본 6행 DXF 를 재현한다 — 회귀 테스트 통과")
