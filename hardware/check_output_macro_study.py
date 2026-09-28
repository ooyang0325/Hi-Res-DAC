#!/usr/bin/env python3
"""Gate the manual output-macro study without claiming a routed board."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew

from audit_placement import check_board_netlist
from manual_output_macro_study import FEEDBACK, LOAD_PATHS, MOVES, RELAY_LEGS, SIGNAL_VIAS


CHANNELS = {
    "LP": ("U401", "9", "10", "R402", "C401", "R417", "K601"),
    "LN": ("U401", "7", "6", "R406", "C403", "R418", "K602"),
    "RP": ("U402", "9", "10", "R410", "C405", "R419", "K603"),
    "RN": ("U402", "7", "6", "R414", "C407", "R420", "K604"),
}


def loop_area(leg: str) -> float:
    points = list(FEEDBACK[f"N4_{leg}_OUT"])
    points += list(reversed(FEEDBACK[f"N4_{leg}_INN"]))
    return abs(sum(a[0] * b[1] - b[0] * a[1]
                   for a, b in zip(points, points[1:] + points[:1]))) / 2


def check(board_path: Path, placement_path: Path, dfa_path: Path,
          fab_path: Path, drc_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    placement = json.loads(placement_path.read_text())
    dfa = json.loads(dfa_path.read_text())
    fab = json.loads(fab_path.read_text())
    drc = json.loads(drc_path.read_text())
    if placement["footprints"] != 544 or placement["named_nets"] != 250:
        raise AssertionError("Output study population/net count differs from ECO capture")
    if placement["bbox_overlaps"] or placement["high_z_clock_pad_gap_violations"]:
        raise AssertionError("Output study has component overlap or sensitive clock-pad gap")
    if (dfa["package_pair_spacing_violation_count"]
            or dfa["board_edge_body_spacing_violation_count"]
            or fab["via_target_failure_count"]
            or fab["project_settings_below_target"]
            or drc["violations"]):
        raise AssertionError("Output study failed KiCad/JLC geometry screen")
    if len(board.GetTracks()) != 87:
        raise AssertionError("Output study partial-copper count differs")
    check_board_netlist(board_path)
    for ref, (x_mm, y_mm, angle) in MOVES.items():
        footprint = footprints[ref]
        at = footprint.GetPosition()
        actual = (pcbnew.ToMM(at.x), pcbnew.ToMM(at.y), footprint.GetOrientationDegrees() % 360)
        if any(abs(a - w) > 0.001 for a, w in zip(actual, (x_mm, y_mm, angle % 360))):
            raise AssertionError(f"Hand-selected {ref} placement changed: {actual}")

    track_segments = {
        (track.GetNetname(), track.GetLayer(), frozenset((
            (round(pcbnew.ToMM(track.GetStart().x), 3),
             round(pcbnew.ToMM(track.GetStart().y), 3)),
            (round(pcbnew.ToMM(track.GetEnd().x), 3),
             round(pcbnew.ToMM(track.GetEnd().y), 3)),
        ))): track
        for track in board.GetTracks() if not isinstance(track, pcbnew.PCB_VIA)
    }

    def require_path(net: str, points: tuple, layer: int, width: float,
                     first_width: float | None = None) -> None:
        for index, (a, b) in enumerate(zip(points, points[1:])):
            item = track_segments.get((net, layer, frozenset((a, b))))
            expected = first_width if index == 0 and first_width else width
            if item is None or abs(pcbnew.ToMM(item.GetWidth()) - expected) > 0.001:
                raise AssertionError(f"Missing {net} {layer} {expected} mm segment {a}->{b}")

    for net, points in FEEDBACK.items():
        require_path(net, points, pcbnew.F_Cu, 0.2,
                     first_width=0.25 if net.endswith("_OUT") else None)
    for net, points in RELAY_LEGS.items():
        require_path(net, points, pcbnew.F_Cu, 1.0)
    for net, layer, width, points in LOAD_PATHS:
        require_path(net, points, layer, width)
    actual_vias = {
        (item.GetNetname(), round(pcbnew.ToMM(item.GetPosition().x), 3),
         round(pcbnew.ToMM(item.GetPosition().y), 3),
         round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 3),
         round(pcbnew.ToMM(item.GetDrillValue()), 3))
        for item in board.GetTracks() if isinstance(item, pcbnew.PCB_VIA)
    }
    for net, (x, y) in SIGNAL_VIAS:
        if (net, x, y, 0.6, 0.2) not in actual_vias:
            raise AssertionError(f"Missing reviewed signal via: {net} {x},{y}")
    zone = board.Zones()[0]
    if (zone.GetNetname() != "GND"
            or not zone.HasFilledPolysForLayer(pcbnew.In1_Cu)
            or zone.GetFilledPolysList(pcbnew.In1_Cu).OutlineCount() != 1):
        raise AssertionError("The saved L2 GND fill is not one connected polygon")

    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    pad_ids = {
        pad.m_Uuid.AsString(): (fp.GetReference(), pad.GetNumber())
        for fp in board.GetFootprints() for pad in fp.Pads()
    }

    def copper_group(ref: str, pin: str) -> set[tuple[str, str]]:
        pad = next(p for p in footprints[ref].Pads() if p.GetNumber() == pin)
        return {pad_ids[item.m_Uuid.AsString()]
                for item in connectivity.GetConnectedItems(pad)
                if isinstance(item, pcbnew.PAD)}

    areas = {}
    trace_resistance = {}
    for leg, (opamp, out_pin, inn_pin, rf, cf, link, relay) in CHANNELS.items():
        if copper_group(opamp, out_pin) != {
            (opamp, out_pin), (rf, "2"), (cf, "2"), (link, "1"),
        }:
            raise AssertionError(f"{leg} amplifier output/feedback/link copper differs")
        if copper_group(opamp, inn_pin) != {
            (opamp, inn_pin), (rf, "1"), (cf, "1"),
        }:
            raise AssertionError(f"{leg} feedback return copper differs")
        if copper_group(relay, "4") != {(link, "2"), (relay, "4")}:
            raise AssertionError(f"{leg} link-to-relay input is open")
        area = loop_area(leg)
        if not 0 < area < 5.0:
            raise AssertionError(f"{leg} Rf/Cf centreline loop area {area:.3f} mm²")
        areas[leg] = round(area, 3)
        # 0.551 mOhm/square assumes 35 µm copper at 50 °C in the v1.1
        # calculation package. Excludes vias, relay, jacks and open branches.
        squares = sum(
            pcbnew.ToMM(track.GetLength()) / pcbnew.ToMM(track.GetWidth())
            for track in board.GetTracks()
            if not isinstance(track, pcbnew.PCB_VIA)
            and (track.GetNetname() == f"LEG_{leg}"
                 or (track.GetNetname() == f"N4_{leg}_OUT"
                     and pcbnew.ToMM(track.GetWidth()) >= 0.249))
        )
        trace_resistance[leg] = round(squares * 0.551, 2)
    return {
        "board": board_path.name,
        "footprints": 544,
        "named_nets": 250,
        "moved_footprints": len(MOVES),
        "drc_violations": 0,
        "bbox_overlaps": 0,
        "jlc_spacing_and_edge_proxy_findings": 0,
        "l2_gnd_filled_polygons": 1,
        "feedback_centreline_loop_area_mm2": areas,
        "load_path_trace_mohm_35um_50c_excluding_vias": trace_resistance,
        "drc_reported_unconnected_items": len(drc["unconnected_items"]),
        "ratsnest_unconnected_items": connectivity.GetUnconnectedCount(False),
        "routing_release": "HOLD: jack branches, input/T networks, supply returns, L3/L4 return, extraction and physical gates",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("placement", type=Path)
    parser.add_argument("dfa", type=Path)
    parser.add_argument("fab", type=Path)
    parser.add_argument("drc", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(check(args.board, args.placement, args.dfa, args.fab, args.drc),
                        indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
