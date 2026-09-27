#!/usr/bin/env python3
"""Measure placement geometry from actual KiCad pads and footprint bounds.

These are lower bounds and density proxies. They do not prove that copper can
be routed with the required width, clearance, return path, or length.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import re
from pathlib import Path

import pcbnew

import place_board


ORIGIN_X = 40.0
ORIGIN_Y = 40.0
POWER = {
    "GND", "3V3D", "3V3M", "3V3A", "5V_SYS", "5V_ANA", "VPOS",
    "VNEG", "1V3", "AVCC", "DVCC", "VBUS", "N2_V33_CPLD",
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def point(pad: pcbnew.PAD, height: float) -> tuple[float, float]:
    pos = pad.GetPosition()
    return mm(pos.x) - ORIGIN_X, height - (mm(pos.y) - ORIGIN_Y)


def box(fp: pcbnew.FOOTPRINT, height: float) -> tuple[float, float, float, float]:
    bb = fp.GetBoundingBox() if isinstance(fp, pcbnew.PAD) else fp.GetBoundingBox(False, False)
    return (
        mm(bb.GetLeft()) - ORIGIN_X,
        mm(bb.GetRight()) - ORIGIN_X,
        height - (mm(bb.GetBottom()) - ORIGIN_Y),
        height - (mm(bb.GetTop()) - ORIGIN_Y),
    )


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.dist(a, b)


def hpwl(points: list[tuple[float, float]]) -> float:
    if not points:
        return 0.0
    xs, ys = zip(*points)
    return max(xs) - min(xs) + max(ys) - min(ys)


def overlap(a: tuple[float, float, float, float],
            b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def area_in(a: tuple[float, float, float, float],
            b: tuple[float, float, float, float]) -> float:
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0])) * max(
        0.0, min(a[3], b[3]) - max(a[2], b[2])
    )


def copper_gap(a: tuple[float, float, float, float],
               b: tuple[float, float, float, float]) -> float:
    """Conservative gap between pad bounding rectangles, in millimetres."""
    return math.hypot(max(0.0, a[0] - b[1], b[0] - a[1]),
                      max(0.0, a[2] - b[3], b[2] - a[3]))


def check_board_netlist(path: Path) -> None:
    """Reject a stale placement whose footprints or pad nets differ from capture."""
    board = pcbnew.LoadBoard(str(path))
    actual_footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    root = place_board.netlist_xml()
    expected_footprints = {
        comp.get("ref"): comp.findtext("footprint")
        for comp in root.findall("./components/comp")
        if comp.find("property[@name='exclude_from_board']") is None
    }
    if set(actual_footprints) != set(expected_footprints):
        missing = sorted(set(expected_footprints) - set(actual_footprints))
        extra = sorted(set(actual_footprints) - set(expected_footprints))
        raise SystemExit(f"board footprint references differ: missing={missing}, extra={extra}")
    for ref, expected_id in expected_footprints.items():
        actual_id = actual_footprints[ref].GetFPIDAsString()
        if actual_id != expected_id:
            raise SystemExit(f"{ref} footprint {actual_id} != schematic {expected_id}")
    expected_nets = {
        (node.get("ref"), node.get("pin")): net.get("name")
        for net in root.findall("./nets/net")
        if not (net.get("name") or "").startswith("unconnected-")
        for node in net.findall("node")
        if node.get("ref") in expected_footprints
    }
    actual_nets = {
        (fp.GetReference(), pad.GetNumber()): pad.GetNetname()
        for fp in actual_footprints.values() for pad in fp.Pads()
        if pad.GetNumber() and pad.GetNetname()
    }
    if actual_nets != expected_nets:
        wrong = sorted((key, expected_nets.get(key), actual_nets.get(key))
                       for key in set(expected_nets) | set(actual_nets)
                       if expected_nets.get(key) != actual_nets.get(key))
        raise SystemExit(f"board pad nets differ from schematic: {wrong[:12]}")


def audit(path: Path, height: float) -> dict:
    board = pcbnew.LoadBoard(str(path))
    edge_points = [point for drawing in board.GetDrawings()
                   if drawing.GetLayer() == pcbnew.Edge_Cuts
                   for point in (drawing.GetStart(), drawing.GetEnd())]
    outline_width = round(max(mm(point.x) for point in edge_points)
                          - min(mm(point.x) for point in edge_points))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    rectangles = {ref: box(fp, height) for ref, fp in footprints.items()}
    pads = {
        ref: {pad.GetNumber(): pad for pad in fp.Pads() if pad.GetNumber()}
        for ref, fp in footprints.items()
    }

    def pt(ref: str, pin: str | int) -> tuple[float, float]:
        return point(pads[ref][str(pin)], height)

    def d(a: str, ap: str | int, b: str, bp: str | int) -> float:
        return distance(pt(a, ap), pt(b, bp))

    def r(value: float) -> float:
        return round(value, 2)

    all_nets: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
    net_pads: dict[str, list[tuple[str, str, tuple[float, float, float, float]]]] = collections.defaultdict(list)
    for fp in footprints.values():
        for pad in fp.Pads():
            if pad.GetNetname():
                all_nets[pad.GetNetname()].append(point(pad, height))
                net_pads[pad.GetNetname()].append(
                    (fp.GetReference(), pad.GetNumber(), box(pad, height)))

    clock_nets = (
        "MCLK", "N2_X201_OUT", "N6_MCK_IN", "N6_MCK_BUF", "N6_PMP",
        "FAM_CLK", "BCLK", "LRCLK", "SDATA", "LINK_SCK",
    )
    high_z_to_clock = []
    for net, nodes in net_pads.items():
        if re.match(r"N6_VLL|N6_VOR", net):
            minimum = 10.0
        elif re.match(r"N6_(?:V3|TW|LW|OR)", net) and net != "N6_ORTEST":
            minimum = 5.0
        else:
            continue
        closest = min(
            (copper_gap(sensitive[2], clock[2]), clock_net,
             f"{sensitive[0]}.{sensitive[1]}", f"{clock[0]}.{clock[1]}")
            for sensitive in nodes for clock_net in clock_nets
            for clock in net_pads.get(clock_net, [])
        )
        if closest[0] < minimum:
            high_z_to_clock.append({
                "net": net, "min_gap_mm": r(closest[0]), "required_mm": minimum,
                "clock_net": closest[1], "sensitive_pad": closest[2],
                "clock_pad": closest[3],
            })
    high_z_to_clock.sort(key=lambda item: (item["min_gap_mm"], item["net"]))

    collisions = []
    items = list(rectangles.items())
    for index, (ref, rect) in enumerate(items):
        for other_ref, other in items[index + 1:]:
            if overlap(rect, other):
                collisions.append([ref, other_ref])

    zone_fill = {}
    if outline_width == 100 and height in (80, 100):
        if height == 100:
            place_board.configure_100x100()
        for name in ("Z1", "Z2", "Z4U", "Z4L", "Z4S", "Z5", "Z6", "Z7A", "Z7B", "Z8A"):
            region = place_board.ROOMS[name]
            zone = (region[0], region[1], region[2], region[3])
            used = sum(area_in(rect, zone) for ref, rect in rectangles.items()
                       if not ref.startswith(("FID", "TP", "MH")))
            zone_fill[name] = r(100 * used / ((zone[1] - zone[0]) * (zone[3] - zone[2])))

    dac_iv = {
        net: r(d("U301", dac_pin, opamp, input_pin))
        for net, dac_pin, opamp, input_pin in (
            ("DACL", 13, "U403", 2), ("DACLB", 14, "U403", 6),
            ("DACR", 9, "U404", 2), ("DACRB", 10, "U404", 6)
        )
    }
    iv_feedback = {}
    for ref, opamp, input_pin, output_pin in (
        ("R423", "U403", 2, 1), ("C417", "U403", 2, 1),
        ("R424", "U403", 6, 7), ("C418", "U403", 6, 7),
        ("R425", "U404", 2, 1), ("C419", "U404", 2, 1),
        ("R426", "U404", 6, 7), ("C420", "U404", 6, 7),
    ):
        iv_feedback[ref] = r(max(d(ref, 1, opamp, input_pin),
                                 d(ref, 2, opamp, output_pin)))

    jack = {}
    for relay, net, jack_pads in (
        ("K601", "JACK_LP", [("J701", 7), ("J701", 8), ("J702", 4)]),
        ("K602", "JACK_LN", [("J701", 6)]),
        ("K603", "JACK_RP", [("J701", 4), ("J701", 5), ("J702", 3)]),
        ("K604", "JACK_RN", [("J701", 2), ("J701", 3)]),
    ):
        jack[net] = {
            f"{ref}.{pin}": r(d(relay, 6, ref, pin)) for ref, pin in jack_pads
        }
    esd = {}
    for ref in ("D701", "D702", "D703", "D704"):
        net = next(pad.GetNetname() for pad in footprints[ref].Pads()
                   if pad.GetNetname() != "GND")
        candidates = [
            (d(ref, 1, jack_ref, pad.GetNumber()), jack_ref, pad.GetNumber())
            for jack_ref in ("J701", "J702")
            for pad in footprints[jack_ref].Pads() if pad.GetNetname() == net
        ]
        best = min(candidates)
        esd[ref] = {"net": net, "closest_jack_pad": f"{best[1]}.{best[2]}",
                    "distance_mm": r(best[0])}

    clock = {
        "X201.3_to_R203.1": r(d("X201", 3, "R203", 1)),
        "R203.2_to_U301.7": r(d("R203", 2, "U301", 7)),
        "R665.1_to_U301.7": r(d("R665", 1, "U301", 7)),
        "R665.2_to_U607.2": r(d("R665", 2, "U607", 2)),
    }
    clock["MCLK_core_euclidean_lower_bound"] = r(
        d("X201", 3, "R203", 1) + d("R203", 2, "R665", 1)
        + d("R665", 1, "U301", 7)
    )
    clock["MCLK_via_TP711_euclidean_lower_bound"] = r(
        d("X201", 3, "R203", 1) + d("R203", 2, "TP711", 1)
        + d("TP711", 1, "R665", 1) + d("R665", 1, "U301", 7)
    )
    i2s = {
        net: {
            "source_to_R": r(d("U202", cpld_pin, resistor, 1)),
            "core_R_to_DAC": r(d(resistor, 2, "U301", dac_pin)),
            "core_euclidean_lower_bound": r(
                d("U202", cpld_pin, resistor, 1)
                + d(resistor, 2, "U301", dac_pin)
            ),
            "test_pad_to_DAC": r(d(testpad, 1, "U301", dac_pin)),
            "header_to_DAC": (r(d("J703", header_pin, "U301", dac_pin))
                              if "J703" in footprints else None),
            "net_hpwl": r(hpwl(all_nets[net])),
        }
        for net, resistor, testpad, header_pin, cpld_pin, dac_pin in (
            ("BCLK", "R204", "TP715", 2, 18, 27),
            ("LRCLK", "R205", "TP716", 3, 19, 26),
            ("SDATA", "R206", "TP717", 4, 20, 25),
        )
    }
    usb = {
        "D102_VBUS_to_J101_B4": r(d("D102", 1, "J101", "B4/A9")),
        "U101_DP_to_J101_A6": r(d("U101", 1, "J101", "A6")),
        "U101_DN_to_J101_B7": r(d("U101", 3, "J101", "B7")),
        "U103_CC1_to_J101_A5": r(d("U103", 3, "J101", "A5")),
        "U103_CC2_to_J101_B5": r(d("U103", 5, "J101", "B5")),
        "U102_VBUS_to_J101_B4": r(d("U102", 6, "J101", "B4/A9")),
        "C102_VBUS_to_J101_A4": r(d("C102", 1, "J101", "A4/B9")),
        "U502_IN_to_C102_VBUS": r(d("U502", 1, "C102", 1)),
        "Y201_HSE_IN_to_U201_5": r(d("Y201", 1, "U201", 5)),
        "Y201_HSE_OUT_to_U201_6": r(d("Y201", 2, "U201", 6)),
    }
    timer = {}
    for index in range(8):
        opamp = f"U{613 + index}"
        timer_cap = f"C{647 + index}"
        timer_res = f"R{942 + index}"
        decap = f"C{659 + index}"
        # Body-center distances are only grouping proxies, not timer trace lengths.
        op_pos = footprints[opamp].GetPosition()
        center = (mm(op_pos.x) - ORIGIN_X, height - (mm(op_pos.y) - ORIGIN_Y))
        timer[opamp] = {
            "cap_center_mm": r(distance(center, (
                mm(footprints[timer_cap].GetPosition().x) - ORIGIN_X,
                height - (mm(footprints[timer_cap].GetPosition().y) - ORIGIN_Y)))),
            "res_center_mm": r(distance(center, (
                mm(footprints[timer_res].GetPosition().x) - ORIGIN_X,
                height - (mm(footprints[timer_res].GetPosition().y) - ORIGIN_Y)))),
            "decap_center_mm": r(distance(center, (
                mm(footprints[decap].GetPosition().x) - ORIGIN_X,
                height - (mm(footprints[decap].GetPosition().y) - ORIGIN_Y)))),
        }

    protection_timer = {}
    for name, comparator, comparator_pin, cap, transistor, resistor in (
        ("LP_L", "U609", 8, "C631", "Q623", "R920"),
        ("LN_L", "U609", 10, "C632", "Q624", "R921"),
        ("LP_R", "U610", 8, "C633", "Q625", "R922"),
        ("LN_R", "U610", 10, "C634", "Q626", "R923"),
    ):
        target = pt(comparator, comparator_pin)
        parts = {"cap": (cap, 1), "bleed": (transistor, 3),
                 "charge_resistor": (resistor, 2)}
        protection_timer[name] = {
            part: {
                "euclidean_pad_mm": r(distance(target, pt(ref, pin))),
                "manhattan_pad_lower_bound_mm": r(
                    abs(target[0] - pt(ref, pin)[0])
                    + abs(target[1] - pt(ref, pin)[1])),
            }
            for part, (ref, pin) in parts.items()
        }

    return {
        "board": str(path), "size_mm": [outline_width, int(height)],
        "footprints": len(footprints), "named_nets": len(all_nets),
        "bbox_overlaps": collisions, "zone_bbox_fill_pct": zone_fill,
        "dac_iv_pad_distance_mm": dac_iv,
        "iv_feedback_max_pad_distance_mm": iv_feedback,
        "clock_mm": clock, "i2s_mm": i2s, "usb_mm": usb,
        "relay_to_jack_pad_mm": jack,
        "esd_to_nearest_jack_pad_mm": esd, "lpw_group_center_mm": timer,
        "protection_timer_pad_distance_mm": protection_timer,
        "fam_clk_hpwl_mm": r(hpwl(all_nets["FAM_CLK"])),
        "high_z_clock_pad_gap_violations": high_z_to_clock,
        "track_count": len(board.GetTracks()),
        "zone_count": len(board.Zones()),
        "total_nonpower_hpwl_mm": r(sum(hpwl(nodes) for name, nodes
                                         in all_nets.items() if name not in POWER)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--height", type=float, required=True)
    parser.add_argument("--check-invariants", action="store_true",
                        help="fail if board size, item counts, or overlap invariants regress")
    args = parser.parse_args()
    result = audit(args.board, args.height)
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.check_invariants and (
        result["size_mm"][1] != int(args.height)
        or result["footprints"] != 536 or result["named_nets"] != 246
        or result["bbox_overlaps"]
    ):
        raise SystemExit("placement invariant failed")
    if args.check_invariants:
        check_board_netlist(args.board)


if __name__ == "__main__":
    main()
