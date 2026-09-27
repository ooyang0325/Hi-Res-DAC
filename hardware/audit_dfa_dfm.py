#!/usr/bin/env python3
"""Screen a reviewed board against JLC assembly spacing and route corridors.

This is a read-only audit. It never chooses or moves footprint positions.
F.Fab drawing rectangles are a proxy for component bodies; JLC's package-pair
table and final DFM inspection remain authoritative.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
MATRIX = {
    "0201": {"0201": .15, "0402": .15, "0603": .18, "0805": .18,
             "1206": .25, "QFN": 1.0, "QFP": .5, "SOP": .4, "SOT": .2, "BGA": 1.0},
    "0402": {"0402": .15, "0603": .18, "0805": .18,
             "1206": .25, "QFN": 1.0, "QFP": .5, "SOP": .4, "SOT": .2, "BGA": 1.0},
    "0603": {"0603": .18, "0805": .18, "1206": .25, "QFN": 1.0,
             "QFP": .5, "SOP": .4, "SOT": .2, "BGA": 1.0},
    "0805": {"0805": .25, "1206": .35, "QFN": 1.0,
             "QFP": .5, "SOP": .4, "SOT": .2, "BGA": 1.0},
    "1206": {"1206": .35, "QFN": 1.0, "QFP": .5,
             "SOP": .4, "SOT": .2, "BGA": 1.0},
    "QFN": {"QFN": 1.0, "QFP": 1.25, "SOP": 1.0,
            "SOT": 1.0, "BGA": 1.5},
    "QFP": {"QFP": 1.25, "SOP": 1.25, "SOT": 1.0, "BGA": 1.5},
    "SOP": {"SOP": .5, "SOT": .4, "BGA": 1.0},
    "SOT": {"SOT": .4, "BGA": 1.0},
    "BGA": {"BGA": 2.0},
}
for left, pairs in list(MATRIX.items()):
    for right, value in pairs.items():
        MATRIX[right][left] = value

# Hand-defined L1 output passages between the jacks and their relays. Their
# ESD diodes are allowed at the ends; every other component must stay clear.
CORRIDORS = {
    "J702_to_lower_relays": (85.0, 100.0, 35.2, 41.4),
    "lower_relays_to_J701": (78.0, 100.0, 55.6, 58.9),
}
CORRIDOR_ALLOWED = {"J701", "J702", "K601", "K603", "D701", "D702"}


def placed_refs() -> set[str]:
    with (HERE / "JLCPCB_BOM_REVIEW_ONLY.csv").open(encoding="utf-8-sig", newline="") as handle:
        return {ref.strip() for row in csv.DictReader(handle)
                for ref in row["Designator"].split(",")}


def component_class(fp: pcbnew.FOOTPRINT) -> str | None:
    name = fp.GetFPIDAsString().split(":")[-1]
    for size in ("0201", "0402", "0603", "0805", "1206"):
        if re.search(rf"[_-]{size}(?:[_-]|$)", name):
            return size
    if any(token in name for token in ("QFN", "WSON", "VSON", "DFN")):
        return "QFN"
    if "QFP" in name:
        return "QFP"
    if any(token in name for token in ("SOP", "SOIC", "TSSOP", "VSSOP", "ESOP")):
        return "SOP"
    if any(token in name for token in ("SOT", "SC-88")):
        return "SOT"
    if "BGA" in name:
        return "BGA"
    return None


def outline(board: pcbnew.BOARD) -> tuple[float, float, float, float]:
    points = [point for drawing in board.GetDrawings()
              if drawing.GetLayer() == pcbnew.Edge_Cuts
              for point in (drawing.GetStart(), drawing.GetEnd())]
    return (min(pcbnew.ToMM(point.x) for point in points),
            max(pcbnew.ToMM(point.x) for point in points),
            min(pcbnew.ToMM(point.y) for point in points),
            max(pcbnew.ToMM(point.y) for point in points))


def box(fp: pcbnew.FOOTPRINT, left: float, bottom: float
        ) -> tuple[float, float, float, float]:
    bb = fp.GetBoundingBox(False, False)
    return (pcbnew.ToMM(bb.GetLeft()) - left,
            pcbnew.ToMM(bb.GetRight()) - left,
            bottom - pcbnew.ToMM(bb.GetBottom()),
            bottom - pcbnew.ToMM(bb.GetTop()))


def body_box(fp: pcbnew.FOOTPRINT, left: float, bottom: float
             ) -> tuple[float, float, float, float]:
    shapes = [item.GetBoundingBox() for item in fp.GraphicalItems()
              if item.GetLayer() == pcbnew.F_Fab
              and not isinstance(item, pcbnew.PCB_TEXT)]
    if not shapes:
        return box(fp, left, bottom)
    return (min(pcbnew.ToMM(bb.GetLeft()) for bb in shapes) - left,
            max(pcbnew.ToMM(bb.GetRight()) for bb in shapes) - left,
            bottom - max(pcbnew.ToMM(bb.GetBottom()) for bb in shapes),
            bottom - min(pcbnew.ToMM(bb.GetTop()) for bb in shapes))


def gap(a: tuple[float, float, float, float],
        b: tuple[float, float, float, float]) -> float:
    return math.hypot(max(0.0, a[0] - b[1], b[0] - a[1]),
                      max(0.0, a[2] - b[3], b[2] - a[3]))


def overlaps(a: tuple[float, float, float, float],
             b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def audit(path: Path) -> dict:
    board = pcbnew.LoadBoard(str(path))
    left, right, top, bottom = outline(board)
    width = right - left
    height = bottom - top
    fitted = placed_refs()
    entries = [(fp.GetReference(), component_class(fp),
                body_box(fp, left, bottom))
               for fp in board.GetFootprints() if fp.GetReference() in fitted]
    spacing = []
    for index, (left_ref, left_class, left_box) in enumerate(entries):
        if left_class is None:
            continue
        for right_ref, right_class, right_box in entries[index + 1:]:
            if right_class is None:
                continue
            required = MATRIX[left_class][right_class]
            actual = gap(left_box, right_box)
            if actual + 1e-6 < required:
                spacing.append({"refs": [left_ref, right_ref],
                                "classes": [left_class, right_class],
                                "gap_mm": round(actual, 3),
                                "jlc_min_mm": required})
    spacing.sort(key=lambda item: item["gap_mm"] - item["jlc_min_mm"])

    edge = []
    unclassified_edge = []
    for ref, klass, rect in entries:
        distance = min(rect[0], width - rect[1], rect[2], height - rect[3])
        if distance < 2.5:
            item = {"ref": ref, "class": klass,
                    "body_to_edge_mm": round(distance, 3),
                    "jlc_body_min_mm": 2.5}
            (unclassified_edge if klass is None else edge).append(item)
    edge.sort(key=lambda item: item["body_to_edge_mm"])
    unclassified_edge.sort(key=lambda item: item["body_to_edge_mm"])

    all_boxes = {fp.GetReference(): box(fp, left, bottom)
                 for fp in board.GetFootprints()}
    corridor_shift = height - 100.0
    corridor_x_shift = width - 100.0
    passages = {name: sorted(ref for ref, rect in all_boxes.items()
                             if ref not in CORRIDOR_ALLOWED and overlaps(
                                 rect, (region[0] + corridor_x_shift,
                                        region[1] + corridor_x_shift,
                                        region[2] + corridor_shift,
                                        region[3] + corridor_shift)))
                for name, region in CORRIDORS.items()}
    return {
        "board": str(path),
        "outline_mm": [round(width, 3), round(height, 3)],
        "method": "F.Fab drawing rectangles where available, otherwise footprint bounds; body-spacing proxy",
        "jlc_source": "https://jlcpcb.com/help/article/minimum-spacing-for-smd-components",
        "jlc_placed_refs": len(fitted),
        "jlc_classified_refs": len(entries) - sum(klass is None for _, klass, _ in entries),
        "jlc_unclassified_refs": sorted(ref for ref, klass, _ in entries
                                        if klass is None),
        "package_pair_spacing_violation_count": len(spacing),
        "package_pair_spacing_worst_40": spacing[:40],
        "package_pair_violations_by_class": dict(Counter(
            "/".join(sorted(item["classes"])) for item in spacing)),
        "board_edge_body_spacing_violation_count": len(edge),
        "board_edge_body_spacing_violations": edge,
        "unclassified_body_edge_concerns": unclassified_edge,
        "l1_output_corridor_blockers": passages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.board), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
