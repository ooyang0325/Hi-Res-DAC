#!/usr/bin/env python3
"""Gate repeatable manual geometry checks without declaring routing complete."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


J701_ACCESS_NEIGHBORS = {
    "D701", "D702", "D703", "D704",
    "R406", "R407", "R408", "R410", "R440",
}


def check(placement_path: Path, dfa_path: Path, drc_path: Path,
          require_timer_feasible: bool = False, esd_limit_mm: float = 3.0,
          require_clean_drc: bool = False) -> dict:
    placement = json.loads(placement_path.read_text())
    dfa = json.loads(dfa_path.read_text())
    drc = json.loads(drc_path.read_text())
    if placement["bbox_overlaps"]:
        raise SystemExit(f"Footprint bounding-box overlaps: {placement['bbox_overlaps']}")
    if placement["footprints"] != 536 or placement["named_nets"] != 246:
        raise SystemExit("Manual placement differs from the captured PCB population")
    if dfa["outline_mm"] != placement["size_mm"]:
        raise SystemExit("Requested audit size differs from the actual Edge.Cuts outline")
    if require_timer_feasible:
        impossible = [f"{channel}.{part}"
                      for channel, parts in
                      placement["protection_timer_pad_distance_mm"].items()
                      for part, lengths in parts.items()
                      if lengths["manhattan_pad_lower_bound_mm"] > 8.0]
        if impossible:
            raise SystemExit(f"Timer paths cannot fit the 8 mm rule: {impossible}")
    if dfa["package_pair_spacing_violation_count"]:
        raise SystemExit("JLC package-body spacing proxy has violations")
    if dfa["board_edge_body_spacing_violation_count"]:
        raise SystemExit("JLC component-body-to-edge proxy has violations")
    connector_edge_exceptions = [item["ref"] for item in
                                 dfa["unclassified_body_edge_concerns"]]
    # J201/J202: ECO F05 programming headers, still at the historical boards' debug-pad positions.
    if set(connector_edge_exceptions) - {"J101", "J702", "J201", "J202"}:
        raise SystemExit(f"New unclassified component-edge concerns: {connector_edge_exceptions}")
    if any(dfa["l1_output_corridor_blockers"].values()):
        raise SystemExit("A manually reserved L1 headphone corridor is blocked")
    known_holds = []
    unexpected = []
    for violation in drc["violations"]:
        refs = {item["description"].removeprefix("Footprint ")
                for item in violation["items"]}
        if (violation["type"] == "courtyards_overlap"
                and "J701" in refs
                and len(refs) == 2
                and next(iter(refs - {"J701"})) in J701_ACCESS_NEIGHBORS):
            known_holds.append(next(iter(refs - {"J701"})))
        else:
            unexpected.append(violation)
    if unexpected:
        raise SystemExit(f"Unexpected KiCad DRC violations: {unexpected[:3]}")
    if require_clean_drc and known_holds:
        raise SystemExit(f"J701 hand-access DRC errors remain: {sorted(known_holds)}")
    esd_over_limit = sorted(ref for ref, details in
                          placement["esd_to_nearest_jack_pad_mm"].items()
                          if details["distance_mm"] > esd_limit_mm + 1e-6)
    if esd_over_limit:
        raise SystemExit(f"J701 TVS pad distances exceed {esd_limit_mm} mm: {esd_over_limit}")
    return {
        "board": placement["board"],
        "outline_mm": dfa["outline_mm"],
        "footprints": placement["footprints"],
        "named_nets": placement["named_nets"],
        "footprint_overlaps": 0,
        "jlc_package_pair_body_proxy_violations": 0,
        "jlc_body_edge_proxy_violations": 0,
        "jlc_connector_edge_exceptions_pending_panel_review": connector_edge_exceptions,
        "jlc_unclassified_package_refs": len(dfa["jlc_unclassified_refs"]),
        "l1_output_corridor_blockers": 0,
        "protection_timer_manhattan_lower_bound_max_mm": max(
            lengths["manhattan_pad_lower_bound_mm"]
            for parts in placement["protection_timer_pad_distance_mm"].values()
            for lengths in parts.values()),
        "known_j701_hand_access_drc_holds": sorted(known_holds),
        "esd_signal_pad_max_mm": max(
            details["distance_mm"] for details in
            placement["esd_to_nearest_jack_pad_mm"].values()),
        "esd_limit_mm": esd_limit_mm,
        "esd_refs_over_limit": esd_over_limit,
        "track_count": placement["track_count"],
        "zone_count": placement["zone_count"],
        "unconnected_items": len(drc["unconnected_items"]),
        "routing_release": "HOLD",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("placement", type=Path)
    parser.add_argument("dfa", type=Path)
    parser.add_argument("drc", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--require-timer-feasible", action="store_true")
    parser.add_argument("--esd-limit-mm", type=float, default=3.0)
    parser.add_argument("--require-clean-drc", action="store_true")
    args = parser.parse_args()
    summary = check(args.placement, args.dfa, args.drc,
                    args.require_timer_feasible, args.esd_limit_mm,
                    args.require_clean_drc)
    result = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
