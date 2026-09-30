#!/usr/bin/env python3
"""EMS layout screen for the integrated DAC-HPA board (home RF and 50/60 Hz hum).

Geometry-only checks on the saved, filled KiCad board:

* L2 GND plane integrity and fill fraction; return-path gaps (audit_return_path).
* Magnetic (hum) pickup: loop area of each analog audio net = routed length x
  height above its reference plane, and the EMF 2*pi*f*B*A it would see.
* Aggressor spacing: minimum copper gap from clock/USB/switching nets to the
  high-impedance and audio nets on the same or the facing layer.
* GND stitching: worst distance from any outer/L3 GND pour point to a GND via,
  and the largest gap in the board-edge via fence.
* Jack sleeve vias and headphone left/right copper separation.

Stack-up is JLC's default 1.6 mm 4-layer 7628 (JLC04161H-7628): L1-L2 and L3-L4
0.2104 mm prepreg, L2-L3 1.065 mm core. The results are a layout screen, not a
field solution or a measured IEC 61000-4-3/-4-6 immunity result.
"""

from __future__ import annotations

import argparse
import collections
import fnmatch
import json
import math
from pathlib import Path

import pcbnew

import audit_return_path

PREPREG_MM = 0.2104
CORE_MM = 1.065
HUM_B_T = (1e-6, 10e-6)          # typical near appliances / close to a mains transformer
HUM_F_HZ = (50.0, 60.0)
AUDIO = ["DACL", "DACLB", "DACR", "DACRB", "N4_*", "LEG_*", "JACK_*", "VREF"]
HIGHZ = ["N6_LW*", "N6_TW*", "N6_ORLP", "N6_ORLN", "N6_ORRP", "N6_ORRN", "N6_TLP_*", "N6_TLN_*", "N6_V3R_*",
         "N6_V3AG_A", "N6_V3AG_B", "N6_VOR*", "N6_VLL*", "N6_DA_*", "N6_DB_*", "N6_DC_*", "N6_DD_*", "N6_VT",
         "N6_CML", "N6_CMR"]
AGGRESSORS = ["MCLK", "FAM_CLK", "BCLK", "LRCLK", "SDATA", "USB_DP", "USB_DN", "N6_MCK_*", "N6_PMP",
              "N2_X20*_OUT", "N2_HSE_*", "N2_*CLK*", "LINK_SCK", "N2_LINK_SCK_*", "SWCLK", "N5_SW*", "N5_CP*"]
FACING = {"F.Cu": ("F.Cu",), "B.Cu": ("B.Cu", "PWR"), "PWR": ("PWR", "B.Cu")}


def match(net: str, pats: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(net, p) for p in pats)


def mm(v: int) -> float:
    return pcbnew.ToMM(v)


def seg_gap(t1, t2) -> float:
    """edge-to-edge gap of two straight tracks (mm)."""
    def pd(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        u = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
        return math.hypot(px - ax - u * dx, py - ay - u * dy)
    a = [mm(t1.GetStart().x), mm(t1.GetStart().y), mm(t1.GetEnd().x), mm(t1.GetEnd().y)]
    b = [mm(t2.GetStart().x), mm(t2.GetStart().y), mm(t2.GetEnd().x), mm(t2.GetEnd().y)]
    d = min(pd(*a[:2], *b), pd(*a[2:], *b), pd(*b[:2], *a), pd(*b[2:], *a))
    return d - mm(t1.GetWidth()) / 2 - mm(t2.GetWidth()) / 2


def hum(board) -> dict:
    height = {"F.Cu": PREPREG_MM, "B.Cu": PREPREG_MM, "PWR": PREPREG_MM}
    area = collections.defaultdict(float)
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or not match(t.GetNetname(), AUDIO):
            continue
        area[t.GetNetname()] += mm(t.GetLength()) * height[board.GetLayerName(t.GetLayer())]
    worst = sorted(area.items(), key=lambda kv: -kv[1])[:12]
    emf = lambda a_mm2, b, f: 2 * math.pi * f * b * a_mm2 * 1e-6
    return {
        "model": "loop = routed length x prepreg height to the adjacent GND copper (return current flows directly beneath)",
        "largest_loops_mm2": [[n, round(a, 2)] for n, a in worst],
        "emf_nV_at_60Hz": {f"{b * 1e6:g}uT": {n: round(emf(a, b, 60.0) * 1e9, 3) for n, a in worst[:6]} for b in HUM_B_T},
    }


def aggressor_spacing(board) -> list:
    tracks = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    agg = [t for t in tracks if match(t.GetNetname(), AGGRESSORS)]
    vic = [t for t in tracks if match(t.GetNetname(), HIGHZ + AUDIO)]
    best = {}
    for a in agg:
        la = board.GetLayerName(a.GetLayer())
        ba = a.GetBoundingBox()
        for v in vic:
            lv = board.GetLayerName(v.GetLayer())
            if lv not in FACING.get(la, ()) or v.GetNetname() == a.GetNetname():
                continue
            bv = v.GetBoundingBox()
            if (mm(bv.GetLeft()) - mm(ba.GetRight()) > 6 or mm(ba.GetLeft()) - mm(bv.GetRight()) > 6 or
                    mm(bv.GetTop()) - mm(ba.GetBottom()) > 6 or mm(ba.GetTop()) - mm(bv.GetBottom()) > 6):
                continue
            g = seg_gap(a, v)
            k = (a.GetNetname(), v.GetNetname())
            if g < best.get(k, (1e9,))[0]:
                best[k] = (round(g, 3), la, lv)
    return sorted([[k[0], k[1], *v] for k, v in best.items()], key=lambda r: r[2])[:25]


def stitching(board) -> dict:
    gvias = [(mm(v.GetPosition().x), mm(v.GetPosition().y)) for v in board.GetTracks()
             if isinstance(v, pcbnew.PCB_VIA) and v.GetNetname() == "GND"]
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                gvias.append((mm(p.GetPosition().x), mm(p.GetPosition().y)))
    out = {"gnd_vias_and_pth": len(gvias)}
    cell = collections.defaultdict(list)
    for x, y in gvias:
        cell[(int(x // 5), int(y // 5))].append((x, y))

    def nearest(x, y):
        best = 1e9
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for q in cell.get((int(x // 5) + dx, int(y // 5) + dy), ()):
                    best = min(best, math.hypot(x - q[0], y - q[1]))
        return best
    for layer in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        polys = [z.GetFilledPolysList(layer) for z in board.Zones()
                 if z.GetNetname() == "GND" and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer)]
        worst, pts = 0.0, 0
        bb = board.GetBoardEdgesBoundingBox()
        x = mm(bb.GetLeft()) + 0.25
        while x < mm(bb.GetRight()):
            y = mm(bb.GetTop()) + 0.25
            while y < mm(bb.GetBottom()):
                p = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
                if any(poly.Contains(p) for poly in polys):
                    pts += 1
                    worst = max(worst, min(nearest(x, y), 99.0))
                y += 0.5
            x += 0.5
        out[board.GetLayerName(layer)] = {"pour_samples": pts, "worst_distance_to_gnd_via_mm": round(worst, 2)}
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())
    fence = [(x, y) for x, y in gvias if min(x - x0, x1 - x, y - y0, y1 - y) <= 2.5]
    per = []
    for x, y in fence:
        d = min(x - x0, x1 - x, y - y0, y1 - y)
        if d == y - y0:
            per.append(x - x0)
        elif d == x1 - x:
            per.append((x1 - x0) + (y - y0))
        elif d == y1 - y:
            per.append((x1 - x0) + (y1 - y0) + (x1 - x))
        else:
            per.append(2 * (x1 - x0) + (y1 - y0) + (y1 - y))
    per.sort()
    L = 2 * ((x1 - x0) + (y1 - y0))
    gaps = [b - a for a, b in zip(per, per[1:])] + ([L - per[-1] + per[0]] if per else [L])
    out["edge_fence"] = {"vias_within_2p5mm_of_edge": len(fence), "largest_gap_mm": round(max(gaps), 2)}
    return out


def jacks_and_separation(board) -> dict:
    res = {}
    gv = [v for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA) and v.GetNetname() == "GND"]
    for fp in board.GetFootprints():
        if fp.GetReference() not in ("J701", "J702"):
            continue
        for p in fp.Pads():
            if p.GetNetname() == "GND":
                c = p.GetPosition()
                n = sum(1 for v in gv if math.hypot(mm(v.GetPosition().x - c.x), mm(v.GetPosition().y - c.y)) <= 3.0)
                res[f"{fp.GetReference()}.{p.GetNumber()}_gnd_vias_within_3mm"] = n
    tr = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    left = [t for t in tr if match(t.GetNetname(), ["JACK_L*", "LEG_L*"])]
    right = [t for t in tr if match(t.GetNetname(), ["JACK_R*", "LEG_R*"])]
    best = (1e9, "", "")
    for a in left:
        for b in right:
            if a.GetLayer() == b.GetLayer():
                g = seg_gap(a, b)
                if g < best[0]:
                    best = (g, a.GetNetname(), b.GetNetname())
    res["headphone_left_right_min_gap_mm"] = [round(best[0], 3), best[1], best[2]]
    return res


def audit(path: Path) -> dict:
    board = pcbnew.LoadBoard(str(path))
    rp = audit_return_path.audit(path)
    bb = board.GetBoardEdgesBoundingBox()
    board_area = mm(bb.GetWidth()) * mm(bb.GetHeight())
    l2 = [z for z in board.Zones() if z.IsOnLayer(pcbnew.In1_Cu)]
    l2_area = sum(z.GetFilledPolysList(pcbnew.In1_Cu).Area() for z in l2) / 1e12
    return {
        "board": path.name,
        "stackup_assumption": f"L1-L2 {PREPREG_MM} mm, L2-L3 {CORE_MM} mm, L3-L4 {PREPREG_MM} mm (JLC04161H-7628)",
        "l2_plane": {"filled_outlines": rp["l2_filled_outlines"], "fill_fraction_of_board": round(l2_area / board_area, 3)},
        "return_path": {k: rp[k] for k in ("f_cu_track_mm_without_l2", "f_cu_track_mm_total",
                                           "b_cu_track_mm_without_l3_gnd", "b_cu_track_mm_total")},
        "return_path_sensitive_gaps": rp["sensitive_nets_with_gaps"][:15],
        "hum": hum(board),
        "aggressor_min_gaps_mm": aggressor_spacing(board),
        "stitching": stitching(board),
        "jacks": jacks_and_separation(board),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("board", type=Path)
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    text = json.dumps(audit(a.board), indent=2) + "\n"
    if a.output:
        a.output.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
