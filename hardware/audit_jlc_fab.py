#!/usr/bin/env python3
"""Read-only JLCPCB multilayer fabrication screen for the review board.

Sources: JLCPCB PCB capabilities (1 oz multilayer trace/space, annular ring,
plated-slot tolerance, silkscreen and edge clearance). It does not replace
JLC's uploaded Gerber and drill-file DFM review.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pcbnew


JLC_SLOT_POSITIVE_TOLERANCE_MM = 0.13
JLC_MULTILAYER_RING_ABSOLUTE_MM = 0.15
JLC_MULTILAYER_RING_RECOMMENDED_MM = 0.20
PROJECT_JACK_RING_TARGET_MM = 0.30


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def audit(path: Path) -> dict:
    board = pcbnew.LoadBoard(str(path))
    project = json.loads(path.with_suffix(".kicad_pro").read_text())
    rules = project["board"]["design_settings"]["rules"]
    required_project_floors = {
        "min_track_width": 0.15,       # design margin over JLC 1 oz 0.09 mm
        "min_clearance": 0.15,
        "min_copper_edge_clearance": 0.40,  # JLC V-cut edge
        "min_hole_clearance": 0.28,    # JLC PTH-to-track minimum
        "min_via_annular_width": 0.15, # JLC multilayer absolute ring (slow digital nets only; else 0.20)
        "min_via_diameter": 0.50,      # slow digital nets only (owner decision 5 Oct); else 0.60
        "min_silk_clearance": 0.15,
        "min_text_height": 1.0,
        "min_text_thickness": 0.15,
    }
    settings_below_target = {
        key: {"actual_mm": rules[key], "target_mm": target}
        for key, target in required_project_floors.items()
        if rules[key] + 1e-6 < target
    }
    slots = []
    for fp in board.GetFootprints():
        if fp.GetReference() not in {"J101", "J701", "J702"}:
            continue
        for pad in fp.Pads():
            if (pad.GetAttribute() != pcbnew.PAD_ATTRIB_PTH
                    or pad.GetDrillShape() != pcbnew.PAD_DRILL_SHAPE_OBLONG):
                continue
            copper = pad.GetSize()
            drill = pad.GetDrillSize()
            worst = min(
                (mm(copper.x) - mm(drill.x) - JLC_SLOT_POSITIVE_TOLERANCE_MM) / 2,
                (mm(copper.y) - mm(drill.y) - JLC_SLOT_POSITIVE_TOLERANCE_MM) / 2,
            )
            slots.append({
                "ref": fp.GetReference(), "pad": pad.GetNumber(),
                "copper_mm": [round(mm(copper.x), 3), round(mm(copper.y), 3)],
                "slot_mm": [round(mm(drill.x), 3), round(mm(drill.y), 3)],
                "worst_ring_mm": round(worst, 3),
                "meets_jlc_absolute": worst + 1e-6 >= JLC_MULTILAYER_RING_ABSOLUTE_MM,
                "meets_jlc_recommended": worst + 1e-6 >= JLC_MULTILAYER_RING_RECOMMENDED_MM,
                "meets_project_jack_target": (
                    worst + 1e-6 >= PROJECT_JACK_RING_TARGET_MM
                    if fp.GetReference() in {"J701", "J702"} else None),
            })
    slots.sort(key=lambda item: (item["ref"], item["pad"]))
    dru = path.with_suffix(".kicad_dru")
    digital = set()
    if dru.exists():
        text = dru.read_text()
        start = text.find('(rule "Slow digital control nets 0.15 mm"')
        if start >= 0:
            digital = set(re.findall(r"A\.NetName == '([^']+)'", text[start:text.find("\n\n", start)]))
    vias = []
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_VIA):
            continue
        drill = mm(item.GetDrillValue())
        diameter = mm(item.GetWidth(pcbnew.F_Cu))
        ring = (diameter - drill) / 2
        vias.append({
            "net": item.GetNetname(), "diameter_mm": round(diameter, 3),
            "drill_mm": round(drill, 3), "ring_mm": round(ring, 3),
            "through": item.GetViaType() == pcbnew.VIATYPE_THROUGH,
            "meets_project_target": (drill + 1e-6 >= 0.20
                                     and (diameter + 1e-6 >= 0.60 and ring + 1e-6 >= 0.20
                                          or item.GetNetname() in digital
                                          and diameter + 1e-6 >= 0.50 and ring + 1e-6 >= JLC_MULTILAYER_RING_ABSOLUTE_MM)
                                     and item.GetViaType() == pcbnew.VIATYPE_THROUGH),
        })
    return {
        "board": str(path),
        "jlc_source": "https://jlcpcb.com/capabilities/pcb-capabilities",
        "assumption": "4-layer FR-4, 1 oz outer copper; JLC plated-slot +0.13 mm size tolerance",
        "project_rule_targets_mm": required_project_floors,
        "project_settings_below_target": settings_below_target,
        "slot_ring_jlc_absolute_min_mm": JLC_MULTILAYER_RING_ABSOLUTE_MM,
        "slot_ring_jlc_recommended_min_mm": JLC_MULTILAYER_RING_RECOMMENDED_MM,
        "jack_design_target_mm": PROJECT_JACK_RING_TARGET_MM,
        "plated_slots": slots,
        "vias": vias,
        "via_target_failure_count": sum(not via["meets_project_target"] for via in vias),
        "jlc_absolute_ring_failure_count": sum(not slot["meets_jlc_absolute"] for slot in slots),
        "jlc_recommended_ring_failure_count": sum(not slot["meets_jlc_recommended"] for slot in slots),
        "project_jack_ring_open_count": sum(
            slot["meets_project_jack_target"] is False for slot in slots),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    args = parser.parse_args()
    result = audit(args.board)
    print(json.dumps(result, indent=2, sort_keys=True))
    if (result["project_settings_below_target"]
            or result["jlc_absolute_ring_failure_count"]
            or result["via_target_failure_count"]):
        raise SystemExit("JLCPCB fabrication-rule screen failed")


if __name__ == "__main__":
    main()
