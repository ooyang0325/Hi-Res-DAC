#!/usr/bin/env python3
"""Gate the manually placed functional-ECO board without claiming routing."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew

from audit_placement import POST_FREEZE_ECO_REFS, check_board_netlist
from manual_functional_eco_layout import (
    CLOCK_GROUND_PATH,
    CLOCK_GROUND_VIA,
    CLOCK_PATHS,
    EXISTING_MOVES,
    GROUND_TVS_VIAS,
    LP_TVS_WAYPOINTS,
    NEW_POSITIONS,
    RP_TVS_WAYPOINTS,
)


def pad_xy(footprints: dict[str, pcbnew.FOOTPRINT], ref: str, pad: str) -> tuple[float, float]:
    found = [item for item in footprints[ref].Pads() if item.GetNumber() == pad]
    if len(found) != 1:
        raise AssertionError(f"{ref}.{pad} pad count differs")
    position = found[0].GetPosition()
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def pad_distance(footprints: dict[str, pcbnew.FOOTPRINT], a: str, ap: str,
                 b: str, bp: str) -> float:
    return math.dist(pad_xy(footprints, a, ap), pad_xy(footprints, b, bp))


def path_length(points: tuple[tuple[float, float], ...]) -> float:
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def check(board_path: Path, placement_path: Path, dfa_path: Path,
          fab_path: Path, drc_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    placement = json.loads(placement_path.read_text())
    dfa = json.loads(dfa_path.read_text())
    fab = json.loads(fab_path.read_text())
    drc = json.loads(drc_path.read_text())
    if placement["footprints"] != 544 or placement["named_nets"] != 250:
        raise AssertionError("Functional-ECO board population/net count changed")
    for ref, (x_mm, y_mm, orientation) in {**EXISTING_MOVES, **NEW_POSITIONS}.items():
        fp = footprints[ref]
        at = fp.GetPosition()
        actual = (pcbnew.ToMM(at.x), pcbnew.ToMM(at.y), fp.GetOrientationDegrees() % 360)
        wanted = (x_mm, y_mm, orientation % 360)
        if any(abs(a - b) > 0.001 for a, b in zip(actual, wanted)):
            raise AssertionError(f"Hand-selected {ref} position changed: {actual} != {wanted}")
    if placement["bbox_overlaps"] or placement["high_z_clock_pad_gap_violations"]:
        raise AssertionError("Placement overlap or clock-to-sensitive pad gap")
    if drc["violations"]:
        raise AssertionError(f"KiCad placement/partial-route DRC violations: {drc['violations'][:3]}")
    if dfa["package_pair_spacing_violation_count"] or dfa["board_edge_body_spacing_violation_count"]:
        raise AssertionError("JLC package-pair/edge geometry proxy violation")
    if {"D707", "D708", "U621"} & set(dfa["jlc_unclassified_refs"]):
        raise AssertionError("New JLC parts were omitted from the conservative package screen")
    if dfa["l1_output_corridor_blockers"] != {
        "J702_to_lower_relays": ["D707"], "lower_relays_to_J701": [],
    }:
        raise AssertionError("Unexpected L1 audio-corridor footprint occupation")
    if fab["project_settings_below_target"] or any(
        not slot["meets_project_jack_target"]
        for slot in fab["plated_slots"] if slot["ref"] in {"J701", "J702"}
    ):
        raise AssertionError("JLC/project ring or rule screen failed")
    check_board_netlist(board_path, POST_FREEZE_ECO_REFS)

    local = {
        "R688.2-U621.1": pad_distance(footprints, "R688", "2", "U621", "1"),
        "R689.2-U621.3": pad_distance(footprints, "R689", "2", "U621", "3"),
        "C667.1-U621.5": pad_distance(footprints, "C667", "1", "U621", "5"),
        "C667.2-U621.2": pad_distance(footprints, "C667", "2", "U621", "2"),
    }
    if max(local[key] for key in ("R688.2-U621.1", "R689.2-U621.3")) >= 2.0:
        raise AssertionError(f"Buffered U605 high-impedance inputs are too remote: {local}")
    if max(local[key] for key in ("C667.1-U621.5", "C667.2-U621.2")) >= 2.5:
        raise AssertionError(f"U621 local supply/return cap is too remote: {local}")
    dac_supply = {
        "AVCC_L": pad_distance(footprints, "U301", "15", "C305", "1"),
        "AVCC_R": pad_distance(footprints, "U301", "16", "C306", "1"),
        "VCCA": pad_distance(footprints, "U301", "17", "C307", "1"),
        "DVCC": pad_distance(footprints, "U301", "18", "C308", "1"),
        "1V3": pad_distance(footprints, "U301", "21", "C309", "1"),
    }
    if max(dac_supply.values()) >= 2.5:
        raise AssertionError(f"DAC high-frequency bypass pad placement regressed: {dac_supply}")

    segments = {
        (track.GetNetname(), frozenset((
            (round(pcbnew.ToMM(track.GetStart().x), 2), round(pcbnew.ToMM(track.GetStart().y), 2)),
            (round(pcbnew.ToMM(track.GetEnd().x), 2), round(pcbnew.ToMM(track.GetEnd().y), 2)),
        )))
        for track in board.GetTracks()
        if not isinstance(track, pcbnew.PCB_VIA) and track.GetLayer() == pcbnew.F_Cu
    }
    for net, points in (("JACK_RP", RP_TVS_WAYPOINTS), ("JACK_LP", LP_TVS_WAYPOINTS)):
        for a, b in zip(points, points[1:]):
            if (net, frozenset((a, b))) not in segments:
                raise AssertionError(f"Missing hand-drawn {net} TVS segment {a}->{b}")
    clock_segments = {
        (track.GetNetname(), frozenset((
            (round(pcbnew.ToMM(track.GetStart().x), 3), round(pcbnew.ToMM(track.GetStart().y), 3)),
            (round(pcbnew.ToMM(track.GetEnd().x), 3), round(pcbnew.ToMM(track.GetEnd().y), 3)),
        ))): track
        for track in board.GetTracks()
        if not isinstance(track, pcbnew.PCB_VIA) and track.GetLayer() == pcbnew.F_Cu
    }
    for net, points in CLOCK_PATHS:
        for a, b in zip(points, points[1:]):
            key = (net, frozenset((a, b)))
            track = clock_segments.get(key)
            if track is None or abs(pcbnew.ToMM(track.GetWidth()) - 0.15) > 0.001:
                raise AssertionError(f"Missing 0.15 mm L1 clock segment {net} {a}->{b}")
    clock_ground = clock_segments.get(("GND", frozenset(CLOCK_GROUND_PATH)))
    if clock_ground is None or abs(pcbnew.ToMM(clock_ground.GetWidth()) - 0.25) > 0.001:
        raise AssertionError("R227 is missing its local L2 GND return")
    clock_lengths = {
        "X201_to_R203": path_length(CLOCK_PATHS[0][1]),
        "R203_to_R227": path_length(CLOCK_PATHS[1][1]),
        "R203_to_DAC": path_length(CLOCK_PATHS[2][1]),
        "R665_to_U607": path_length(CLOCK_PATHS[4][1]),
    }
    clock_lengths["X201_to_DAC"] = clock_lengths["X201_to_R203"] + clock_lengths["R203_to_DAC"]
    if (clock_lengths["X201_to_R203"] > 2.0
            or clock_lengths["R203_to_DAC"] > 8.0
            or clock_lengths["X201_to_DAC"] > 10.0):
        raise AssertionError(f"Routed clock source-to-DAC limit exceeded: {clock_lengths}")
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    pad_ids = {
        pad.m_Uuid.AsString(): (fp.GetReference(), pad.GetNumber())
        for fp in board.GetFootprints() for pad in fp.Pads()
    }
    for ref, pin, wanted in (
        ("X201", "3", {("X201", "3"), ("R203", "1"), ("R227", "1")}),
        ("R203", "2", {("R203", "2"), ("TP711", "1"),
                        ("R665", "1"), ("U301", "7")}),
        ("R665", "2", {("R665", "2"), ("U607", "2")}),
        ("R703", "1", {("R703", "1")}),
    ):
        pad = next(item for item in footprints[ref].Pads() if item.GetNumber() == pin)
        actual = {pad_ids[item.m_Uuid.AsString()]
                  for item in connectivity.GetConnectedItems(pad)
                  if isinstance(item, pcbnew.PAD)}
        if actual != wanted:
            raise AssertionError(f"Clock copper connectivity {ref}.{pin}: {actual} != {wanted}")
    vias = {
        (round(pcbnew.ToMM(item.GetPosition().x), 2),
         round(pcbnew.ToMM(item.GetPosition().y), 2), item.GetNetname())
        for item in board.GetTracks() if isinstance(item, pcbnew.PCB_VIA)
    }
    if {(x, y, "GND") for x, y in (*GROUND_TVS_VIAS, CLOCK_GROUND_VIA)} - vias:
        raise AssertionError("Local TVS or R227 GND via is missing")
    local_tvs = {
        "D707-RP_to_J702": path_length(RP_TVS_WAYPOINTS[3:]),
        "D708-LP_to_J702": path_length(LP_TVS_WAYPOINTS),
    }
    if max(local_tvs.values()) > 4.2:
        raise AssertionError(f"J702 local TVS path exceeds 4.2 mm: {local_tvs}")
    return {
        "board": board_path.name,
        "footprints": placement["footprints"],
        "named_nets": placement["named_nets"],
        "schematic_pad_map": "exact",
        "drc_violations": 0,
        "unconnected_items": len(drc["unconnected_items"]),
        "ratsnest_unconnected_items": connectivity.GetUnconnectedCount(False),
        "bbox_overlaps": 0,
        "jlc_package_spacing_proxy_findings": 0,
        "jlc_body_edge_proxy_findings": 0,
        "u621_local_pad_distances_mm": {key: round(value, 3) for key, value in local.items()},
        "dac_hf_bypass_pad_distances_mm": {key: round(value, 3) for key, value in dac_supply.items()},
        "j702_local_tvs_route_mm": {key: round(value, 3) for key, value in local_tvs.items()},
        "clock_route_mm": {key: round(value, 3) for key, value in clock_lengths.items()},
        "routing_release": "HOLD: output/USB/I2S/power/protection routes, returns, G-3/G-4 and functional tests",
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
