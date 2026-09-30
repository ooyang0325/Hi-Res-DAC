#!/usr/bin/env python3
"""EMS screen: reference-plane continuity under every routed track.

For each F.Cu track the nearest reference is the L2 GND plane; for each
B.Cu (L4) track it is the L3 layer, which on this board carries a GND pour
plus power traces. The screen samples each track centreline every 0.1 mm and
reports length without the saved filled GND copper directly beneath (L2 for
F.Cu, L3 GND pour for B.Cu). It is a plan-view return-path screen, not a
field solution or a measured immunity result.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path

import pcbnew

SENSITIVE = ("DACL", "DACLB", "DACR", "DACRB", "MCLK", "FAM_CLK", "BCLK", "LRCLK", "SDATA",
             "USB_DP", "USB_DN", "VREF", "N4_", "LEG_", "JACK_", "N6_")


def gnd_polys(board: pcbnew.BOARD, layer: int):
    return [z.GetFilledPolysList(layer) for z in board.Zones()
            if z.GetNetname() == "GND" and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer)]


def audit(path: Path, step: float = 0.1) -> dict:
    board = pcbnew.LoadBoard(str(path))
    refs = {pcbnew.F_Cu: gnd_polys(board, pcbnew.In1_Cu), pcbnew.B_Cu: gnd_polys(board, pcbnew.In2_Cu)}
    missing = collections.defaultdict(float)
    total = collections.defaultdict(float)
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() not in refs or t.GetNetname() == "GND":
            continue
        a, b = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = map(pcbnew.ToMM, (a.x, a.y, b.x, b.y))
        length = math.hypot(bx - ax, by - ay)
        n = max(1, math.ceil(length / step))
        key = (t.GetNetname(), board.GetLayerName(t.GetLayer()))
        total[key] += length
        for i in range(n):
            f = (i + 0.5) / n
            p = pcbnew.VECTOR2I(pcbnew.FromMM(ax + (bx - ax) * f), pcbnew.FromMM(ay + (by - ay) * f))
            if not any(poly.Contains(p) for poly in refs[t.GetLayer()]):
                missing[key] += length / n
    rows = sorted(((net, layer, round(m, 2), round(total[(net, layer)], 2))
                   for (net, layer), m in missing.items() if m > 0.05), key=lambda r: -r[2])
    sens = [r for r in rows if r[0].startswith(SENSITIVE)]
    l2 = gnd_polys(board, pcbnew.In1_Cu)
    return {
        "board": path.name,
        "method": "0.1 mm centreline samples against saved filled GND: L2 under F.Cu, L3 GND pour under B.Cu",
        "l2_filled_outlines": sum(p.OutlineCount() for p in l2),
        "l2_holes": sum(p.HoleCount(i) for p in l2 for i in range(p.OutlineCount())),
        "f_cu_track_mm_without_l2": round(sum(m for (n, l), m in missing.items() if l == "F.Cu"), 2),
        "b_cu_track_mm_without_l3_gnd": round(sum(m for (n, l), m in missing.items() if l == "B.Cu"), 2),
        "f_cu_track_mm_total": round(sum(v for (n, l), v in total.items() if l == "F.Cu"), 1),
        "b_cu_track_mm_total": round(sum(v for (n, l), v in total.items() if l == "B.Cu"), 1),
        "sensitive_nets_with_gaps": sens[:60],
        "worst_40": rows[:40],
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
