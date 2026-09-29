#!/usr/bin/env python3
"""Screen SMT-pad/via proximity for JLCPCB process review.

The pad bounding-box and via-copper-edge distance is conservative, and JLC's
0.35 mm wording does not define a KiCad measurement datum. This report is a
process triage list, not an assembly acceptance or solder-mask DRC result.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew


LIMIT_MM = 0.35
MASK_BRIDGE_SCREEN_MM = 0.10
SOURCE = "https://jlcpcb.com/help/article/pcb-via-covering"
MASK_SOURCE = "https://jlcpcb.com/help/article/instructions-for-ordering"


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def audit(board_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    smd_pads = []
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            box = pad.GetBoundingBox()
            rectangle = tuple(mm(value) for value in
                              (box.GetLeft(), box.GetRight(),
                               box.GetTop(), box.GetBottom()))
            for layer, side in ((pcbnew.F_Cu, "top"),
                                (pcbnew.B_Cu, "bottom")):
                if pad.IsOnLayer(layer):
                    smd_pads.append((side, footprint.GetReference(),
                                     pad.GetNumber(), pad.GetNetname(), rectangle))

    close = []
    vias = [item for item in board.GetTracks()
            if isinstance(item, pcbnew.PCB_VIA)]
    for via in vias:
        at = via.GetPosition()
        x, y = mm(at.x), mm(at.y)
        radius = mm(via.GetWidth(pcbnew.F_Cu)) / 2
        nearest = None
        for side, ref, pin, pad_net, (left, right, top, bottom) in smd_pads:
            gap = math.hypot(max(left - x, 0.0, x - right),
                             max(top - y, 0.0, y - bottom)) - radius
            if nearest is None or gap < nearest[0]:
                nearest = gap, side, ref, pin, pad_net
        if nearest is None or nearest[0] >= LIMIT_MM:
            continue
        gap, side, ref, pin, pad_net = nearest
        filled_capped = bool(via.GetPrimaryDrillFilledFlag()
                             and via.GetPrimaryDrillCappedFlag())
        close.append({
            "via_net": via.GetNetname(),
            "via_at_mm": [round(x, 4), round(y, 4)],
            "via_diameter_mm": round(2 * radius, 4),
            "via_drill_mm": round(mm(via.GetDrillValue()), 4),
            "filled_and_capped": filled_capped,
            "nearest_smd_pad": f"{ref}.{pin}",
            "nearest_pad_net": pad_net,
            "side": side,
            "conservative_copper_edge_gap_mm": round(gap, 4),
        })
    close.sort(key=lambda row: (row["conservative_copper_edge_gap_mm"],
                                row["via_at_mm"]))
    unfilled = [row for row in close if not row["filled_and_capped"]]
    return {
        "board": board_path.name,
        "jlc_source": SOURCE,
        "jlc_mask_bridge_source": MASK_SOURCE,
        "screen_gap_mm": LIMIT_MM,
        "mask_bridge_screen_mm": MASK_BRIDGE_SCREEN_MM,
        "method": "nearest SMT pad axis-aligned copper bounding box to via copper circle;"
                  " conservative for nonrectangular pads and excludes mask expansion",
        "scope": "via-to-SMT-pad process triage on both board sides;"
                 " filling/capping still requires a JLC order remark/preview",
        "via_count": len(vias),
        "unfilled_smd_pad_overlap_count": sum(
            row["conservative_copper_edge_gap_mm"] < 0 for row in unfilled),
        "unfilled_below_0p10_copper_gap_count": sum(
            row["conservative_copper_edge_gap_mm"] < MASK_BRIDGE_SCREEN_MM
            for row in unfilled),
        "minimum_unfilled_near_pad_gap_mm": min(
            (row["conservative_copper_edge_gap_mm"] for row in unfilled),
            default=None),
        "unfilled_near_smd_pad_count": len(unfilled),
        "filled_capped_near_smd_pad_count": sum(
            row["filled_and_capped"] for row in close),
        "different_net_near_smd_pad_count": sum(
            row["via_net"] != row["nearest_pad_net"] for row in close),
        "near_smd_pad_vias": close,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gate", action="store_true",
                        help="Fail on unfilled SMT-pad overlap or <0.10 mm copper gap")
    args = parser.parse_args()
    result = audit(args.board)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    if args.gate and (result["unfilled_smd_pad_overlap_count"]
                      or result["unfilled_below_0p10_copper_gap_count"]):
        raise SystemExit("Unfilled via is too close to an SMT pad for the"
                         " provisional JLC mask-bridge screen")


if __name__ == "__main__":
    main()
