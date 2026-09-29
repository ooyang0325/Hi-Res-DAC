#!/usr/bin/env python3
"""Bound the local VBUS/5V_SYS neckdowns allowed by the review-board DRC.

The 1 mm rule applies to the power trunks. The listed connector and WSON
lands need one short, narrower F.Cu segment at the pad. This checks the
actual copper endpoint and length; merely crossing a courtyard is not enough.
It is a geometry screen, not a current, temperature, or USB attach proof.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew


TRUNK_MIN_MM = 1.0
PAD_TOLERANCE_MM = 0.01
EXCEPTIONS = {
    ("J101", "A4/B9"): ("VBUS", 0.50, 2.0),
    ("J101", "B4/A9"): ("VBUS", 0.50, 2.0),
    ("U102", "1"): ("5V_SYS", 0.30, 1.2),
    ("U102", "6"): ("VBUS", 0.30, 1.2),
    ("U504", "6"): ("5V_SYS", 0.30, 1.2),
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def audit(board_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    pads = {}
    for key, (net, minimum_width, maximum_length) in EXCEPTIONS.items():
        ref, number = key
        matches = [pad for pad in footprints[ref].Pads()
                   if pad.GetNumber() == number]
        if len(matches) != 1 or matches[0].GetNetname() != net:
            raise AssertionError(f"Power escape pad identity changed: {key}")
        pads[key] = (matches[0].GetPosition(), net,
                     minimum_width, maximum_length)

    narrow = []
    violations = []
    used_pads = set()
    for track in board.GetTracks():
        if (isinstance(track, pcbnew.PCB_VIA)
                or track.GetNetname() not in {"VBUS", "5V_SYS"}):
            continue
        width = mm(track.GetWidth())
        if width >= TRUNK_MIN_MM - 1e-6:
            continue
        start, end = track.GetStart(), track.GetEnd()
        length = math.hypot(mm(end.x - start.x), mm(end.y - start.y))
        match = None
        for key, (position, net, minimum_width, maximum_length) in pads.items():
            if net != track.GetNetname():
                continue
            if min(math.hypot(mm(endpoint.x - position.x),
                              mm(endpoint.y - position.y))
                   for endpoint in (start, end)) <= PAD_TOLERANCE_MM:
                match = key, minimum_width, maximum_length
                break
        row = {
            "net": track.GetNetname(),
            "layer": track.GetLayerName(),
            "start_mm": [round(mm(start.x), 4), round(mm(start.y), 4)],
            "end_mm": [round(mm(end.x), 4), round(mm(end.y), 4)],
            "width_mm": round(width, 4),
            "length_mm": round(length, 4),
            "pad": f"{match[0][0]}.{match[0][1]}" if match else None,
        }
        reasons = []
        if match is None:
            reasons.append("not launched at a whitelisted power pad")
        else:
            key, minimum_width, maximum_length = match
            if width < minimum_width - 1e-6:
                reasons.append(f"width below {minimum_width:.2f} mm")
            if length > maximum_length + 1e-6:
                reasons.append(f"length above {maximum_length:.2f} mm")
            if key in used_pads:
                reasons.append("more than one narrow segment at this pad")
            used_pads.add(key)
        if track.GetLayer() != pcbnew.F_Cu:
            reasons.append("narrow power escape is not on F.Cu")
        if track.GetClass() == "PCB_ARC":
            reasons.append("narrow power escape is an arc")
        if reasons:
            violations.append({**row, "reasons": reasons})
        narrow.append(row)
    narrow.sort(key=lambda row: (row["net"], row["pad"] or "",
                                 row["start_mm"]))
    return {
        "board": board_path.name,
        "trunk_min_width_mm": TRUNK_MIN_MM,
        "method": "one F.Cu pad-centred straight neckdown per listed small land;"
                  " all other VBUS/5V_SYS copper at least 1 mm",
        "exception_count": len(narrow),
        "violations": violations,
        "exceptions": narrow,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()
    report = audit(args.board)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    if args.gate and report["violations"]:
        raise SystemExit(f"{len(report['violations'])} narrow power escapes"
                         " exceed the scoped local-pad rule")


if __name__ == "__main__":
    main()
