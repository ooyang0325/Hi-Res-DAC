#!/usr/bin/env python3
"""Screen top-side iron approaches to both timer film-capacitor pairs.

The C631/C632 side gap to C636 and C633/C634 gap to C638 are local exceptions.
Each exposed terminal must still have a 1.5 mm north/south approach corridor
free of other component courtyards. Rectangular bounds make this conservative
for irregular packages. The screen does not replace a physical fit check.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


CAPACITORS = {"C631", "C632", "C633", "C634"}
APPROACH_MM = 1.5
TOOL_SIDE_MARGIN_MM = 0.25
EXPECTED_NETS = {
    "C631": {"N6_TLP_L", "GND"},
    "C632": {"N6_TLN_L", "GND"},
    "C633": {"N6_TLP_R", "GND"},
    "C634": {"N6_TLN_R", "GND"},
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def rectangle(box: pcbnew.BOX2I) -> tuple[float, float, float, float]:
    return tuple(mm(value) for value in
                 (box.GetLeft(), box.GetRight(), box.GetTop(), box.GetBottom()))


def audit(board_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {footprint.GetReference(): footprint
                  for footprint in board.GetFootprints()}
    envelopes = {}
    for ref, footprint in footprints.items():
        courtyard = footprint.GetCourtyard(pcbnew.F_CrtYd).BBox()
        if courtyard.GetWidth() <= 0 or courtyard.GetHeight() <= 0:
            courtyard = footprint.GetBoundingBox(False, False)
        envelopes[ref] = rectangle(courtyard)

    approaches = []
    violations = []
    for ref in sorted(CAPACITORS):
        pads = list(footprints[ref].Pads())
        if len(pads) != 2 or {pad.GetNetname() for pad in pads} != EXPECTED_NETS[ref]:
            raise AssertionError(f"Timer film capacitor pad map changed: {ref}")
        north = min(pads, key=lambda pad: pad.GetPosition().y)
        south = max(pads, key=lambda pad: pad.GetPosition().y)
        for label, pad, direction in (("north", north, -1),
                                      ("south", south, 1)):
            left, right, top, bottom = rectangle(pad.GetBoundingBox())
            span_left = left - TOOL_SIDE_MARGIN_MM
            span_right = right + TOOL_SIDE_MARGIN_MM
            candidates = []
            for other_ref, (other_left, other_right,
                            other_top, other_bottom) in envelopes.items():
                if other_ref == ref:
                    continue
                if other_left >= span_right or other_right <= span_left:
                    continue
                if direction < 0 and other_top < top:
                    candidates.append((top - other_bottom, other_ref))
                elif direction > 0 and other_bottom > bottom:
                    candidates.append((other_top - bottom, other_ref))
            nearest, blocker = min(candidates, default=(float("inf"), None))
            row = {
                "terminal": f"{ref}.{pad.GetNumber()}",
                "direction": label,
                "pad_bbox_mm": [round(value, 4) for value in
                                (left, right, top, bottom)],
                "approach_width_mm": round(span_right - span_left, 4),
                "nearest_other_footprint": blocker,
                "clearance_mm": round(nearest, 4) if blocker else None,
            }
            approaches.append(row)
            if nearest < APPROACH_MM - 1e-6:
                violations.append(row)
    return {
        "board": board_path.name,
        "minimum_approach_mm": APPROACH_MM,
        "tool_side_margin_mm": TOOL_SIDE_MARGIN_MM,
        "method": "pad copper bbox projected 1.5 mm north/south with 0.25 mm"
                  " lateral tool margin; other F.CrtYd bboxes or footprint"
                  " body bounds conservatively obstruct the corridor",
        "approaches": approaches,
        "violations": violations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()
    result = audit(args.board)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    if args.gate and result["violations"]:
        raise SystemExit(f"{len(result['violations'])} film-capacitor"
                         " terminal approaches are obstructed")


if __name__ == "__main__":
    main()
