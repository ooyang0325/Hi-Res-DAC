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
    assert all(not p.GetNumber() and near(pcbnew.ToMM(p.GetDrillSize().x), 0.65) for p in locating)
    checks += 4
    j702 = footprint("JLC_Imported", "AUDIO-SMD_PJ-332A-6A")
    pad(j702, "1", (-4.725, 2.95), (1.0, 1.9), pcbnew.PAD_ATTRIB_PTH)
    pad(j702, "2", (-4.725, -2.5), (1.0, 1.9), pcbnew.PAD_ATTRIB_PTH)
    assert all(not p.IsOnLayer(pcbnew.F_Paste) for p in j702.Pads() if p.GetNumber() in {"1", "2"})
    checks += 1
    j701 = footprint("JLC_Imported", "AUDIO-TH_GT-3321667P-01")
    j701_pads = list(j701.Pads())
    assert {p.GetNumber() for p in j701_pads} == {str(number) for number in range(1, 13)}
    assert all(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in j701_pads)
    assert all(not p.IsOnLayer(pcbnew.F_Paste) for p in j701_pads)
    checks += 3
    print(f"PASS: {checks} selected pad dimensions, pad types and hole checks")
    print("OPEN: G-3 manufacturer drawing overlays and physical sample checks; J101/J702 through-hole soldering process")


if __name__ == "__main__":
    main()
