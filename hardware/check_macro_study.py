#!/usr/bin/env python3
"""Gate the new manual macro-placement candidate without claiming routing."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew


def pad_distance(fp_by_ref: dict, left: str, lp: str,
                 right: str, rp: str) -> float:
    a = next(p for p in fp_by_ref[left].Pads() if p.GetNumber() == lp).GetPosition()
    b = next(p for p in fp_by_ref[right].Pads() if p.GetNumber() == rp).GetPosition()
    return math.hypot(pcbnew.ToMM(a.x - b.x), pcbnew.ToMM(a.y - b.y))


def check(board_path: Path, placement_path: Path, dfa_path: Path,
          drc_path: Path) -> dict:
    placement = json.loads(placement_path.read_text())
    dfa = json.loads(dfa_path.read_text())
    drc = json.loads(drc_path.read_text())
    if placement["footprints"] != 536 or placement["named_nets"] != 246:
        raise SystemExit("Candidate population or named nets changed")
    if placement["bbox_overlaps"] or placement["high_z_clock_pad_gap_violations"]:
        raise SystemExit("Footprint or clock-to-sensitive-pad geometry failed")
    if drc["violations"]:
        raise SystemExit("KiCad DRC reports error/warning violations")
    if dfa["package_pair_spacing_violation_count"] or dfa["board_edge_body_spacing_violation_count"]:
        raise SystemExit("JLC package-body or edge proxy failed")
    if any(dfa["l1_output_corridor_blockers"].values()):
        raise SystemExit("Primary L1 output corridor proxy is obstructed")
    clock = placement["clock_mm"]["MCLK_via_TP711_euclidean_lower_bound"]
    if clock >= 10:
        raise SystemExit(f"MCLK pad-distance lower bound {clock} mm exceeds 10 mm")
    i2s = {name: data["core_euclidean_lower_bound"]
           for name, data in placement["i2s_mm"].items()}
    if max(i2s.values()) >= 25:
        raise SystemExit(f"I2S pad-distance lower bound cannot fit 25 mm: {i2s}")
    dac_iv = placement["dac_iv_pad_distance_mm"]
    if max(dac_iv.values()) >= 7:
        raise SystemExit(f"DAC-to-I/V pad-distance lower bound cannot fit 7 mm: {dac_iv}")
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    local = {
        "U208.8_C224.1": pad_distance(footprints, "U208", "8", "C224", "1"),
        "U605.8_C628.1": pad_distance(footprints, "U605", "8", "C628", "1"),
        "U608.8_C630.1": pad_distance(footprints, "U608", "8", "C630", "1"),
        "U501.11_C510.1": pad_distance(footprints, "U501", "11", "C510", "1"),
    }
    if max(local.values()) >= 6:
        raise SystemExit(f"Selected bypass/output capacitors remain remote: {local}")
    or_taps = {
        ref: pad_distance(footprints, ref, "2", cap, "1")
        for ref, cap in (("R926", "C639"), ("R927", "C640"),
                         ("R928", "C641"), ("R929", "C642"))
    }
    if max(or_taps.values()) >= 5:
        raise SystemExit(f"High-impedance OR tap/filter remains remote: {or_taps}")
    return {
        "board": board_path.name,
        "footprints": placement["footprints"],
        "named_nets": placement["named_nets"],
        "footprint_overlaps": 0,
        "clock_sensitive_pad_gap_findings": 0,
        "drc_violations": 0,
        "jlc_package_spacing_proxy_findings": 0,
        "jlc_body_edge_proxy_findings": 0,
        "jlc_unclassified_package_refs": len(dfa["jlc_unclassified_refs"]),
        "unconnected_items": len(drc["unconnected_items"]),
        "mclk_via_TP711_pad_lower_bound_mm": clock,
        "i2s_pad_lower_bounds_mm": i2s,
        "dac_iv_pad_lower_bounds_mm": dac_iv,
        "selected_cap_pad_distances_mm": {key: round(value, 2) for key, value in local.items()},
        "or_tap_to_filter_pad_distances_mm": {key: round(value, 2) for key, value in or_taps.items()},
        "routing_release": "HOLD — critical concurrent routes, returns, G-3/G-4 and JLC process open",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("placement", type=Path)
    parser.add_argument("dfa", type=Path)
    parser.add_argument("drc", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(check(args.board, args.placement, args.dfa, args.drc),
                        indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
