#!/usr/bin/env python3
"""Gate the manually routed amplifier-to-jack study as partial review data."""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import pcbnew

from audit_placement import check_board_netlist
from check_output_macro_study import CHANNELS, loop_area
from manual_output_macro_study import FEEDBACK


HERE = Path(__file__).resolve().parent
JACK_GROUPS = {
    "LP": {("K601", "6"), ("J701", "7"), ("J701", "8"),
           ("J702", "4"), ("D701", "1"), ("D708", "1")},
    "LN": {("K602", "6"), ("J701", "6"), ("D703", "1")},
    "RP": {("K603", "6"), ("J701", "4"), ("J701", "5"),
           ("J702", "3"), ("D702", "1"), ("D707", "1")},
    "RN": {("K604", "6"), ("J701", "2"), ("J701", "3"), ("D704", "1")},
}


def check(board_path: Path, placement_path: Path, dfa_path: Path,
          fab_path: Path, drc_path: Path, tvs_path: Path,
          trace_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    placement = json.loads(placement_path.read_text())
    dfa = json.loads(dfa_path.read_text())
    fab = json.loads(fab_path.read_text())
    drc = json.loads(drc_path.read_text())
    tvs = json.loads(tvs_path.read_text())
    trace = json.loads(trace_path.read_text())
    manual = json.loads((HERE / "INTEGRATED_AUDIO_MANUAL_DELTA.json").read_text())
    if placement["footprints"] != 544 or placement["named_nets"] != 250:
        raise AssertionError("Integrated study population/net count changed")
    if placement["bbox_overlaps"] or placement["high_z_clock_pad_gap_violations"]:
        raise AssertionError("Integrated study overlap or sensitive-to-clock gap")
    if (dfa["package_pair_spacing_violation_count"]
            or dfa["board_edge_body_spacing_violation_count"]
            or fab["via_target_failure_count"]
            or fab["project_settings_below_target"]
            or drc["violations"]):
        raise AssertionError("Integrated study KiCad/JLC geometry screen failed")
    if tvs["board"] != board_path.name or trace["board"] != board_path.name:
        raise AssertionError("Audit board identity differs")
    if len(tvs["local_routes_mm"]) != 6 or max(tvs["local_routes_mm"].values()) > 4.2:
        raise AssertionError("Named-pad local TVS path exceeds provisional screen")
    if any(value["worst_contact_path_ohm"] >= 0.5
           for value in trace["balanced_4p4_planning_estimate_1khz"].values()):
        raise AssertionError("Even the conditional 1 kHz trace/contact estimate exceeds 0.5 Ω")
    check_board_netlist(board_path)

    # This frozen record is a replay of the engineer's chosen positions and
    # copper. It proves no extra automatic placement or hidden tracks entered
    # the review board; it is separate from electrical DRC/connectivity.
    source = pcbnew.LoadBoard(str(HERE / manual["source_board"]))
    original = {fp.GetReference(): fp for fp in source.GetFootprints()}
    actual_moves = {}
    for ref, fp in footprints.items():
        before = original[ref]
        if (fp.GetPosition().x, fp.GetPosition().y, fp.GetOrientationDegrees()) != (
                before.GetPosition().x, before.GetPosition().y,
                before.GetOrientationDegrees()):
            at = fp.GetPosition()
            actual_moves[ref] = [round(pcbnew.ToMM(at.x), 4),
                                 round(pcbnew.ToMM(at.y), 4),
                                 round(fp.GetOrientationDegrees() % 360, 3)]
    if actual_moves != manual["moved_footprints"]:
        raise AssertionError("Manual footprint move record differs from the PCB")

    def copper_item(item: pcbnew.BOARD_CONNECTED_ITEM) -> tuple:
        if isinstance(item, pcbnew.PCB_VIA):
            at = item.GetPosition()
            return ("via", item.GetNetname(), round(pcbnew.ToMM(at.x), 4),
                    round(pcbnew.ToMM(at.y), 4),
                    round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 4),
                    round(pcbnew.ToMM(item.GetDrillValue()), 4))
        a, b = item.GetStart(), item.GetEnd()
        return ("track", item.GetNetname(), item.GetLayerName(),
                round(pcbnew.ToMM(a.x), 4), round(pcbnew.ToMM(a.y), 4),
                round(pcbnew.ToMM(b.x), 4), round(pcbnew.ToMM(b.y), 4),
                round(pcbnew.ToMM(item.GetWidth()), 4))

    def manifest_item(item: dict) -> tuple:
        if item["kind"] == "via":
            return ("via", item["net"], *item["at_mm"],
                    item["diameter_mm"], item["drill_mm"])
        return ("track", item["net"], item["layer"],
                *item["start_mm"], *item["end_mm"], item["width_mm"])

    base_copper = collections.Counter(copper_item(item) for item in source.GetTracks())
    candidate_copper = collections.Counter(copper_item(item) for item in board.GetTracks())
    added_copper = collections.Counter(manifest_item(item)
                                       for item in manual["added_copper"])
    if candidate_copper != base_copper + added_copper:
        raise AssertionError("Manual copper record differs from the PCB")

    zone = board.Zones()[0]
    if (len(board.Zones()) != 1 or zone.GetNetname() != "GND"
            or not zone.HasFilledPolysForLayer(pcbnew.In1_Cu)
            or zone.GetFilledPolysList(pcbnew.In1_Cu).OutlineCount() != 1):
        raise AssertionError("L2 GND is not one saved filled polygon")
    segments = {
        (t.GetNetname(), t.GetLayer(), frozenset((
            (round(pcbnew.ToMM(t.GetStart().x), 3), round(pcbnew.ToMM(t.GetStart().y), 3)),
            (round(pcbnew.ToMM(t.GetEnd().x), 3), round(pcbnew.ToMM(t.GetEnd().y), 3)),
        ))): t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)
    }
    feedback_areas = {}
    for leg in CHANNELS:
        area = loop_area(leg)
        if area >= 5.0:
            raise AssertionError(f"{leg} feedback centreline loop is too large")
        feedback_areas[leg] = round(area, 3)
    for net, points in FEEDBACK.items():
        for index, (a, b) in enumerate(zip(points, points[1:])):
            track = segments.get((net, pcbnew.F_Cu, frozenset((a, b))))
            width = 0.25 if net.endswith("_OUT") and index == 0 else 0.2
            if track is None or abs(pcbnew.ToMM(track.GetWidth()) - width) > 0.001:
                raise AssertionError(f"Missing local feedback segment {net} {a}->{b}")

    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    pad_ids = {
        pad.m_Uuid.AsString(): (fp.GetReference(), pad.GetNumber())
        for fp in board.GetFootprints() for pad in fp.Pads()
    }

    def pad(ref: str, pin: str) -> pcbnew.PAD:
        return next(item for item in footprints[ref].Pads() if item.GetNumber() == pin)

    def group(ref: str, pin: str) -> set[tuple[str, str]]:
        return {pad_ids[item.m_Uuid.AsString()]
                for item in connectivity.GetConnectedItems(pad(ref, pin))
                if isinstance(item, pcbnew.PAD)}

    for leg, (opamp, out_pin, inn_pin, rf, cf, link, relay) in CHANNELS.items():
        if group(opamp, out_pin) != {
            (opamp, out_pin), (rf, "2"), (cf, "2"), (link, "1"),
        }:
            raise AssertionError(f"{leg} amplifier output/load/feedback copper differs")
        if group(opamp, inn_pin) != {(opamp, inn_pin), (rf, "1"), (cf, "1")}:
            raise AssertionError(f"{leg} feedback return copper differs")
        if (link, "2") not in group(relay, "4"):
            raise AssertionError(f"{leg} link-to-relay copper is open")
        if group(relay, "6") != JACK_GROUPS[leg]:
            raise AssertionError(f"{leg} relay-to-jack/contact/TVS copper differs")
    for opamp, pin, cap in (("U401", "1", "C402"), ("U401", "5", "C404"),
                            ("U402", "1", "C406"), ("U402", "5", "C408")):
        if (cap, "1") not in group(opamp, pin):
            raise AssertionError(f"{cap} input shunt signal is open")
        if not any(item.GetClass() == "ZONE"
                   for item in connectivity.GetConnectedItems(pad(cap, "2"))):
            raise AssertionError(f"{cap} input shunt has no L2 return")
    for ref, pin in (("U401", "3"), ("U402", "3"), ("J701", "1"),
                     ("J702", "1"), ("J702", "2")):
        if not any(item.GetClass() == "ZONE"
                   for item in connectivity.GetConnectedItems(pad(ref, pin))):
            raise AssertionError(f"{ref}.{pin} GND lacks L2 connection")
    for ref, pin in (("J701", "9"), ("J701", "10"),
                     ("J702", "5"), ("J702", "6")):
        if pad(ref, pin).GetNetname() or connectivity.GetConnectedItems(pad(ref, pin)):
            raise AssertionError(f"{ref}.{pin} must remain a physical no-connect")
    return {
        "board": board_path.name,
        "footprints": 544,
        "named_nets": 250,
        "manual_moves": len(manual["moved_footprints"]),
        "manual_added_copper_items": len(manual["added_copper"]),
        "drc_violations": 0,
        "bbox_overlaps": 0,
        "jlc_spacing_and_edge_proxy_findings": 0,
        "l2_gnd_filled_polygons": 1,
        "feedback_centreline_loop_area_mm2": feedback_areas,
        "local_tvs_routes_mm": tvs["local_routes_mm"],
        "balanced_4p4_planning_estimate_1khz": trace["balanced_4p4_planning_estimate_1khz"],
        "balanced_4p4_model_sensitivity_20khz": trace["balanced_4p4_model_sensitivity_20khz"],
        "drc_reported_unconnected_items": len(drc["unconnected_items"]),
        "ratsnest_unconnected_items": connectivity.GetUnconnectedCount(False),
        "routing_release": "HOLD: input/T networks, VPOS/VNEG/EP bypass, L3/L4 return, R-15 measurement, F01–F04 and G-3/G-4",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("board", "placement", "dfa", "fab", "drc", "tvs", "trace"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(check(args.board, args.placement, args.dfa, args.fab,
                              args.drc, args.tvs, args.trace), indent=2,
                        sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
