#!/usr/bin/env python3
"""Gate the DAC/CPLD critical routes in the partial integrated PCB study.

These are copper and saved-zone screens, not signal-integrity extraction or
fabrication release. Coordinates are measured from the current hand placement.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew

from audit_audio_output_traces import route


I2S = (
    ("BCLK", "18", "R204", "27"),
    ("LRCLK", "19", "R205", "26"),
    ("SDATA", "20", "R206", "25"),
)
INPUTS = ("DACL", "DACLB", "DACR", "DACRB")


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def point(pos: pcbnew.VECTOR2I) -> tuple[float, float]:
    return mm(pos.x), mm(pos.y)


def pad(footprints: dict, ref: str, number: str) -> pcbnew.PAD:
    return next(p for p in footprints[ref].Pads() if p.GetNumber() == number)


def point_segment_distance(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    denominator = dx * dx + dy * dy
    if denominator == 0:
        return math.dist(p, a)
    fraction = max(0.0, min(1.0,
        ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / denominator))
    return math.dist(p, (a[0] + fraction * dx, a[1] + fraction * dy))


def segment_distance(a, b, c, d) -> float:
    def cross(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    sides = (cross(a, b, c), cross(a, b, d),
             cross(c, d, a), cross(c, d, b))
    collinear = all(abs(value) < 1e-12 for value in sides)
    bounding_boxes_touch = (
        max(min(a[0], b[0]), min(c[0], d[0]))
        <= min(max(a[0], b[0]), max(c[0], d[0]))
        and max(min(a[1], b[1]), min(c[1], d[1]))
        <= min(max(a[1], b[1]), max(c[1], d[1])))
    if (collinear and bounding_boxes_touch) or (
            not collinear and sides[0] * sides[1] <= 0
            and sides[2] * sides[3] <= 0):
        return 0.0
    return min(point_segment_distance(a, c, d),
               point_segment_distance(b, c, d),
               point_segment_distance(c, a, b),
               point_segment_distance(d, a, b))


def outside_rect(a, b, rect):
    """Clip a track centreline to the region outside an axis-aligned box."""
    left, right, top, bottom = rect
    x, y = a
    dx, dy = b[0] - x, b[1] - y
    low, high = 0.0, 1.0
    for p, q in ((-dx, x - left), (dx, right - x),
                 (-dy, y - top), (dy, bottom - y)):
        if abs(p) < 1e-12:
            if q < 0:
                return [(a, b)]
        elif p < 0:
            low = max(low, q / p)
        else:
            high = min(high, q / p)
    if low > high:
        return [(a, b)]
    pieces = []
    if low > 1e-9:
        pieces.append((a, (x + low * dx, y + low * dy)))
    if high < 1 - 1e-9:
        pieces.append(((x + high * dx, y + high * dy), b))
    return pieces


def track_segments(board, net: str):
    segments = []
    for item in board.GetTracks():
        if item.GetNetname() != net:
            continue
        if isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() != pcbnew.F_Cu:
            raise AssertionError(f"{net} must have F.Cu tracks and no vias")
        segments.append((point(item.GetStart()), point(item.GetEnd()),
                         mm(item.GetWidth())))
    if not segments:
        raise AssertionError(f"{net} has no F.Cu copper")
    return segments


def closest_track_gap(left, right, courtyard=None) -> float:
    best = math.inf
    for a, b, width_a in left:
        pieces_a = outside_rect(a, b, courtyard) if courtyard else [(a, b)]
        for c, d, width_b in right:
            pieces_b = outside_rect(c, d, courtyard) if courtyard else [(c, d)]
            for p, q in pieces_a:
                for r, s in pieces_b:
                    best = min(best, segment_distance(p, q, r, s)
                               - (width_a + width_b) / 2)
    return best


def rect_segment_distance(rect, a, b) -> float:
    left, right, top, bottom = rect
    if (left <= a[0] <= right and top <= a[1] <= bottom) or (
            left <= b[0] <= right and top <= b[1] <= bottom):
        return 0.0
    corners = ((left, top), (right, top), (right, bottom), (left, bottom))
    return min(segment_distance(a, b, corners[i], corners[(i + 1) % 4])
               for i in range(4))


def pad_box(p: pcbnew.PAD):
    box = p.GetBoundingBox()
    return mm(box.GetLeft()), mm(box.GetRight()), mm(box.GetTop()), mm(box.GetBottom())


def l2_missing_mm(segments, filled, offsets=(-0.075, 0.0, 0.075)):
    missing = {offset: 0.0 for offset in offsets}
    for a, b, _ in segments:
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if not length:
            raise AssertionError("Zero-length critical route")
        nx, ny = -dy / length, dx / length
        count = math.ceil(length / 0.01)
        for index in range(count):
            fraction = (index + 0.5) / count
            x, y = a[0] + fraction * dx, a[1] + fraction * dy
            for offset in offsets:
                at = pcbnew.VECTOR2I(pcbnew.FromMM(x + offset * nx),
                                     pcbnew.FromMM(y + offset * ny))
                if not filled.Contains(at):
                    missing[offset] += length / count
    return {f"{offset:+.3f}": round(value, 4)
            for offset, value in missing.items()}


def corridor_at_y(segments, y: float) -> tuple[float, float]:
    matches = []
    for a, b, width in segments:
        if abs(a[1] - b[1]) < 1e-9:
            continue
        if min(a[1], b[1]) <= y <= max(a[1], b[1]):
            fraction = (y - a[1]) / (b[1] - a[1])
            matches.append((a[0] + fraction * (b[0] - a[0]), width))
    if len(matches) != 1:
        raise AssertionError(f"Expected one critical clock lane at y={y}: {matches}")
    return matches[0]


def audit(board_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    zone = next((z for z in board.Zones() if z.GetNetname() == "GND"
                 and z.IsOnLayer(pcbnew.In1_Cu)
                 and z.HasFilledPolysForLayer(pcbnew.In1_Cu)), None)
    if zone is None or zone.GetFilledPolysList(pcbnew.In1_Cu).OutlineCount() != 1:
        raise AssertionError("Critical-route audit requires one saved filled L2 GND polygon")
    filled = zone.GetFilledPolysList(pcbnew.In1_Cu)

    copper = {}
    for net in ("MCLK", "FAM_CLK", *(f"N2_{name}_SRC" for name, *_ in I2S),
                *(name for name, *_ in I2S), *INPUTS):
        copper[net] = track_segments(board, net)

    path_lengths = {}
    for name, src_pin, resistor, dac_pin in I2S:
        source_net = f"N2_{name}_SRC"
        source_length = route(board, footprints, source_net,
                              ("U202", src_pin), (resistor, "1"))[1]
        post_length = route(board, footprints, name,
                            (resistor, "2"), ("U301", dac_pin))[1]
        span = math.dist(point(pad(footprints, resistor, "1").GetPosition()),
                         point(pad(footprints, resistor, "2").GetPosition()))
        total = source_length + span + post_length
        if total > 25.0 + 1e-6:
            raise AssertionError(f"{name} source-to-DAC path exceeds 25 mm: {total:.3f}")
        for net in (source_net, name):
            if any(abs(width - 0.15) > 1e-6 for _, _, width in copper[net]):
                raise AssertionError(f"{net} must remain 0.15 mm in this 3W corridor")
        path_lengths[name] = {
            "U202_to_series_pad_mm": round(source_length, 3),
            "series_pad_span_mm": round(span, 3),
            "series_to_U301_mm": round(post_length, 3),
            "complete_pad_centre_mm": round(total, 3),
        }
    lengths = [row["complete_pad_centre_mm"] for row in path_lengths.values()]
    if max(lengths) - min(lengths) > 5.0:
        raise AssertionError("I2S path length spread exceeds 5 mm")

    corridor = {}
    for y in (74.0, 76.0, 78.0, 80.0):
        row = [(name, *corridor_at_y(copper[name], y))
               for name, *_ in I2S]
        if not all(row[index][1] < row[index + 1][1]
                   for index in range(2)):
            raise AssertionError(f"I2S lane ordering reverses at y={y}")
        gaps = [row[index + 1][1] - row[index][1]
                - (row[index][2] + row[index + 1][2]) / 2
                for index in range(2)]
        for index, gap in enumerate(gaps):
            required = 3 * max(row[index][2], row[index + 1][2])
            if gap < required - 1e-6:
                raise AssertionError(f"I2S 3W edge gap fails at y={y}: {gap:.3f}")
        corridor[f"y={y:.1f}"] = {
            "centres_mm": {name: round(x, 3) for name, x, _ in row},
            "edge_gaps_mm": [round(gap, 3) for gap in gaps],
        }

    source_clock = route(board, footprints, "N2_X201_OUT",
                         ("X201", "3"), ("R203", "1"))[1]
    dac_clock = route(board, footprints, "MCLK",
                      ("R203", "2"), ("U301", "7"))[1]
    if source_clock > 2.0 or dac_clock > 8.0 or source_clock + dac_clock > 10.0:
        raise AssertionError("MCLK 2/8/10 mm path screen failed")
    fam_clock = route(board, footprints, "FAM_CLK",
                      ("R215", "2"), ("U202", "1"))[1]

    # These are routed copper-contact lengths. The path helper stops at the
    # first copper inside each pad, so they are not pad-centre lengths.
    local_pairs = (
        ("CPLD_C213_to_U202_32", "N2_V33_CPLD", ("C213", "1"),
         ("U202", "32"), 2.0),
        ("CPLD_C215_to_U202_6", "N2_V33_CPLD", ("C215", "1"),
         ("U202", "6"), 4.0),
        ("CPLD_C214_to_U202_16", "N2_V33_CPLD", ("C214", "1"),
         ("U202", "16"), 3.0),
        ("CPLD_FB202_to_C220", "N2_V33_CPLD", ("FB202", "2"),
         ("C220", "1"), 3.0),
        ("CPLD_FB202_to_C213", "N2_V33_CPLD", ("FB202", "2"),
         ("C213", "1"), 6.0),
        ("LP5907_U302_input_to_C301", "5V_SYS", ("U302", "1"),
         ("C301", "1"), 2.0),
        ("LP5907_U302_output_to_C302", "3V3A", ("U302", "5"),
         ("C302", "1"), 2.5),
        ("LP5907_U302_output_to_FB302", "3V3A", ("U302", "5"),
         ("FB302", "1"), 6.0),
    )
    local_paths = {}
    for name, net, start, end, screen in local_pairs:
        length = route(board, footprints, net, start, end)[1]
        if length > screen + 1e-6:
            raise AssertionError(f"{name} local copper exceeds {screen} mm: {length:.3f}")
        local_paths[name] = round(length, 3)

    box = footprints["U301"].GetCourtyard(pcbnew.F_CrtYd).BBox()
    package = tuple(mm(value) for value in
                    (box.GetLeft(), box.GetRight(), box.GetTop(), box.GetBottom()))
    clock_gaps = {}
    external_pad_gaps = {}
    clock_pads = [p for f in board.GetFootprints() for p in f.Pads()
                  if p.GetNetname() == "MCLK" and f.GetReference() != "U301"]
    for net in INPUTS:
        inside = closest_track_gap(copper["MCLK"], copper[net])
        outside = closest_track_gap(copper["MCLK"], copper[net], package)
        if inside < 1.0 - 1e-6 or outside < 2.0 - 1e-6:
            raise AssertionError(f"MCLK/{net} copper separation fails: {inside}, {outside}")
        pad_gap = math.inf
        for clock_pad in clock_pads:
            rect = pad_box(clock_pad)
            for a, b, width in copper[net]:
                for c, d in outside_rect(a, b, package):
                    pad_gap = min(pad_gap, rect_segment_distance(rect, c, d) - width / 2)
        if pad_gap < 2.0 - 1e-6:
            raise AssertionError(f"MCLK pad/{net} track gap outside U301 <2 mm: {pad_gap}")
        clock_gaps[net] = {"full_track_gap_mm": round(inside, 4),
                           "outside_U301_courtyard_mm": round(outside, 4)}
        external_pad_gaps[net] = round(pad_gap, 4)

    l2 = {net: l2_missing_mm(copper[net], filled)
          for net in ("MCLK", "FAM_CLK", *(f"N2_{name}_SRC" for name, *_ in I2S),
                      *(name for name, *_ in I2S))}
    if any(value > 0.0100 for samples in l2.values() for value in samples.values()):
        raise AssertionError("Critical F.Cu clock route loses direct sampled L2 support")

    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    ground_refs = ("U202", "U301", "U302", "U303", "C213", "C214", "C215",
                   "C220", "C222", "C301", "C302", "C303", "C304", "C305",
                   "C306", "C307", "C308", "C309", "C310", "C311", "C312",
                   "C439", "C440", "R534")
    ground_pads = [(ref, p) for ref in ground_refs for p in footprints[ref].Pads()
                   if p.GetNetname() == "GND"]
    without_l2 = [f"{ref}.{p.GetNumber()}" for ref, p in ground_pads
                  if not any(item.GetClass() == "ZONE"
                             for item in connectivity.GetConnectedItems(p))]
    if without_l2:
        raise AssertionError(f"DAC/regulator GND pads do not reach L2: {without_l2}")
    ep_counts = {}
    for ref, expected in (("U301", 5), ("U202", 2)):
        ep_box = pad_box(pad(footprints, ref, "EP"))
        ep_vias = [v for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA)
                   and v.GetNetname() == "GND"
                   and ep_box[0] <= point(v.GetPosition())[0] <= ep_box[1]
                   and ep_box[2] <= point(v.GetPosition())[1] <= ep_box[3]]
        if (len(ep_vias) != expected
                or any(not (v.GetPrimaryDrillFilledFlag()
                                and v.GetPrimaryDrillCappedFlag())
                       or abs(mm(v.GetDrillValue()) - 0.30) > 1e-6
                       or abs(mm(v.GetWidth(pcbnew.F_Cu)) - 0.70) > 1e-6
                       for v in ep_vias)):
            raise AssertionError(
                f"{ref} EP must have {expected} 0.7/0.3 filled/capped GND vias")
        ep_counts[ref] = len(ep_vias)

    regulator_output = pad(footprints, "U303", "5")
    dac_1v3 = pad(footprints, "U301", "21")
    if dac_1v3 not in connectivity.GetConnectedItems(regulator_output):
        raise AssertionError("U303 output does not physically reach DAC 1V3 pin")
    supply_vias = [item for item in board.GetTracks()
                   if isinstance(item, pcbnew.PCB_VIA)
                   and item.GetNetname() == "1V3"]
    if len(supply_vias) != 2:
        raise AssertionError("Manual 1V3 bridge must use exactly two through vias")
    pwr_layer = board.GetLayerID("PWR")
    supply_pwr_length = sum(
        math.dist(point(item.GetStart()), point(item.GetEnd()))
        for item in board.GetTracks()
        if not isinstance(item, pcbnew.PCB_VIA)
        and item.GetNetname() == "1V3" and item.GetLayer() == pwr_layer)

    return {
        "board": board_path.name,
        "complete_I2S_paths_mm": path_lengths,
        "I2S_complete_length_spread_mm": round(max(lengths) - min(lengths), 3),
        "I2S_central_3W_edge_gap": corridor,
        "MCLK_X201_to_R203_mm": round(source_clock, 3),
        "MCLK_R203_to_U301_mm": round(dac_clock, 3),
        "MCLK_total_mm": round(source_clock + dac_clock, 3),
        "FAM_CLK_R215_to_U202_mm": round(fam_clock, 3),
        "local_pad_contact_routes_mm": local_paths,
        "U303_to_DAC_1V3_connected": True,
        "U303_to_DAC_1V3_PWR_copper_mm": round(supply_pwr_length, 3),
        "U303_to_DAC_1V3_vias": len(supply_vias),
        "MCLK_to_DAC_input_tracks_mm": clock_gaps,
        "MCLK_pad_to_DAC_input_track_outside_U301_mm": external_pad_gaps,
        "clock_L2_direct_support_missing_mm": l2,
        "DAC_CPLD_LDO_local_GND_pads_to_L2": len(ground_pads),
        "U301_EP_filled_capped_vias": ep_counts["U301"],
        "U202_EP_filled_capped_vias": ep_counts["U202"],
        "ratsnest_unconnected_items": connectivity.GetUnconnectedCount(False),
        "model_limits": "2D copper-edge and saved L2 samples only; no return impedance,"
                        " extracted parasitics, stackup/EMI/ESD or operational test",
        "release": "HOLD: full routing, upstream source rails, I/V feedback return,"
                   " DVDD capacitor ECO, JLC via-pad process and measured audio/EMI",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.board)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
