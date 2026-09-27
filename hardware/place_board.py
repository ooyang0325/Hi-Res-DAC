#!/usr/bin/env python3
"""Populate and provisionally place DAC-HPA's editable KiCad board.

This consumes the current schematic netlist, keeps symbol paths and pad nets,
places the fixed connectors/ICs from Notes v1.0 Section 9.1, and packs the
remaining footprints by functional region and local connectivity. It does not
route, pour copper, or create fabrication outputs. Existing board edits are
preserved unless --force is explicitly supplied.
"""

from __future__ import annotations

import argparse
import collections
import math
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SCHEMATIC = HERE / "DAC_HPA.kicad_sch"
OUTPUT = HERE / "DAC_HPA.kicad_pcb"
REPORT = HERE / "PLACEMENT_REPORT.md"
BOARD_X = 40.0  # KiCad top-left, mm
BOARD_Y = 40.0
WIDTH = 100.0
HEIGHT = 80.0
GRID = 0.5
CELL = 5.0

# Coordinates in the Notes: origin at the board's bottom-left, +y upward.
ANCHORS: dict[str, tuple[float, float, int]] = {
    "MH1": (3.5, 3.5, 0), "MH2": (3.5, 76.5, 0),
    "MH3": (96.5, 3.5, 0), "MH4": (96.5, 76.5, 0),
    "J101": (5.0, 50.0, 270),
    "J701": (86.5, 58.5, 180),
    "J702": (90.84, 16.5, 180),
    "D701": (80.5, 66.0, 0), "D703": (86.5, 66.0, 0),
    "D702": (89.5, 66.0, 0), "D704": (92.5, 66.0, 0),
    "J201": (12.0, 77.0, 0), "J202": (33.0, 77.0, 0),
    "J703": (65.0, 8.5, 0),
    "K602": (80.0, 45.0, 0), "K604": (93.0, 45.0, 0),
    "K601": (80.0, 29.5, 0), "K603": (93.0, 29.5, 0),
    "D102": (15.5, 47.5, 180),
    "U101": (10.0, 58.0, 0), "U102": (16.0, 38.0, 0),
    "U103": (11.0, 53.0, 0), "U502": (6.0, 34.0, 0),
    "Q507": (12.2, 38.0, 0),
    "U201": (25.0, 67.0, 0), "U202": (42.0, 66.0, 0),
    "U208": (47.1, 66.0, 0), "Y201": (18.0, 55.0, 0),
    "X202": (36.0, 58.5, 0), "X203": (41.0, 58.5, 0),
    "U205": (40.0, 54.5, 0),
    "U301": (50.0, 49.0, 0), "U302": (44.0, 54.5, 0),
    "U303": (62.0, 75.0, 0), "X201": (50.0, 38.5, 0),
    "U206": (45.0, 38.5, 0), "U607": (50.0, 43.0, 0),
    "U605": (36.0, 45.0, 0),
    "U403": (60.0, 57.0, 0), "U404": (60.0, 44.0, 0),
    "U401": (70.0, 57.0, 0), "U402": (70.0, 44.0, 0),
    "C442": (63.0, 66.0, 0), "C443": (61.0, 34.0, 0),
    "U501": (22.0, 13.0, 0), "U503": (14.0, 18.0, 0),
    "U504": (11.0, 7.0, 0), "U505": (21.0, 22.0, 0),
    "U603": (42.0, 27.0, 0), "U606": (49.0, 27.0, 0),
    "U609": (57.0, 25.0, 0), "U610": (65.0, 25.0, 0),
    "U611": (42.0, 15.0, 0), "U612": (50.0, 15.0, 0),
    "U608": (53.0, 34.0, 0), "U604": (71.3, 29.0, 0),
    "U613": (49.0, 75.0, 0), "U614": (55.0, 75.0, 0),
    "U615": (49.0, 58.5, 0), "U616": (55.0, 64.5, 0),
    "U617": (25.0, 53.0, 0), "U618": (30.0, 53.0, 0),
    "U619": (25.0, 43.0, 0), "U620": (30.0, 43.0, 0),
}

ROOMS: dict[str, tuple[float, float, float, float]] = {
    "Z1": (0, 20, 30, 58),
    "Z2": (0, 46, 58, 80),
    "Z3": (32, 53, 52, 65),
    "Z4U": (46, 58, 58, 80),
    "Z4L": (40, 58, 36, 58),
    "Z4S": (18, 40, 36, 58),
    "Z5": (57, 79, 29, 80),
    "Z6": (75, 100, 0, 80),
    "Z6B": (58, 78, 0, 12),
    "Z7A": (30, 58, 0, 36),
    "Z7B": (58, 78, 12, 30),
    "Z8A": (0, 30, 0, 30),
    "Z8B": (18, 30, 30, 36),
    "ALL": (0, 100, 0, 80),
}

POWER_NAMES = {
    "GND", "VBUS", "5V_SYS", "5V_ANA", "3V3A", "3V3D", "3V3M",
    "VPOS", "VNEG", "1V3", "AVCC", "DVCC", "VCCA", "VCCD",
}


@dataclass(frozen=True)
class Rect:
    left: float
    right: float
    bottom: float
    top: float

    def expanded(self, gap: float) -> "Rect":
        return Rect(self.left - gap, self.right + gap, self.bottom - gap, self.top + gap)

    def intersects(self, other: "Rect") -> bool:
        return self.left < other.right and other.left < self.right and self.bottom < other.top and other.bottom < self.top


@dataclass
class Part:
    ref: str
    value: str
    footprint_id: str
    footprint: pcbnew.FOOTPRINT
    path: str
    nets: set[str]
    room: str
    bbox: dict[int, Rect]


def mm(v: int) -> float:
    return pcbnew.ToMM(v)


def vec(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def board_position(x: float, y: float) -> pcbnew.VECTOR2I:
    return vec(BOARD_X + x, BOARD_Y + HEIGHT - y)


def local_box(fp: pcbnew.FOOTPRINT, angle: int) -> Rect:
    fp.SetPosition(vec(0, 0))
    fp.SetOrientationDegrees(angle)
    box = fp.GetBoundingBox(False, False)
    return Rect(mm(box.GetX()), mm(box.GetX() + box.GetWidth()),
                -mm(box.GetY() + box.GetHeight()), -mm(box.GetY()))


def at(box: Rect, x: float, y: float) -> Rect:
    return Rect(box.left + x, box.right + x, box.bottom + y, box.top + y)


def footprint_library(lib: str) -> Path:
    if lib in {"DAC_HPA", "JLC_Imported"}:
        return HERE / f"{lib}.pretty"
    for root in (
        os.environ.get("KICAD10_FOOTPRINT_DIR"),
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
        "/usr/share/kicad/footprints",
    ):
        if root and (p := Path(root) / f"{lib}.pretty").is_dir():
            return p
    raise FileNotFoundError(f"footprint library {lib}")


def netlist_xml() -> ET.Element:
    cli = shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "DAC_HPA.xml"
        result = subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadxml",
                                 "-o", str(path), str(SCHEMATIC)], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return ET.parse(path).getroot()


def number(ref: str) -> int:
    match = re.search(r"\d+", ref)
    return int(match.group()) if match else 0


def room_for(ref: str) -> str:
    num = number(ref)
    if ref.startswith("FID"):
        return "ALL"
    if ref in {"U502", "Q507", "C502", "R537", "R538"}:
        return "Z1"
    if ref in {"R446", "R447"}:  # DNF VREF trims beside the DAC reference network
        return "Z4U"
    if ref.startswith("TP"):
        return "ALL"
    if ref.startswith("MH"):
        return "ALL"
    if ref in {"X201", "U206", "U607", "R665", "R203", "R227", "C217", "C223", "R235", "R645"}:
        return "Z4L"
    if ref in {"X202", "X203", "U205", "R210", "R211", "R215"}:
        return "Z3"
    if ref in {"U605", "Q619", "Q620", "C624", "D609", "C625", "R666"} or 675 <= num <= 689 and ref.startswith("R"):
        return "Z4S"
    if ref.startswith("U") and 613 <= num <= 616:
        return "Z4U"
    if ref.startswith("U") and 617 <= num <= 620:
        return "Z4S"
    if ref.startswith("C") and 647 <= num <= 650 or ref.startswith("R") and 942 <= num <= 945 or ref.startswith("C") and 659 <= num <= 662:
        return "Z4U"
    if ref.startswith("C") and 651 <= num <= 654 or ref.startswith("R") and 946 <= num <= 949 or ref.startswith("C") and 663 <= num <= 666:
        return "Z4S"
    if ref in {"R930", "R931", "C643", "C644"}:
        return "Z4U"
    if ref in {"R932", "R933", "C645", "C646"}:
        return "Z4S"
    if ref in {"U604", "Q612", "Q614", "Q616", "Q617", "Q622", "R641", "R642", "R643", "R644", "R692", "R696"}:
        return "Z6"
    if ref.startswith("J") and num >= 700 or ref.startswith("K"):
        return "Z6"
    if ref.startswith("J") and num < 200 or num < 200:
        return "Z1"
    if num < 300:
        return "Z2"
    if num < 400:
        return "Z4L"
    if num < 500:
        return "Z5"
    if num < 600:
        return "Z8A"
    if num < 700:
        return "Z7A"
    return "Z6"


def parse_parts(root: ET.Element) -> tuple[dict[str, Part], dict[str, list[tuple[str, str]]]]:
    components = root.findall("./components/comp")
    net_nodes: dict[str, list[tuple[str, str]]] = {}
    ref_nets: dict[str, set[str]] = collections.defaultdict(set)
    for item in root.findall("./nets/net"):
        name = item.get("name") or ""
        net_nodes[name] = [(node.get("ref") or "", node.get("pin") or "") for node in item.findall("node")]
        for ref, _ in net_nodes[name]:
            ref_nets[ref].add(name)
    parts = {}
    for comp in components:
        ref = comp.get("ref") or ""
        fp_id = comp.findtext("footprint") or ""
        lib, name = fp_id.split(":", 1)
        fp = pcbnew.FootprintLoad(str(footprint_library(lib)), name)
        if fp is None:
            raise FileNotFoundError(fp_id)
        fp.SetFPIDAsString(fp_id)
        sheetpath = comp.find("sheetpath")
        timestamp = comp.findtext("tstamps") or ""
        path = (sheetpath.get("tstamps") if sheetpath is not None else "/") + timestamp
        fp.SetReference(ref)
        fp.SetValue(comp.findtext("value") or "")
        fp.SetPath(pcbnew.KIID_PATH(path))
        fp.SetSheetname(comp.find("property[@name='Sheetname']").get("value") if comp.find("property[@name='Sheetname']") is not None else "")
        fp.SetSheetfile(comp.find("property[@name='Sheetfile']").get("value") if comp.find("property[@name='Sheetfile']") is not None else "")
        if comp.find("exclude_from_bom") is not None:
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
        if comp.find("exclude_from_board") is not None:
            raise ValueError(f"board-excluded component in netlist: {ref}")
        fp.Reference().SetLayer(pcbnew.F_Fab)
        fp.Reference().SetVisible(True)
        fp.Value().SetVisible(False)
        parts[ref] = Part(ref, comp.findtext("value") or "", fp_id, fp, path,
                          ref_nets[ref], room_for(ref), {angle: local_box(fp, angle) for angle in (0, 90, 180, 270)})
    return parts, net_nodes


def clearance(ref: str) -> float:
    if ref.startswith("TP"):
        return 0.55
    if ref.startswith("FID"):
        return 1.0
    if ref in {"C631", "C632", "C633", "C634"}:
        return 0.75
    if ref.startswith("K6"):
        return 0.45
    if ref.startswith("MH"):
        return 0.0
    return 0.10


class Occupancy:
    def __init__(self) -> None:
        self.items: list[tuple[str, Rect, float]] = []
        self.cells: dict[tuple[int, int], set[int]] = collections.defaultdict(set)

    def keys(self, rect: Rect) -> list[tuple[int, int]]:
        return [(i, j)
                for i in range(math.floor(rect.left / CELL), math.floor(rect.right / CELL) + 1)
                for j in range(math.floor(rect.bottom / CELL), math.floor(rect.top / CELL) + 1)]

    def collision(self, rect: Rect, gap: float) -> str | None:
        expanded = rect.expanded(gap)
        indices = set().union(*(self.cells.get(key, set()) for key in self.keys(expanded)))
        for index in indices:
            ref, other, other_gap = self.items[index]
            if expanded.intersects(other.expanded(other_gap)):
                return ref
        return None

    def add(self, ref: str, rect: Rect) -> None:
        gap = clearance(ref)
        index = len(self.items)
        self.items.append((ref, rect, gap))
        for key in self.keys(rect.expanded(gap)):
            self.cells[key].add(index)


def inside_board(rect: Rect, ref: str) -> bool:
    if ref == "J101":  # its shell overhang and edge guide are intentional
        return rect.left >= -0.35 and rect.right <= WIDTH - 0.5 and 0.5 <= rect.bottom and rect.top <= HEIGHT - 0.5
    if ref in {"J701", "J702"}:  # connector edge courtyards may overhang by a drawing hairline
        return rect.left >= 0 and rect.right <= WIDTH + 0.1 and rect.bottom >= 0 and rect.top <= HEIGHT
    if ref.startswith("MH"):  # Ø7.05 courtyard rounds 0.025 mm beyond the nominal Ø7 keep-out
        return rect.left >= -0.05 and rect.right <= WIDTH + 0.05 and rect.bottom >= -0.05 and rect.top <= HEIGHT + 0.05
    return 0 <= rect.left and rect.right <= WIDTH and 0 <= rect.bottom and rect.top <= HEIGHT


def place(fp: pcbnew.FOOTPRINT, x: float, y: float, angle: int) -> None:
    fp.SetOrientationDegrees(angle)
    fp.SetPosition(board_position(x, y))


def region_sequence(room: str) -> list[str]:
    alternatives = {
        "Z1": ["Z1", "Z4S", "Z2"],
        "Z2": ["Z2", "Z3", "Z4U", "Z4S"],
        "Z3": ["Z3", "Z2", "Z4L", "Z4S"],
        "Z4U": ["Z4U", "Z4L", "Z4S", "Z5"],
        "Z4L": ["Z4L", "Z4U", "Z4S", "Z5"],
        "Z4S": ["Z4S", "Z4L", "Z7A", "Z2"],
        "Z5": ["Z5", "Z4U", "Z4L", "Z6"],
        "Z6": ["Z6", "Z6B", "Z7B", "Z5"],
        "Z7A": ["Z7A", "Z7B", "Z4S", "Z8B"],
        "Z7B": ["Z7B", "Z7A", "Z6", "Z5"],
        "Z8A": ["Z8A", "Z8B", "Z7A", "Z1"],
        "Z8B": ["Z8B", "Z8A", "Z7A", "Z4S"],
        "ALL": ["ALL"],
    }
    return alternatives[room] + ([] if room == "ALL" else ["ALL"])


def custom_target(ref: str, placed: dict[str, tuple[float, float, int]]) -> tuple[float, float] | None:
    num = number(ref)
    timer_targets = {"C647": (49, 70), "C648": (55, 70),
                     "C649": (45, 58), "C650": (55, 58)}
    if ref in timer_targets:
        return timer_targets[ref]
    if ref.startswith("C") and 647 <= num <= 654:
        anchor = f"U{613 + num - 647}"
        return placed.get(anchor, (0, 0, 0))[:2]
    if ref.startswith("R") and 942 <= num <= 949:
        return placed.get(f"U{613 + num - 942}", (0, 0, 0))[:2]
    if ref.startswith("C") and 659 <= num <= 666:
        return placed.get(f"U{613 + num - 659}", (0, 0, 0))[:2]
    if ref in {"R930", "C643"}:
        return (52, 75)
    if ref in {"R931", "C644"}:
        return (52, 65)
    if ref in {"R932", "C645"}:
        return (27.5, 53)
    if ref in {"R933", "C646"}:
        return (27.5, 43)
    if ref in {"C631", "C632"}:
        return (58, 18)
    if ref in {"C633", "C634"}:
        return (65, 18)
    if ref in {"R509", "R510", "C505"}:
        return (19, 18)
    if ref == "R665":
        return (53, 44.5)
    if ref in {"R203", "R227", "C217"}:
        return (52, 38.5)
    if ref in {"C223", "R235", "R645"}:
        return (45, 38.5)
    if ref in {"C104", "R108", "R109"}:
        return (16, 38)
    if ref in {"R537", "R538"}:
        return (12.5, 38)
    if ref == "TP732":
        return (12, 74)
    return None


def priority(ref: str) -> int:
    num = number(ref)
    if ref.startswith("C") and 659 <= num <= 666:
        return 0  # comparator supply decoupling has almost no placement freedom
    if ref.startswith("C") and 647 <= num <= 654 or ref.startswith("R") and 942 <= num <= 949:
        return 1  # LPW timer nodes
    if ref in {"R665", "R203", "R227", "C217", "C223", "C624", "D609", "C625", "R666",
               "C104", "R509", "R510", "C631", "C632", "C633", "C634"}:
        return 2
    if ref in {"R930", "R931", "R932", "R933", "C643", "C644", "C645", "C646"}:
        return 3
    if ref.startswith("D") and 701 <= num <= 704:
        return 3
    return 10


def target_for(part: Part, placed: dict[str, tuple[float, float, int]],
               net_nodes: dict[str, list[tuple[str, str]]],
               ref_rooms: dict[str, str]) -> tuple[float, float]:
    special = custom_target(part.ref, placed)
    if special and special != (0, 0):
        return special
    region = ROOMS[part.room]
    base = ((region[0] + region[1]) / 2, (region[2] + region[3]) / 2)
    neighbors = []
    for net in part.nets:
        if net in POWER_NAMES:
            continue
        refs = [ref for ref, _ in net_nodes[net] if ref != part.ref]
        if len(refs) > 9:
            continue
        for ref in refs:
            if ref in placed and not ref.startswith("TP") and ref_rooms.get(ref) == part.room:
                x, y, _ = placed[ref]
                weight = 1 / max(1, len(refs))
                if ref.startswith(("U", "J", "K", "X", "Y")):
                    weight *= 2
                neighbors.append((x, y, weight))
    if neighbors:
        weight = sum(item[2] for item in neighbors)
        near = (sum(x * w for x, _, w in neighbors) / weight,
                sum(y * w for _, y, w in neighbors) / weight)
        return (base[0] * 0.25 + near[0] * 0.75,
                base[1] * 0.25 + near[1] * 0.75)
    return base


def grid_points(room: str, target: tuple[float, float]) -> list[tuple[float, float]]:
    left, right, bottom, top = ROOMS[room]
    xs = range(math.ceil(left / GRID), math.floor(right / GRID) + 1)
    ys = range(math.ceil(bottom / GRID), math.floor(top / GRID) + 1)
    points = [(i * GRID, j * GRID) for i in xs for j in ys]
    points.sort(key=lambda p: (p[0] - target[0]) ** 2 + (p[1] - target[1]) ** 2)
    return points


def find_spot(part: Part, target: tuple[float, float], occupied: Occupancy) -> tuple[float, float, int, str]:
    for room in region_sequence(part.room):
        for x, y in grid_points(room, target):
            for angle in (0, 90):
                rect = at(part.bbox[angle], x, y)
                if not inside_board(rect, part.ref):
                    continue
                if occupied.collision(rect, clearance(part.ref)) is None:
                    return x, y, angle, room
    raise RuntimeError(f"cannot place {part.ref} ({part.footprint_id}) in any room")


def add_edge(board: pcbnew.BOARD) -> None:
    # Four 98/78 mm straight runs plus four R1 corners.
    x0, y0, x1, y1, r = BOARD_X, BOARD_Y, BOARD_X + WIDTH, BOARD_Y + HEIGHT, 1.0
    lines = [((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)),
             ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + r))]
    for start, end in lines:
        item = pcbnew.PCB_SHAPE(board)
        item.SetShape(pcbnew.SHAPE_T_SEGMENT)
        item.SetLayer(pcbnew.Edge_Cuts)
        item.SetWidth(pcbnew.FromMM(0.05))
        item.SetStart(vec(*start))
        item.SetEnd(vec(*end))
        board.Add(item)
    k = math.sqrt(0.5)
    arcs = [
        ((x1 - r, y0), (x1 - r + r * k, y0 + r - r * k), (x1, y0 + r)),
        ((x1, y1 - r), (x1 - r + r * k, y1 - r + r * k), (x1 - r, y1)),
        ((x0 + r, y1), (x0 + r - r * k, y1 - r + r * k), (x0, y1 - r)),
        ((x0, y0 + r), (x0 + r - r * k, y0 + r - r * k), (x0 + r, y0)),
    ]
    for start, middle, end in arcs:
        item = pcbnew.PCB_SHAPE(board)
        item.SetShape(pcbnew.SHAPE_T_ARC)
        item.SetArcGeometry(vec(*start), vec(*middle), vec(*end))
        item.SetLayer(pcbnew.Edge_Cuts)
        item.SetWidth(pcbnew.FromMM(0.05))
        board.Add(item)


def add_note(board: pcbnew.BOARD) -> None:
    item = pcbnew.PCB_TEXT(board)
    item.SetText("PROVISIONAL PLACEMENT — UNROUTED — NO FABRICATION OUTPUT")
    item.SetLayer(pcbnew.Cmts_User)
    item.SetPosition(vec(BOARD_X + 50, BOARD_Y - 6))
    item.SetTextSize(vec(1.2, 1.2))
    item.SetTextThickness(pcbnew.FromMM(0.18))
    item.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(item)


def add_fiducials(parts: dict[str, Part], occupied: Occupancy,
                  placements: dict[str, tuple[float, float, int]],
                  assigned_room: dict[str, str]) -> list[str]:
    # The seven fiducials already exist in the schematic; reserve their space early.
    targets = [(5, 20), (8, 70), (88, 7.5), (36, 72), (44.5, 73), (16, 61), (34, 72)]
    created = []
    for index, (tx, ty) in enumerate(targets, 1):
        name = f"FID{index}"
        fp = parts[name].footprint
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        box = parts[name].bbox[0]
        candidates = [(tx + i * 0.5, ty + j * 0.5)
                      for i in range(-12, 13) for j in range(-12, 13)]
        candidates.sort(key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2)
        for x, y in candidates:
            rect = at(box, x, y)
            if 3 <= rect.left and rect.right <= 97 and 3 <= rect.bottom and rect.top <= 77 and occupied.collision(rect, clearance(name)) is None:
                place(fp, x, y, 0)
                occupied.add(name, rect)
                placements[name] = (x, y, 0)
                assigned_room[name] = "ALL"
                created.append(name)
                break
        else:
            raise RuntimeError(f"cannot place {name} near ({tx}, {ty})")
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace an existing board deliberately")
    args = parser.parse_args()
    if OUTPUT.exists() and not args.force:
        raise SystemExit(f"{OUTPUT} already exists; refusing to overwrite. Use --force only intentionally.")
    root = netlist_xml()
    parts, net_nodes = parse_parts(root)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    board.SetLayerName(pcbnew.In1_Cu, "GND")
    board.SetLayerName(pcbnew.In2_Cu, "PWR")
    title = board.GetTitleBlock()
    title.SetTitle("DAC-HPA — provisional placement")
    title.SetRevision("v1.1 placement")
    title.SetDate("2026-09-27")
    title.SetComment(0, "Unrouted. Source: Spec v1.1 / Notes v1.0 / Parts List v0.9")
    title.SetComment(1, "Owner directed placement without pre-layout checks")
    add_edge(board)
    add_note(board)
    nets: dict[str, pcbnew.NETINFO_ITEM] = {}
    for name in sorted(net_nodes):
        if name.startswith("unconnected-"):
            continue
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
        nets[name] = net
    for part in parts.values():
        board.Add(part.footprint)
    for name, nodes in net_nodes.items():
        if name.startswith("unconnected-"):
            continue
        for ref, pin in nodes:
            item = parts[ref].footprint
            pads = [pad for pad in item.Pads() if pad.GetNumber() == pin]
            if len(pads) != 1:
                raise RuntimeError(f"netlist pad mismatch: {ref} {pin}: {len(pads)} pads")
            pads[0].SetNet(nets[name])

    occupied = Occupancy()
    placements: dict[str, tuple[float, float, int]] = {}
    assigned_room: dict[str, str] = {}
    for ref, (x, y, angle) in ANCHORS.items():
        part = parts[ref]
        rect = at(part.bbox[angle], x, y)
        if not inside_board(rect, ref):
            raise RuntimeError(f"anchor {ref} outside board: {rect}")
        conflict = occupied.collision(rect, clearance(ref))
        if conflict:
            raise RuntimeError(f"anchor {ref} intersects {conflict}: {rect}")
        place(part.footprint, x, y, angle)
        occupied.add(ref, rect)
        placements[ref] = (x, y, angle)
        assigned_room[ref] = part.room
    fiducials = add_fiducials(parts, occupied, placements, assigned_room)
    pending = [part for ref, part in parts.items() if ref not in placements and not ref.startswith("TP")]
    pending.sort(key=lambda p: (priority(p.ref),
                                -(p.bbox[0].right - p.bbox[0].left) * (p.bbox[0].top - p.bbox[0].bottom), p.ref))
    for part in pending:
        target = target_for(part, placements, net_nodes, {ref: p.room for ref, p in parts.items()})
        x, y, angle, room = find_spot(part, target, occupied)
        rect = at(part.bbox[angle], x, y)
        place(part.footprint, x, y, angle)
        occupied.add(part.ref, rect)
        placements[part.ref] = (x, y, angle)
        assigned_room[part.ref] = room
    test_pads = [part for ref, part in parts.items() if ref.startswith("TP")]
    for part in sorted(test_pads, key=lambda p: number(p.ref)):
        if part.ref == "TP732":
            target = (12, 74)
        else:
            neighbors = []
            for net in part.nets:
                neighbors += [ref for ref, _ in net_nodes[net]
                              if ref in placements and not ref.startswith(("TP", "MH"))]
            if neighbors:
                # Prefer the nearest logical block over a centroid across the whole board.
                anchor = min(neighbors, key=lambda ref: len(parts[ref].nets))
                target = placements[anchor][:2]
            else:
                target = (50, 5)
        x, y, angle, room = find_spot(part, target, occupied)
        rect = at(part.bbox[angle], x, y)
        place(part.footprint, x, y, angle)
        occupied.add(part.ref, rect)
        placements[part.ref] = (x, y, angle)
        assigned_room[part.ref] = room
    pcbnew.SaveBoard(str(OUTPUT), board)
    spill = [(ref, part.room, assigned_room[ref]) for ref, part in parts.items()
             if assigned_room[ref] not in {part.room, "ALL"}]
    lines = [
        "# DAC-HPA provisional placement",
        "",
        "This editable four-layer KiCad board places all schematic footprint items on a 100 × 80 mm R1 outline. "
        "The board has pad nets and schematic paths but no tracks or copper pours. The owner directed "
        "placement without the pre-layout physical checks; this board is not a manufacturing release.",
        "",
        f"- Schematic footprint items: **{len(parts)}** (including {len(fiducials)} fiducials)",
        f"- Electrical nets: **{len(nets)}**",
        f"- Anchored connectors, mounting holes, relays and principal ICs: **{len(ANCHORS)}**",
        "- Coordinate origin: lower-left of the 100 × 80 mm board, as in Notes v1.0 §9.1.",
        "- The two 5 mm V-cut panel rails are not part of this main-board outline; JLCPCB adds them at panelization.",
        "- Placement script: `place_board.py`; it refuses to replace an existing board without `--force`.",
        "",
        "## Principal positions (mm from lower-left)",
        "",
        "| Ref | x | y | Rotation |",
        "| --- | ---: | ---: | ---: |",
    ]
    for ref in ("J101", "U201", "U202", "U301", "X201", "U403", "U404", "U401", "U402",
                "J701", "J702", "K601", "K602", "K603", "K604", "U503", "U603", "U606",
                "U609", "U610", "U611", "U612"):
        x, y, angle = placements[ref]
        lines.append(f"| {ref} | {x:.2f} | {y:.2f} | {angle}° |")
    lines += ["", "## Fiducials", "", "| Ref | x | y |", "| --- | ---: | ---: |"]
    for ref in fiducials:
        x, y, _ = placements[ref]
        lines.append(f"| {ref} | {x:.2f} | {y:.2f} |")
    lines += ["", "## Region spills", ""]
    if spill:
        lines += ["Some footprint centers moved beyond their preferred functional region to avoid occupied courtyards:", "",
                  "| Ref | Preferred | Placed in |", "| --- | --- | --- |"]
        for ref, preferred, actual in sorted(spill):
            lines.append(f"| {ref} | {preferred} | {actual} |")
    else:
        lines.append("All non-test-pad footprint centers remained in their preferred region; some courtyards cross approximate region boundaries.")
    lines += ["", "The board remains provisional; routing, copper pours, silkscreen, impedance and assembly outputs are outside this placement artifact.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Placed {len(parts)} schematic items, including {len(fiducials)} fiducials, on {WIDTH:.0f} × {HEIGHT:.0f} mm; {len(spill)} room spills")


if __name__ == "__main__":
    main()
