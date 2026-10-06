#!/usr/bin/env python3
"""Check CAD land dimensions selected from FOOTPRINT_SOURCES.md.

Run with KiCad's Python interpreter, which provides pcbnew. These dimensional
checks complement, but cannot replace, G-3 sample and 1:1 overlay checks.
"""

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
checks = 0


def footprint(library: str, name: str):
    item = pcbnew.FootprintLoad(str(HERE / f"{library}.pretty"), name)
    assert item is not None, f"Cannot load {library}:{name}"
    return item


def near(actual: float, expected: float) -> bool:
    return abs(actual - expected) <= 0.011


def pad(item, number: str, position: tuple[float, float], size: tuple[float, float], kind: int = pcbnew.PAD_ATTRIB_SMD) -> None:
    global checks
    found = [p for p in item.Pads() if p.GetNumber() == number]
    assert len(found) == 1, f"{item.GetFPIDAsString()} pad {number}: {len(found)} instances"
    p = found[0]
    xy = tuple(pcbnew.ToMM(v) for v in (p.GetPosition().x, p.GetPosition().y))
    wh = tuple(pcbnew.ToMM(v) for v in (p.GetSize().x, p.GetSize().y))
    assert p.GetAttribute() == kind and all(near(a, e) for a, e in zip(xy + wh, position + size)), (
        f"{item.GetFPIDAsString()} pad {number}: {xy} {wh} type {p.GetAttribute()} != {position} {size} type {kind}"
    )
    checks += 1


def locating_holes(item, positions: set[tuple[float, float]]) -> None:
    global checks
    holes = [p for p in item.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    found = {
        tuple(round(pcbnew.ToMM(v), 3) for v in (p.GetPosition().x, p.GetPosition().y))
        for p in holes
    }
    assert found == positions and len(holes) == len(positions), (item.GetFPIDAsString(), found)
    assert all(not p.GetNumber() and near(pcbnew.ToMM(p.GetDrillSize().x), 1.2)
               and near(pcbnew.ToMM(p.GetDrillSize().y), 1.2) for p in holes)
    checks += len(holes)


def main() -> None:
    global checks
    x201 = footprint("DAC_HPA", "X201_KC2520K80_Kyocera")
    for n, xy in {"1": (-0.925, 0.725), "2": (0.925, 0.725), "3": (0.925, -0.725), "4": (-0.925, -0.725)}.items():
        pad(x201, n, xy, (1.05, 0.95))
    ndk = footprint("DAC_HPA", "X202_X203_NDK_NZ2520SDA")
    for n, xy in {"1": (-0.825, 0.625), "2": (0.825, 0.625), "3": (0.825, -0.625), "4": (-0.825, -0.625)}.items():
        pad(ndk, n, xy, (1.0, 1.0))
    film = footprint("DAC_HPA", "C631_ECHU1H224GX9_D4")
    pad(film, "1", (-2.75, 0), (1.5, 3.8))
    pad(film, "2", (2.75, 0), (1.5, 3.8))
    relay = footprint("DAC_HPA", "K601_TLP3545A_LF1_HandSolder")
    for n, xy in {"1": (-2.54, 4.5), "2": (0, 4.5), "3": (2.54, 4.5),
                  "4": (2.54, -4.5), "5": (0, -4.5), "6": (-2.54, -4.5)}.items():
        pad(relay, n, xy, (1.5, 1.9))
    tvs = footprint("DAC_HPA", "D102_SMDJ12A_HandSolder")
    for n, x in (("1", -3.55), ("2", 3.55)):
        pad(tvs, n, (x, 0), (3.3, 2.8))
    assert all(near(p.GetOrientationDegrees(), 90) for p in tvs.Pads())
    checks += 1
    cpld = footprint("DAC_HPA", "QFN-32_L4.0-W4.0-P0.40-BL-EP2.7_EP")
    pad(cpld, "EP", (0, 0), (2.8, 2.8))
    connector = footprint("DAC_HPA", "J101_USB4105-GF-A_12lands_4stakes")
    signal = [p for p in connector.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    stakes = [p for p in connector.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    locating = [p for p in connector.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    assert (len(signal), len(stakes), len(locating)) == (12, 4, 2)
    assert {p.GetNumber() for p in stakes} == {"S1", "S2", "S3", "S4"}
    assert all(not p.IsOnLayer(pcbnew.F_Paste) for p in stakes)
    for stake in stakes:
        expected_length = 2.24 if stake.GetNumber() in {"S1", "S2"} else 1.94
        assert near(pcbnew.ToMM(stake.GetSize().x), 1.14)
        assert near(pcbnew.ToMM(stake.GetSize().y), expected_length)
        assert near(pcbnew.ToMM(stake.GetDrillSize().x), 0.6)
    assert all(not p.GetNumber() and near(pcbnew.ToMM(p.GetDrillSize().x), 0.65) for p in locating)
    checks += 4
    j702 = footprint("DAC_HPA", "J702_PJ-332A-6A_peg_holes")
    pad(j702, "1", (-4.725, 2.95), (1.35, 2.25), pcbnew.PAD_ATTRIB_PTH)
    pad(j702, "2", (-4.725, -2.5), (1.35, 2.25), pcbnew.PAD_ATTRIB_PTH)
    assert all(not p.IsOnLayer(pcbnew.F_Paste) for p in j702.Pads() if p.GetNumber() in {"1", "2"})
    for p in j702.Pads():
        if p.GetNumber() in {"1", "2"}:
            assert near(pcbnew.ToMM(p.GetDrillSize().x), 0.6)
            assert near(pcbnew.ToMM(p.GetDrillSize().y), 1.5)
    locating_holes(j702, {(-4.275, -0.05), (2.725, -0.05)})
    assert all(item.GetLayerName() != "Edge.Cuts" for item in j702.GraphicalItems())
    checks += 3
    j701 = footprint("DAC_HPA", "J701_GT-3321667P-01_maker_slots")
    j701_pads = list(j701.Pads())
    assert {p.GetNumber() for p in j701_pads} == {""} | {str(number) for number in range(1, 13)}
    assert all(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in j701_pads if p.GetNumber())
    assert all(not p.IsOnLayer(pcbnew.F_Paste) for p in j701_pads)
    expected_centres = {
        "1": (-6.95, -3.25), "2": (-6.45, 3.25),
        "3": (-4.25, -3.25), "4": (-3.75, 3.25),
        "5": (-1.55, -3.25), "6": (-1.05, 3.25),
        "7": (6.95, -3.45), "8": (6.95, 3.45),
        "9": (6.95, 1.6), "10": (6.95, -1.95),
        "11": (2.2, -4.05), "12": (2.2, 4.05),
    }
    for number, centre in expected_centres.items():
        pad(j701, number, centre, (2.15, 1.25), pcbnew.PAD_ATTRIB_PTH)
    for p in j701_pads:
        if p.GetNumber():
            assert near(pcbnew.ToMM(p.GetDrillSize().x), 1.4)
            assert near(pcbnew.ToMM(p.GetDrillSize().y), 0.5)
    locating_holes(j701, {(-3.55, 0.0), (3.95, -1.55)})
    assert all(item.GetLayerName() != "Edge.Cuts" for item in j701.GraphicalItems())
    # JLCPCB's published plated-slot size tolerance is +0.13 mm. The
    # copper-only enlargement leaves a 0.31 mm worst ring on both jacks.
    assert near(min((2.15 - 1.4 - 0.13) / 2, (1.25 - 0.5 - 0.13) / 2), 0.31)
    assert near(min((2.25 - 1.5 - 0.13) / 2, (1.35 - 0.6 - 0.13) / 2), 0.31)
    checks += 8
    dgk = footprint("JLC_Imported", "VSSOP-8_L3.0-W3.0-P0.65-LS5.0-BL")
    assert {p.GetNumber() for p in dgk.Pads()} == {str(i) for i in range(1, 9)}
    assert near(pcbnew.ToMM(next(p for p in dgk.Pads() if p.GetNumber() == "2").GetPosition().x) -
                pcbnew.ToMM(next(p for p in dgk.Pads() if p.GetNumber() == "1").GetPosition().x), 0.65)
    transistor = footprint("JLC_Imported", "SOT-23-3_L2.9-W1.6-P1.90-LS2.8-BR")
    assert {p.GetNumber() for p in transistor.Pads()} == {"1", "2", "3"}
    checks += 3
    print(f"PASS: {checks} selected pad dimensions, pad types and hole checks")
    print("OPEN: G-3 manufacturer drawing overlays and physical sample checks; J101/J702 through-hole soldering process")


if __name__ == "__main__":
    main()
