#!/usr/bin/env python3
"""Gate the three-resistor physical fit option, not its electrical release."""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path

import pcbnew

from audit_dfa_dfm import body_box, gap, outline, placed_refs
from manual_discharge_fit_option import LOCAL_ROUTES, MOVES, REPLACEMENTS, SOURCE


def xy(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    return round(pcbnew.ToMM(point.x), 4), round(pcbnew.ToMM(point.y), 4)


def tracks(board: pcbnew.BOARD) -> collections.Counter:
    result = collections.Counter()
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            key = ("via", item.GetNetname(), xy(item.GetPosition()),
                   round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 4),
                   round(pcbnew.ToMM(item.GetDrillValue()), 4))
        else:
            key = ("track", item.GetNetname(), item.GetLayerName(),
                   tuple(sorted((xy(item.GetStart()), xy(item.GetEnd())))),
                   round(pcbnew.ToMM(item.GetWidth()), 4))
        result[key] += 1
    return result


def pad(fp: pcbnew.FOOTPRINT, number: str) -> pcbnew.PAD:
    found = [item for item in fp.Pads() if item.GetNumber() == number]
    if len(found) != 1:
        raise AssertionError(f"{fp.GetReference()}.{number} pad changed")
    return found[0]


def audit(board_path: Path, placement_path: Path, dfa_path: Path,
          drc_path: Path, model_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    source = pcbnew.LoadBoard(str(SOURCE))
    placement = json.loads(placement_path.read_text())
    dfa = json.loads(dfa_path.read_text())
    drc = json.loads(drc_path.read_text())
    models = json.loads(model_path.read_text())
    target = {fp.GetReference(): fp for fp in board.GetFootprints()}
    original = {fp.GetReference(): fp for fp in source.GetFootprints()}
    if set(target) != set(original) or len(target) != 544:
        raise AssertionError("Fit option changed the component population")
    changes = set(REPLACEMENTS) | set(MOVES)
    for ref, fp in target.items():
        before = original[ref]
        if {pad.GetNumber(): pad.GetNetname() for pad in fp.Pads()} != {
                pad.GetNumber(): pad.GetNetname() for pad in before.Pads()}:
            raise AssertionError(f"Fit option changed {ref} pad nets")
        at = (*xy(fp.GetPosition()), round(fp.GetOrientationDegrees() % 360, 3))
        previous = (*xy(before.GetPosition()),
                    round(before.GetOrientationDegrees() % 360, 3))
        if ref not in changes and at != previous:
            raise AssertionError(f"Unrecorded fit-option move: {ref}")
        if ref not in REPLACEMENTS and fp.GetFPIDAsString() != before.GetFPIDAsString():
            raise AssertionError(f"Unrecorded fit-option footprint replacement: {ref}")
    for ref, (name, x_mm, y_mm, angle) in REPLACEMENTS.items():
        fp = target[ref]
        if (fp.GetFPIDAsString().split(":")[-1] != name
                or (*xy(fp.GetPosition()), round(fp.GetOrientationDegrees() % 360, 3))
                != (x_mm, y_mm, angle % 360)):
            raise AssertionError(f"Fit-option {ref} package/position changed")
    for ref, (x_mm, y_mm) in MOVES.items():
        if xy(target[ref].GetPosition()) != (x_mm, y_mm):
            raise AssertionError(f"Fit-option hand move changed: {ref}")
    extra = tracks(board) - tracks(source)
    missing = tracks(source) - tracks(board)
    wanted = collections.Counter()
    local_lengths = {}
    for source_ref, source_pin, target_ref, target_pin, width_mm in LOCAL_ROUTES:
        first = pad(target[source_ref], source_pin)
        last = pad(target[target_ref], target_pin)
        label = f"{source_ref}.{source_pin}→{target_ref}.{target_pin}"
        local_lengths[label] = round(math.dist(xy(first.GetPosition()),
                                               xy(last.GetPosition())), 3)
        wanted[("track", first.GetNetname(), "F.Cu",
                tuple(sorted((xy(first.GetPosition()), xy(last.GetPosition())))),
                width_mm)] += 1
    if missing or extra != wanted:
        raise AssertionError(f"Fit-option copper differs: missing={missing}, extra={extra}")
    if (placement["track_count"] != len(board.GetTracks())
            or placement["bbox_overlaps"] or drc["violations"]
            or dfa["package_pair_spacing_violation_count"]
            or dfa["board_edge_body_spacing_violation_count"]
            or not models["ok"]):
        raise AssertionError("Fit-option geometry, DRC, spacing or 3D screen failed")
    left, right, top, bottom = outline(board)
    fitted = placed_refs()
    bodies = {ref: body_box(fp, left, bottom)
              for ref, fp in target.items() if ref in fitted}
    edge = {}
    nearest = {}
    for ref in REPLACEMENTS:
        box = bodies[ref]
        edge[ref] = round(min(box[0], right-left-box[1], box[2], bottom-top-box[3]), 3)
        other_gap, other_ref = min((gap(box, candidate), candidate_ref)
                                   for candidate_ref, candidate in bodies.items()
                                   if candidate_ref != ref)
        nearest[ref] = {"ref": other_ref, "body_gap_mm": round(other_gap, 3)}
        if edge[ref] + 1e-6 < 2.5:
            raise AssertionError(f"{ref} body violates JLC's 2.5 mm edge minimum")
    return {
        "board": board_path.name,
        "source_board": SOURCE.name,
        "status": "physical-fit-option-only",
        "schematic_bom_aligned": False,
        "footprints": len(target),
        "track_and_via_items": len(board.GetTracks()),
        "vias": sum(isinstance(item, pcbnew.PCB_VIA) for item in board.GetTracks()),
        "added_local_routes": len(LOCAL_ROUTES),
        "local_copper_routes_mm": local_lengths,
        "bbox_overlaps": placement["bbox_overlaps"],
        "drc_violations": len(drc["violations"]),
        "drc_unconnected_items": len(drc["unconnected_items"]),
        "jlc_classified_pair_violations": dfa["package_pair_spacing_violation_count"],
        "candidate_body_to_edge_mm": edge,
        "candidate_nearest_fitted_body": nearest,
        "three_d_model_audit_ok": models["ok"],
        "holds": [
            "Board pads are KiCad IPC nominal; exact JLC pads conflict with FOJAN maker A/B land ranges, and Milliohm maker lands remain unchecked.",
            "The schematic and BOM still specify 0603 resistors; this option is not an assembly order.",
            "3V3A/3V3D/1V3 source feeds, temperature, shutdown timing and fault behavior are unverified.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("placement", type=Path)
    parser.add_argument("dfa", type=Path)
    parser.add_argument("drc", type=Path)
    parser.add_argument("models", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(audit(args.board, args.placement, args.dfa, args.drc,
                              args.models), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
