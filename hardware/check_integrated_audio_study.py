#!/usr/bin/env python3
"""Gate the manually routed amplifier-to-jack study as partial review data."""

from __future__ import annotations

import argparse
import collections
import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path

import pcbnew

from audit_placement import check_board_netlist
from audit_audio_output_traces import graph as copper_graph, route as copper_route
from audit_local_tvs_paths import point as copper_point
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
T_CELLS = (
    ("LP−", "R401", "R438", "C431", "U401", "10"),
    ("LP+", "R403", "R439", "C432", "U401", "1"),
    ("LN−", "R405", "R440", "C433", "U401", "6"),
    ("LN+", "R407", "R441", "C434", "U401", "5"),
    ("RP−", "R409", "R442", "C435", "U402", "10"),
    ("RP+", "R411", "R443", "C436", "U402", "1"),
    ("RN−", "R413", "R444", "C437", "U402", "6"),
    ("RN+", "R415", "R445", "C438", "U402", "5"),
)
NEGATIVE_T_SECOND = {"LP": "R438", "LN": "R440",
                     "RP": "R442", "RN": "R444"}


@dataclass(frozen=True)
class IVLeg:
    dac_net: str
    dac_pin: str
    opamp: str
    input_pin: str
    output_pin: str
    output_net: str
    feedback_resistor: str
    feedback_capacitor: str
    clamp: str
    cm: str
    first_t: tuple[str, str]


IV_LEGS = {
    "LP": IVLeg("DACL", "13", "U403", "6", "7", "N4_IVL_P",
                "R423", "C417", "D405", "R653", ("R401", "R407")),
    "LN": IVLeg("DACLB", "14", "U403", "2", "1", "N4_IVL_N",
                "R424", "C418", "D406", "R654", ("R403", "R405")),
    "RP": IVLeg("DACR", "9", "U404", "6", "7", "N4_IVR_P",
                "R425", "C419", "D407", "R655", ("R409", "R415")),
    "RN": IVLeg("DACRB", "10", "U404", "2", "1", "N4_IVR_N",
                "R426", "C420", "D408", "R656", ("R411", "R413")),
}
IV_SWAPPED_PIN_NETS = {
    "U403": {"1": "N4_IVL_N", "2": "DACLB", "6": "DACL", "7": "N4_IVL_P"},
    "U404": {"1": "N4_IVR_N", "2": "DACRB", "6": "DACR", "7": "N4_IVR_P"},
}


def _projected_bounded_area(points: list[tuple[float, float]]) -> float:
    """Sum bounded faces of a self-intersecting plan-view centreline loop."""
    segments = list(zip(points, points[1:] + points[:1]))
    splits = [[(0.0, a), (1.0, b)] for a, b in segments]
    for i, (a, b) in enumerate(segments):
        ux, uy = b[0] - a[0], b[1] - a[1]
        for j, (c, d) in enumerate(segments[i + 1:], i + 1):
            vx, vy = d[0] - c[0], d[1] - c[1]
            cross = ux * vy - uy * vx
            if abs(cross) < 1e-9:
                continue
            wx, wy = c[0] - a[0], c[1] - a[1]
            t = (wx * vy - wy * vx) / cross
            s = (wx * uy - wy * ux) / cross
            if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= s <= 1 + 1e-9:
                intersection = (round(a[0] + t * ux, 9), round(a[1] + t * uy, 9))
                splits[i].append((t, intersection))
                splits[j].append((s, intersection))
    adjacent: dict[tuple[float, float], set[tuple[float, float]]] = {}
    for split in splits:
        ordered = sorted(split)
        for (_, a), (_, b) in zip(ordered, ordered[1:]):
            a = (round(a[0], 9), round(a[1], 9))
            b = (round(b[0], 9), round(b[1], 9))
            if a != b:
                adjacent.setdefault(a, set()).add(b)
                adjacent.setdefault(b, set()).add(a)
    order = {a: sorted(neighbors, key=lambda b: math.atan2(b[1] - a[1], b[0] - a[0]))
             for a, neighbors in adjacent.items()}
    seen: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    faces = []
    for a, neighbors in adjacent.items():
        for b in neighbors:
            if (a, b) in seen:
                continue
            start = a, b
            u, v = start
            face = []
            while (u, v) not in seen:
                seen.add((u, v))
                face.append(u)
                around = order[v]
                w = around[(around.index(u) - 1) % len(around)]
                u, v = v, w
            if (u, v) != start:
                raise AssertionError("I/V projected feedback loop has an invalid face")
            area = sum(x * q - y * p for (x, y), (p, q)
                       in zip(face, face[1:] + face[:1])) / 2
            if abs(area) > 1e-8:
                faces.append(area)
    if not faces or abs(sum(faces)) > 1e-5:
        raise AssertionError("I/V projected feedback faces do not close")
    return sum(area for area in faces if area > 0)


def check_iv_macro(board: pcbnew.BOARD, footprints: dict,
                   group) -> dict:
    """Check the manually frozen I/V copper and its plan-view loop model."""
    def pad(ref: str, number: str) -> pcbnew.PAD:
        return next(item for item in footprints[ref].Pads() if item.GetNumber() == number)

    for ref, expected in IV_SWAPPED_PIN_NETS.items():
        actual = {number: pad(ref, number).GetNetname() for number in expected}
        if actual != expected:
            raise AssertionError(f"{ref} swapped I/V pad nets differ: {actual}")

    graphs = {}

    def graph(net: str):
        if net in graphs:
            return graphs[net]
        edges = collections.defaultdict(list)
        layers = set()
        vias = []
        for item in board.GetTracks():
            if item.GetNetname() != net:
                continue
            if isinstance(item, pcbnew.PCB_VIA):
                vias.append(item)
                continue
            if item.GetClass() == "PCB_ARC":
                raise AssertionError(f"{net} arc is not in the manual I/V route model")
            a, b = item.GetStart(), item.GetEnd()
            layer = item.GetLayer()
            layers.add(layer)
            u, v = (layer, a.x, a.y), (layer, b.x, b.y)
            length = math.hypot(pcbnew.ToMM(a.x - b.x), pcbnew.ToMM(a.y - b.y))
            edges[u].append((v, length))
            edges[v].append((u, length))
        for via in vias:
            at = via.GetPosition()
            nodes = [(layer, at.x, at.y) for layer in layers
                     if via.IsOnLayer(layer) and (layer, at.x, at.y) in edges]
            for index, u in enumerate(nodes):
                for v in nodes[index + 1:]:
                    edges[u].append((v, 0.0))
                    edges[v].append((u, 0.0))
        graphs[net] = edges
        return edges

    def route(net: str, first: tuple[str, str], last: tuple[str, str]):
        for ref, number in (first, last):
            if pad(ref, number).GetNetname() != net:
                raise AssertionError(f"{ref}.{number} is not on {net}")
        a, b = pad(*first).GetPosition(), pad(*last).GetPosition()
        start, end = (pcbnew.F_Cu, a.x, a.y), (pcbnew.F_Cu, b.x, b.y)
        edges = graph(net)
        if start not in edges or end not in edges:
            raise AssertionError(f"{net} pad-centre copper escape is missing: {first}->{last}")
        heap = [(0.0, start)]
        distances = {start: 0.0}
        previous = {}
        while heap:
            length, here = heapq.heappop(heap)
            if here == end:
                break
            if length > distances[here] + 1e-9:
                continue
            for there, segment_length in edges[here]:
                candidate = length + segment_length
                if candidate < distances.get(there, math.inf) - 1e-9:
                    distances[there] = candidate
                    previous[there] = here
                    heapq.heappush(heap, (candidate, there))
        if end not in distances:
            raise AssertionError(f"{net} copper route is open: {first}->{last}")
        nodes = [end]
        while nodes[-1] != start:
            nodes.append(previous[nodes[-1]])
        nodes.reverse()
        return nodes, distances[end]

    def projected(nodes):
        points = []
        for _, x, y in nodes:
            at = (round(pcbnew.ToMM(x), 9), round(pcbnew.ToMM(y), 9))
            if not points or points[-1] != at:
                points.append(at)
        return points

    l2 = next((zone.GetFilledPolysList(pcbnew.In1_Cu)
               for zone in board.Zones()
               if zone.GetNetname() == "GND" and zone.IsOnLayer(pcbnew.In1_Cu)
               and zone.HasFilledPolysForLayer(pcbnew.In1_Cu)), None)
    if l2 is None:
        raise AssertionError("I/V plane screen needs the saved filled L2 GND")

    def l2_missing_mm(nodes, offsets: tuple[float, ...]) -> dict[str, float]:
        """Sample direct plane under F.Cu trace centrelines and width edges.

        This is a plan-view via-antipad screen; it does not model return
        current, field spreading, dielectric or full-width copper polygons.
        """
        missing = {offset: 0.0 for offset in offsets}
        for (layer_a, ax, ay), (layer_b, bx, by) in zip(nodes, nodes[1:]):
            if layer_a != pcbnew.F_Cu or layer_b != pcbnew.F_Cu:
                raise AssertionError("DAC summing/feedback plane screen left F.Cu")
            x, y = pcbnew.ToMM(ax), pcbnew.ToMM(ay)
            dx, dy = pcbnew.ToMM(bx - ax), pcbnew.ToMM(by - ay)
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            count = math.ceil(length / 0.01)
            nx, ny = -dy / length, dx / length
            for index in range(count):
                fraction = (index + 0.5) / count
                sx, sy = x + dx * fraction, y + dy * fraction
                for offset in offsets:
                    probe = pcbnew.VECTOR2I(
                        pcbnew.FromMM(sx + nx * offset),
                        pcbnew.FromMM(sy + ny * offset))
                    if not l2.Contains(probe):
                        missing[offset] += length / count
        return {f"{offset:+.2f}": round(amount, 4)
                for offset, amount in missing.items()}

    dac_lengths = {}
    dac_l2_missing = {}
    first_t_lengths = {}
    feedback_areas = {}
    output_vias = {}
    for leg, path in IV_LEGS.items():
        input_group = {("U301", path.dac_pin), (path.opamp, path.input_pin),
                       (path.feedback_resistor, "1"), (path.feedback_capacitor, "1")}
        output_group = {(path.opamp, path.output_pin),
                        (path.feedback_resistor, "2"), (path.feedback_capacitor, "2"),
                        (path.clamp, "3"), (path.cm, "1"),
                        *((ref, "1") for ref in path.first_t)}
        if group("U301", path.dac_pin) != input_group:
            raise AssertionError(f"{leg} DAC/summing/feedback input group differs")
        if group(path.opamp, path.output_pin) != output_group:
            raise AssertionError(f"{leg} I/V output/feedback/clamp/CM/first-T group differs")
        output_vias[path.output_net] = sum(
            isinstance(item, pcbnew.PCB_VIA) and item.GetNetname() == path.output_net
            for item in board.GetTracks()
        )
        if any(item.GetNetname() == path.dac_net and
               (isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() != pcbnew.F_Cu)
               for item in board.GetTracks()):
            raise AssertionError(f"{path.dac_net} left F.Cu or used a via")
        dac_nodes, length = route(path.dac_net, ("U301", path.dac_pin),
                                  (path.opamp, path.input_pin))
        if length > 7.0 + 1e-6:
            raise AssertionError(f"{path.dac_net} DAC-to-summing copper exceeds 7 mm: {length:.3f}")
        dac_lengths[path.dac_net] = round(length, 3)
        l2_gaps = l2_missing_mm(dac_nodes, (-0.10, -0.05, 0.0, 0.05, 0.10))
        if any(l2_gaps.values()):
            raise AssertionError(f"{path.dac_net} has no direct L2 under part of its 0.20 mm input copper: {l2_gaps}")
        dac_l2_missing[path.dac_net] = l2_gaps
        first_t_lengths[path.output_net] = {}
        for ref in path.first_t:
            _, length = route(path.output_net, (path.opamp, path.output_pin), (ref, "1"))
            first_t_lengths[path.output_net][ref] = round(length, 3)
        for ref in (path.feedback_resistor, path.feedback_capacitor):
            input_nodes, _ = route(path.dac_net, (path.opamp, path.input_pin), (ref, "1"))
            output_nodes, _ = route(path.output_net, (ref, "2"),
                                    (path.opamp, path.output_pin))
            # The manifest freezes exact copper waypoints. Straight closures
            # across the part and opamp pads define a reproducible 2D review
            # polygon; this is not an extracted 3D return-current loop area.
            area = _projected_bounded_area(projected(input_nodes) + projected(output_nodes))
            if not 0 < area < 5.0:
                raise AssertionError(f"{ref} projected 2D I/V feedback loop exceeds 5 mm²: {area:.3f}")
            feedback_areas[ref] = round(area, 3)
    dacl_feedback_nodes, _ = route("DACL", ("U403", "6"), ("C417", "1"))
    dacl_feedback_gap = l2_missing_mm(dacl_feedback_nodes, (0.0,))["+0.00"]
    return {
        "iv_dac_to_summing_routes_mm": dac_lengths,
        "iv_direct_dac_l2_missing_mm_at_offsets": dac_l2_missing,
        "iv_direct_dac_l2_sample_pitch_mm": 0.01,
        "iv_dacl_feedback_l2_centreline_missing_mm": dacl_feedback_gap,
        "iv_l2_support_model": "Saved filled L2 GND sampled at 0.01 mm along F.Cu track centreline and +/-0.05/0.10 mm normal offsets; return impedance not extracted",
        "iv_output_to_t_first_resistor_feeds_mm": first_t_lengths,
        "iv_output_signal_vias_by_net": output_vias,
        "iv_feedback_projected_2d_centreline_loop_area_mm2": feedback_areas,
        "iv_feedback_area_model": "Plan-view copper centrelines with straight part/opamp pad closures; excludes vertical and return-current area",
    }


def _track_intersects_courtyard(track: pcbnew.PCB_TRACK,
                                courtyard: pcbnew.BOX2I) -> bool:
    """Check the track's copper-width envelope against the rectangular U501 courtyard."""
    a, b = track.GetStart(), track.GetEnd()
    x, y = pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)
    dx, dy = pcbnew.ToMM(b.x - a.x), pcbnew.ToMM(b.y - a.y)
    radius = pcbnew.ToMM(track.GetWidth()) / 2
    left = pcbnew.ToMM(courtyard.GetLeft()) - radius
    right = pcbnew.ToMM(courtyard.GetRight()) + radius
    top = pcbnew.ToMM(courtyard.GetTop()) - radius
    bottom = pcbnew.ToMM(courtyard.GetBottom()) + radius
    low, high = 0.0, 1.0
    for p, q in ((-dx, x - left), (dx, right - x),
                 (-dy, y - top), (dy, bottom - y)):
        if abs(p) < 1e-12:
            if q < -1e-9:
                return False
        elif p < 0:
            low = max(low, q / p)
        else:
            high = min(high, q / p)
    return low <= high + 1e-9


def check_u501_local(board: pcbnew.BOARD, footprints: dict,
                     connectivity, group) -> dict:
    """Gate the routed LM27762 switching, supply and feedback macro."""
    def pad(ref: str, number: str) -> pcbnew.PAD:
        return next(item for item in footprints[ref].Pads()
                    if item.GetNumber() == number)

    topology = (
        ("N5_C1P", ("U501", "10"), {("U501", "10"), ("C508", "1")}),
        ("N5_C1N", ("U501", "9"), {("U501", "9"), ("C508", "2")}),
        ("N5_CP", ("U501", "5"), {("U501", "5"), ("C509", "1")}),
        ("5V_ANA_F", ("U501", "12"),
         {("U501", "12"), ("U501", "8"), ("U501", "3"),
          ("C507", "1"), ("FB501", "2")}),
        ("VPOS", ("U501", "11"),
         {("U501", "11"), ("C510", "1"), ("R501", "1")}),
        ("VNEG", ("U501", "6"),
         {("U501", "6"), ("C511", "1"), ("R503", "1")}),
        ("N5_FBP", ("U501", "2"),
         {("U501", "2"), ("R501", "2"), ("R502", "1")}),
        ("N5_FBN", ("U501", "7"),
         {("U501", "7"), ("R504", "1"), ("R503", "2")}),
    )
    for net, source, members in topology:
        wrong = {f"{ref}.{number}": pad(ref, number).GetNetname()
                 for ref, number in members if pad(ref, number).GetNetname() != net}
        if wrong:
            raise AssertionError(f"U501 {net} pad net differs: {wrong}")
        missing = members - group(*source)
        if missing:
            raise AssertionError(f"U501 {net} local copper is open: {sorted(missing)}")

    ground_pads = {("U501", "4"), ("U501", "PAD"),
                   ("C507", "2"), ("C509", "2"),
                   ("C510", "2"), ("C511", "2"),
                   ("R502", "2"), ("R504", "2")}
    if any(pad(ref, number).GetNetname() != "GND"
           for ref, number in ground_pads):
        raise AssertionError("U501 local ground pad nets differ")
    if not ground_pads <= group("U501", "4"):
        raise AssertionError("U501 cap/divider/EP grounds lack connected copper")
    zones = [item for item in board.Zones()
             if item.GetNetname() == "GND" and item.IsOnLayer(pcbnew.In1_Cu)
             and item.HasFilledPolysForLayer(pcbnew.In1_Cu)]
    if (len(zones) != 1 or
            zones[0].GetFilledPolysList(pcbnew.In1_Cu).OutlineCount() != 1):
        raise AssertionError("U501 has no continuous filled L2 GND zone")

    def on_l2(item: pcbnew.BOARD_CONNECTED_ITEM) -> bool:
        return any(other.GetClass() == "ZONE" and other.GetNetname() == "GND"
                   and other.IsOnLayer(pcbnew.In1_Cu)
                   for other in connectivity.GetConnectedItems(item))

    for ref, number in ground_pads:
        if not on_l2(pad(ref, number)):
            raise AssertionError(f"{ref}.{number} has no filled L2 GND return")

    local_nets = {net for net, _, _ in topology} | {"GND"}
    if any(item.GetClass() == "PCB_ARC" and item.GetNetname() in local_nets
           for item in board.GetTracks()):
        raise AssertionError("U501 local arc is outside the centreline route model")
    graphs = {}

    def route_length(net: str, first: tuple[str, str],
                     last: tuple[str, str]) -> float:
        if net not in graphs:
            graphs[net] = copper_graph(board, net)
        edges = graphs[net]
        start = pcbnew.F_Cu, copper_point(pad(*first).GetPosition())
        end = pcbnew.F_Cu, copper_point(pad(*last).GetPosition())
        if start not in edges or end not in edges:
            raise AssertionError(f"{net} pad-centre copper is absent: {first}->{last}")
        heap = [(0.0, start)]
        distances = {start: 0.0}
        while heap:
            length, here = heapq.heappop(heap)
            if here == end:
                return length
            if length > distances[here] + 1e-9:
                continue
            for there, _, segment_length in edges[here]:
                candidate = length + segment_length
                if candidate < distances.get(there, math.inf) - 1e-9:
                    distances[there] = candidate
                    heapq.heappush(heap, (candidate, there))
        raise AssertionError(f"{net} pad-centre route is open: {first}->{last}")

    route_specs = (
        ("c1p_to_c508", "N5_C1P", ("U501", "10"), ("C508", "1"), 2.6),
        ("c1n_to_c508", "N5_C1N", ("U501", "9"), ("C508", "2"), 2.6),
        ("cp_to_c509", "N5_CP", ("U501", "5"), ("C509", "1"), 2.3),
        ("vin12_to_c507", "5V_ANA_F", ("U501", "12"), ("C507", "1"), 2.4),
        ("vin8_to_c507", "5V_ANA_F", ("U501", "8"), ("C507", "1"), 6.2),
        ("vin3_to_c507", "5V_ANA_F", ("U501", "3"), ("C507", "1"), 6.1),
        ("fb501_to_c507", "5V_ANA_F", ("FB501", "2"), ("C507", "1"), 17.5),
        ("vpos_to_c510", "VPOS", ("U501", "11"), ("C510", "1"), 4.2),
        ("c510_to_r501", "VPOS", ("C510", "1"), ("R501", "1"), 12.5),
        ("vneg_to_c511", "VNEG", ("U501", "6"), ("C511", "1"), 3.7),
        ("c511_to_r503", "VNEG", ("C511", "1"), ("R503", "1"), 10.7),
        ("fbp_to_r501", "N5_FBP", ("U501", "2"), ("R501", "2"), 2.5),
        ("r501_to_r502", "N5_FBP", ("R501", "2"), ("R502", "1"), 2.0),
        ("fbn_to_r504", "N5_FBN", ("U501", "7"), ("R504", "1"), 2.3),
        ("r504_to_r503", "N5_FBN", ("R504", "1"), ("R503", "2"), 1.8),
    )
    route_lengths = {}
    for name, net, first, last, limit in route_specs:
        length = route_length(net, first, last)
        if length > limit + 1e-6:
            raise AssertionError(f"U501 {name} exceeds {limit} mm: {length:.3f}")
        route_lengths[name] = round(length, 3)

    supply_tracks = [item for item in board.GetTracks()
                     if item.GetNetname() == "5V_ANA_F"
                     and not isinstance(item, pcbnew.PCB_VIA)]
    narrow = [item for item in supply_tracks
              if pcbnew.ToMM(item.GetWidth()) < 0.8 - 1e-6]
    other = [item for item in supply_tracks if item not in narrow]
    if not narrow or not other:
        raise AssertionError("U501 VIN escapes or 0.8 mm feeder are missing")
    courtyard = footprints["U501"].GetCourtyard(pcbnew.F_CrtYd).BBox()
    for item in narrow:
        width = pcbnew.ToMM(item.GetWidth())
        if (item.GetLayer() != pcbnew.F_Cu or width < 0.2 - 1e-6
                or not _track_intersects_courtyard(item, courtyard)):
            raise AssertionError("Narrow 5V_ANA_F track leaves the U501 escape corridor")
    # All sub-0.8 mm supply segments are in `narrow`; the component check
    # below requires every one to belong to a bounded WSON pin escape.
    incident = collections.defaultdict(set)
    for index, item in enumerate(narrow):
        for at in (item.GetStart(), item.GetEnd()):
            incident[at.x, at.y].add(index)
    visited = set()
    branches = {}
    limits = {"12": 1.10, "8": 1.20, "3": 0.90}
    for index in range(len(narrow)):
        if index in visited:
            continue
        stack = [index]
        component = set()
        endpoints = set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            for at in (narrow[current].GetStart(), narrow[current].GetEnd()):
                key = at.x, at.y
                endpoints.add(key)
                stack.extend(incident[key] - component)
        visited.update(component)
        pins = [number for number in limits
                if (pad("U501", number).GetPosition().x,
                    pad("U501", number).GetPosition().y) in endpoints]
        if len(pins) != 1 or pins[0] in branches:
            raise AssertionError("5V_ANA_F narrow copper is not three VIN pin escapes")
        number = pins[0]
        length = sum(math.hypot(
            pcbnew.ToMM(narrow[i].GetEnd().x - narrow[i].GetStart().x),
            pcbnew.ToMM(narrow[i].GetEnd().y - narrow[i].GetStart().y))
            for i in component)
        if length > limits[number] + 1e-6:
            raise AssertionError(f"U501.{number} narrow VIN escape exceeds {limits[number]} mm")
        branches[number] = round(length, 3)
    if set(branches) != set(limits):
        raise AssertionError(f"U501 VIN escape branches differ: {branches}")

    ground_graph = copper_graph(board, "GND")
    zone_vias = {
        (pcbnew.F_Cu, copper_point(item.GetPosition())): item
        for item in board.GetTracks()
        if isinstance(item, pcbnew.PCB_VIA) and item.GetNetname() == "GND"
        and item.IsOnLayer(pcbnew.F_Cu) and item.IsOnLayer(pcbnew.In1_Cu)
        and on_l2(item)
    }

    def ground_to_via(ref: str, number: str) -> tuple[float, pcbnew.PCB_VIA]:
        start = pcbnew.F_Cu, copper_point(pad(ref, number).GetPosition())
        if start not in ground_graph:
            raise AssertionError(f"{ref}.{number} has no F.Cu ground escape")
        heap = [(0.0, start)]
        distances = {start: 0.0}
        while heap:
            length, here = heapq.heappop(heap)
            if here in zone_vias:
                return length, zone_vias[here]
            if length > distances[here] + 1e-9:
                continue
            for there, _, segment_length in ground_graph[here]:
                if there[0] != pcbnew.F_Cu:
                    continue
                candidate = length + segment_length
                if candidate < distances.get(there, math.inf) - 1e-9:
                    distances[there] = candidate
                    heapq.heappush(heap, (candidate, there))
        raise AssertionError(f"{ref}.{number} has no local F.Cu-to-L2 ground via")

    ground_lengths = {}
    ground_vias = {}
    for ref, number, limit in (("U501", "4", 2.7),
                               ("C507", "2", 1.5), ("C509", "2", 1.5),
                               ("C510", "2", 1.5), ("C511", "2", 1.5),
                               ("R502", "2", 1.5), ("R504", "2", 1.5)):
        length, via = ground_to_via(ref, number)
        if length > limit + 1e-6:
            raise AssertionError(f"{ref}.{number} GND via route exceeds {limit} mm")
        name = f"{ref}.{number}"
        ground_lengths[name] = round(length, 3)
        at = via.GetPosition()
        ground_vias[name] = (pcbnew.ToMM(at.x), pcbnew.ToMM(at.y))
    u_ground = ground_vias["U501.4"]
    l2_spacing = {name: round(math.dist(at, u_ground), 3)
                  for name, at in ground_vias.items() if name.startswith("C")}
    # Project the feeder and sensitive feedback trace copper to the same
    # plane. This geometry screen removes their former crossing near an L2
    # via antipad; it is not a noise or coupling extraction.
    vin_bottom = pcbnew.SHAPE_POLY_SET()
    fbp_top = pcbnew.SHAPE_POLY_SET()
    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_VIA):
            continue
        if track.GetNetname() == "5V_ANA_F" and track.GetLayer() == pcbnew.B_Cu:
            track.TransformShapeToPolygon(vin_bottom, pcbnew.B_Cu, 0,
                                          pcbnew.FromMM(0.0001), pcbnew.ERROR_OUTSIDE)
        elif track.GetNetname() == "N5_FBP" and track.GetLayer() == pcbnew.F_Cu:
            track.TransformShapeToPolygon(fbp_top, pcbnew.F_Cu, 0,
                                          pcbnew.FromMM(0.0001), pcbnew.ERROR_OUTSIDE)
    vin_bottom.BooleanAdd(vin_bottom)
    fbp_top.BooleanAdd(fbp_top)
    vin_bottom.BooleanIntersection(fbp_top)
    fbp_projection_mm2 = vin_bottom.Area() / 1e12
    if fbp_projection_mm2 > 1e-6:
        raise AssertionError(f"U501 feeder projects across FBP copper: {fbp_projection_mm2:.6f} mm²")
    return {
        "u501_local_pad_centre_routes_mm": route_lengths,
        "u501_vin_narrow_escape_branches_mm": branches,
        "u501_vin_narrow_min_width_mm": round(min(
            pcbnew.ToMM(item.GetWidth()) for item in narrow), 3),
        "u501_other_5v_ana_f_track_min_width_mm": round(min(
            pcbnew.ToMM(item.GetWidth()) for item in other), 3),
        "u501_ground_fcu_pad_to_l2_via_mm": ground_lengths,
        "u501_ground_l2_via_spacing_to_ic_mm": l2_spacing,
        "u501_ground_l2_spacing_model": "Straight via-to-via spacing in one connected filled L2 zone; not an extracted return-current path",
        "u501_fbp_feeder_projected_track_overlap_mm2": round(fbp_projection_mm2, 6),
        "u501_fbp_projection_model": "KiCad B.Cu 5V_ANA_F track polygons projected onto F.Cu N5_FBP tracks; pads, dielectric and noise excluded",
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
                    round(pcbnew.ToMM(item.GetDrillValue()), 4),
                    bool(item.GetPrimaryDrillFilledFlag()),
                    bool(item.GetPrimaryDrillCappedFlag()))
        a, b = item.GetStart(), item.GetEnd()
        return ("track", item.GetNetname(), item.GetLayerName(),
                round(pcbnew.ToMM(a.x), 4), round(pcbnew.ToMM(a.y), 4),
                round(pcbnew.ToMM(b.x), 4), round(pcbnew.ToMM(b.y), 4),
                round(pcbnew.ToMM(item.GetWidth()), 4))

    def manifest_item(item: dict) -> tuple:
        if item["kind"] == "via":
            return ("via", item["net"], *item["at_mm"],
                    item["diameter_mm"], item["drill_mm"],
                    bool(item.get("filled", False)), bool(item.get("capped", False)))
        return ("track", item["net"], item["layer"],
                *item["start_mm"], *item["end_mm"], item["width_mm"])

    base_copper = collections.Counter(copper_item(item) for item in source.GetTracks())
    candidate_copper = collections.Counter(copper_item(item) for item in board.GetTracks())
    removed_copper = collections.Counter(manifest_item(item)
                                         for item in manual.get("removed_source_copper", []))
    added_copper = collections.Counter(manifest_item(item)
                                       for item in manual["added_copper"])
    if removed_copper - base_copper:
        raise AssertionError("Manual source-copper removal record is stale")
    if candidate_copper != base_copper - removed_copper + added_copper:
        raise AssertionError("Manual copper record differs from the PCB")

    # Screen both exact and almost-orthogonal free-copper elbows. A component
    # pad centre is a copper landing, while a branch with straight-through
    # copper is a T/cross junction rather than a turn in the main trace.
    incident = collections.defaultdict(list)
    track_layers = {item.GetLayer() for item in board.GetTracks()
                    if not isinstance(item, pcbnew.PCB_VIA)}
    pad_centres = {
        (pad.GetNetname(), layer, pad.GetPosition().x, pad.GetPosition().y)
        for footprint in board.GetFootprints() for pad in footprint.Pads()
        for layer in track_layers if pad.IsOnLayer(layer)
    }
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            continue
        a, b = item.GetStart(), item.GetEnd()
        if a == b:
            raise AssertionError("Zero-length audio-study track")
        for here, other in ((a, b), (b, a)):
            incident[(item.GetNetname(), item.GetLayer(), here.x, here.y)].append(
                (other.x - here.x, other.y - here.y))
    right_angle_bends = []
    near_right_angle_free_bends = []
    pad_centre_near_orthogonal_joins = []
    orthogonal_branches_without_through = []
    near_cosine = math.sin(math.radians(10.0))
    through_cosine = -math.cos(math.radians(5.0))
    for key, vectors in incident.items():
        net, layer, x, y = key
        angles = []
        for index, (ax, ay) in enumerate(vectors):
            for bx, by in vectors[index + 1:]:
                angles.append((ax * bx + ay * by) /
                              (math.hypot(ax, ay) * math.hypot(bx, by)))
        location = (net, board.GetLayerName(layer),
                    round(pcbnew.ToMM(x), 3), round(pcbnew.ToMM(y), 3))
        if len(vectors) == 2:
            cosine = angles[0]
            if abs(cosine) < 1e-5:
                right_angle_bends.append(location)
            if abs(cosine) <= near_cosine:
                if key in pad_centres:
                    pad_centre_near_orthogonal_joins.append(location)
                else:
                    near_right_angle_free_bends.append(location)
        elif (len(vectors) > 2 and any(abs(cosine) <= near_cosine
                                        for cosine in angles)
              and not any(cosine <= through_cosine for cosine in angles)
              and key not in pad_centres):
            orthogonal_branches_without_through.append(location)
    if right_angle_bends:
        raise AssertionError(f"Right-angle track bends remain: {right_angle_bends[:8]}")
    if near_right_angle_free_bends or orthogonal_branches_without_through:
        raise AssertionError(
            "Near-orthogonal free-copper bends or branches remain: "
            f"{near_right_angle_free_bends[:8]}, "
            f"{orthogonal_branches_without_through[:8]}")

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

    iv_result = check_iv_macro(board, footprints, group)
    u501_result = check_u501_local(board, footprints, connectivity, group)

    for leg, (opamp, out_pin, inn_pin, rf, cf, link, relay) in CHANNELS.items():
        if group(opamp, out_pin) != {
            (opamp, out_pin), (rf, "2"), (cf, "2"), (link, "1"),
        }:
            raise AssertionError(f"{leg} amplifier output/load/feedback copper differs")
        if group(opamp, inn_pin) != {
            (opamp, inn_pin), (rf, "1"), (cf, "1"),
            (NEGATIVE_T_SECOND[leg], "2"),
        }:
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
    bypass_pad_distances = {}
    for opamp, rail, pins, caps in (
        ("U401", "VPOS", ("2",), ("C409", "C411")),
        ("U401", "VNEG", ("4", "PAD"), ("C410", "C412")),
        ("U402", "VPOS", ("2",), ("C409", "C411")),
        ("U402", "VNEG", ("4", "PAD"), ("C410", "C412")),
    ):
        for pin in pins:
            at = pad(opamp, pin).GetPosition()
            here = pcbnew.ToMM(at.x), pcbnew.ToMM(at.y)
            nearest = min(
                math.dist(here, (pcbnew.ToMM(v.GetPosition().x),
                                 pcbnew.ToMM(v.GetPosition().y)))
                for cap in caps for v in footprints[cap].Pads()
                if v.GetNumber() == "1"
            )
            bypass_pad_distances[f"{opamp}.{pin} {rail}"] = round(nearest, 2)
    local_vpos = {
        ("U401", "2"), ("U401", "8"), ("C409", "1"),
        ("U402", "2"), ("U402", "8"), ("C411", "1"),
    }
    for opamp in ("U401", "U402"):
        if pad(opamp, "8").GetNetname() != "VPOS":
            raise AssertionError(f"{opamp}.8 EN must be tied to the positive rail")
        if group(opamp, "8") != local_vpos:
            raise AssertionError(f"{opamp}.8 EN lacks the local VPOS copper group")
    for opamp, cap in (("U401", "C409"), ("U402", "C411")):
        if (cap, "1") not in group(opamp, "2"):
            raise AssertionError(f"{opamp}.2 V+ does not reach local {cap} over L3")
        if not any(item.GetClass() == "ZONE"
                   for item in connectivity.GetConnectedItems(pad(cap, "2"))):
            raise AssertionError(f"{cap} 100 nF ground return is not on L2")
    for opamp, cap in (("U401", "C410"), ("U402", "C412")):
        local_vneg = group(opamp, "4")
        if not {(opamp, "4"), (opamp, "PAD"), (cap, "1")} <= local_vneg:
            raise AssertionError(f"{opamp} exposed VNEG pad and {cap} are not locally connected")
        if not any(item.GetClass() == "ZONE"
                   for item in connectivity.GetConnectedItems(pad(cap, "2"))):
            raise AssertionError(f"{cap} 100 nF ground return is not on L2")
    t_lengths = {}
    for leg, first, second, cap, opamp, input_pin in T_CELLS:
        t_net = pad(first, "2").GetNetname()
        if group(first, "2") != {(first, "2"), (second, "1"), (cap, "1")}:
            raise AssertionError(f"{leg} T resistor/capacitor copper is incomplete")
        if (opamp, input_pin) not in group(second, "2"):
            raise AssertionError(f"{leg} T output does not reach the amplifier input")
        if not any(item.GetClass() == "ZONE"
                   for item in connectivity.GetConnectedItems(pad(cap, "2"))):
            raise AssertionError(f"{leg} T capacitor has no L2 ground return")
        if any(t.GetNetname() == t_net and
               (isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != pcbnew.F_Cu)
               for t in board.GetTracks()):
            raise AssertionError(f"{leg} T node left the top copper layer")
        input_net = pad(second, "2").GetNetname()
        lengths = {
            "first_to_second": copper_route(board, footprints, t_net,
                                              (first, "2"), (second, "1"))[1],
            "capacitor_to_second": copper_route(board, footprints, t_net,
                                                  (cap, "1"), (second, "1"))[1],
            "second_to_amp": copper_route(board, footprints, input_net,
                                           (second, "2"), (opamp, input_pin))[1],
        }
        if max(lengths.values()) > 10.0:
            raise AssertionError(f"{leg} local T route exceeds the 10 mm review screen")
        t_lengths[leg] = {name: round(length, 2)
                          for name, length in lengths.items()}
    for shunt, opamp, pin in (("R404", "U401", "1"),
                              ("R408", "U401", "5"),
                              ("R412", "U402", "1"),
                              ("R416", "U402", "5")):
        if (opamp, pin) not in group(shunt, "1"):
            raise AssertionError(f"{shunt} input shunt does not reach {opamp}.{pin}")
        if not any(item.GetClass() == "ZONE"
                   for item in connectivity.GetConnectedItems(pad(shunt, "2"))):
            raise AssertionError(f"{shunt} input shunt has no L2 return")
    return {
        "board": board_path.name,
        "footprints": 544,
        "named_nets": 250,
        "manual_moves": len(manual["moved_footprints"]),
        "manual_replaced_source_copper_items": len(manual.get("removed_source_copper", [])),
        "manual_added_copper_items": len(manual["added_copper"]),
        "right_angle_track_bends": 0,
        "near_right_angle_free_track_bends": 0,
        "orthogonal_branches_without_through": 0,
        "pad_centre_near_orthogonal_joins": len(pad_centre_near_orthogonal_joins),
        "drc_violations": 0,
        "bbox_overlaps": 0,
        "jlc_spacing_and_edge_proxy_findings": 0,
        "l2_gnd_filled_polygons": 1,
        "feedback_centreline_loop_area_mm2": feedback_areas,
        **iv_result,
        **u501_result,
        "local_tvs_routes_mm": tvs["local_routes_mm"],
        "output_amp_hf_bypass_pad_lower_bound_mm": bypass_pad_distances,
        "routed_t_cell_count": len(t_lengths),
        "routed_t_cell_branch_lengths_mm": t_lengths,
        "output_amp_enable_pin8": "U401/U402 EN pin 8 physically joins both VPOS supply pins and local C409/C411; main source feed remains open",
        "local_vpos_pin2_to_cap_and_l2_return": "U401/C409 and U402/C411 connected through local L3 bridges; main rail feed remains open",
        "local_vneg_pad_to_cap_and_l2_return": "U401/C410 and U402/C412 connected; rail feeds and EP thermal vias remain open",
        "balanced_4p4_planning_estimate_1khz": trace["balanced_4p4_planning_estimate_1khz"],
        "balanced_4p4_model_sensitivity_20khz": trace["balanced_4p4_model_sensitivity_20khz"],
        "drc_reported_unconnected_items": len(drc["unconnected_items"]),
        "ratsnest_unconnected_items": connectivity.GetUnconnectedCount(False),
        "routing_release": "HOLD: DACL feedback L2 detour, I/V stability and return extraction, main rails/bulk, EP thermal, R-15 measurement, F01–F04 and G-3/G-4",
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
