#!/usr/bin/env python3
"""Check the separate, unapproved J702 two-TVS physical route option."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew

from j702_esd_option import LP_WAYPOINTS, RP_WAYPOINTS


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def route_length(points: tuple[tuple[float, float], ...]) -> float:
    return sum(math.dist(start, end) for start, end in zip(points, points[1:]))


def check(board_path: Path, dfa_path: Path, drc_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    dfa = json.loads(dfa_path.read_text())
    drc = json.loads(drc_path.read_text())
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if len(footprints) != 538 or drc["violations"]:
        raise SystemExit("J702 option population or DRC failed")
    if (dfa["package_pair_spacing_violation_count"]
            or dfa["board_edge_body_spacing_violation_count"]):
        raise SystemExit("J702 option package/edge proxy failed")
    if dfa["l1_output_corridor_blockers"]["J702_to_lower_relays"] != ["D707"]:
        raise SystemExit("Unexpected J702 output corridor contents")
    segments = set()
    vias = set()
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            p = item.GetPosition()
            vias.add((round(mm(p.x), 2), round(mm(p.y), 2), item.GetNetname()))
        elif item.GetLayer() == pcbnew.F_Cu:
            a, b = item.GetStart(), item.GetEnd()
            ends = frozenset(((round(mm(a.x), 2), round(mm(a.y), 2)),
                              (round(mm(b.x), 2), round(mm(b.y), 2))))
            segments.add((item.GetNetname(), ends))
    for net, points in (("JACK_RP", RP_WAYPOINTS),
                        ("JACK_LP", LP_WAYPOINTS)):
        for a, b in zip(points, points[1:]):
            if (net, frozenset((a, b))) not in segments:
                raise SystemExit(f"Missing hand-drawn {net} segment {a}→{b}")
    if not {(150.2, 102.3, "GND"), (148.31, 119.0, "GND")} <= vias:
        raise SystemExit("Local J702 GND vias are missing")
    for ref, net in (("D707", "JACK_RP"), ("D708", "JACK_LP")):
        pads = {p.GetNumber(): p.GetNetname() for p in footprints[ref].Pads()}
        if pads.get("1") != net or pads.get("2") != "GND":
            raise SystemExit(f"{ref} pad-to-net mapping changed")
    rp_local = route_length(RP_WAYPOINTS[3:])
    lp_local = route_length(LP_WAYPOINTS)
    if max(rp_local, lp_local) > 4.2:
        raise SystemExit("J702 local TVS route exceeds the provisional 4.2 mm screen")
    return {
        "board": board_path.name,
        "footprints": len(footprints),
        "d707_rp_tvs_to_j702_route_mm": round(rp_local, 3),
        "d708_lp_j702_to_tvs_route_mm": round(lp_local, 3),
        "k603_to_j702_rp_trial_route_mm": round(route_length(RP_WAYPOINTS), 3),
        "new_local_ground_vias": 2,
        "drc_violations": 0,
        "existing_jlc_package_spacing_proxy_findings": 0,
        "new_diodes_in_assembly_bom": False,
        "new_diodes_in_classified_package_proxy": False,
        "intentional_corridor_occupant": "D707 on JACK_RP route",
        "eco_status": "NOT in schematic or BOM; system ESD and LP main route open",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("dfa", type=Path)
    parser.add_argument("drc", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(check(args.board, args.dfa, args.drc),
                        indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
