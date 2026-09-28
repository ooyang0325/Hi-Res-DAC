#!/usr/bin/env python3
"""Measure the six local jack-to-TVS copper paths on branched audio nets.

KiCad's generic ``length`` custom constraint can count additional branches
after a second jack contact or relay is routed. This audit instead measures
the shortest actual F.Cu centreline path between the named physical pads.
It does not replace system IEC ESD testing or return-current inspection.
"""

from __future__ import annotations

import argparse
import collections
import heapq
import json
import math
from pathlib import Path

import pcbnew


PAIRS = (
    ("LP J701", "JACK_LP", "J701", "7", "D701", "1"),
    ("RP J701", "JACK_RP", "J701", "5", "D702", "1"),
    ("LN J701", "JACK_LN", "J701", "6", "D703", "1"),
    ("RN J701", "JACK_RN", "J701", "2", "D704", "1"),
    ("RP J702", "JACK_RP", "J702", "3", "D707", "1"),
    ("LP J702", "JACK_LP", "J702", "4", "D708", "1"),
)
LIMIT_MM = 4.2  # Owner-approved provisional routed screen; system test open.


def point(vec: pcbnew.VECTOR2I) -> tuple[float, float]:
    return round(pcbnew.ToMM(vec.x), 3), round(pcbnew.ToMM(vec.y), 3)


def cross(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


def on_segment(p: tuple[float, float], a: tuple[float, float],
               b: tuple[float, float]) -> bool:
    ab = (b[0] - a[0], b[1] - a[1])
    ap = (p[0] - a[0], p[1] - a[1])
    length2 = ab[0] ** 2 + ab[1] ** 2
    if length2 < 1e-12:
        return math.dist(p, a) < 0.01
    t = (ap[0] * ab[0] + ap[1] * ab[1]) / length2
    projection = (a[0] + t * ab[0], a[1] + t * ab[1])
    return -0.001 <= t <= 1.001 and math.dist(p, projection) < 0.01


def crossings(a: tuple, b: tuple, c: tuple, d: tuple) -> set[tuple]:
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    ca = (c[0] - a[0], c[1] - a[1])
    denominator = cross(r, s)
    if abs(denominator) > 1e-9:
        t = cross(ca, s) / denominator
        u = cross(ca, r) / denominator
        if -0.001 <= t <= 1.001 and -0.001 <= u <= 1.001:
            return {(round(a[0] + t * r[0], 3), round(a[1] + t * r[1], 3))}
        return set()
    if abs(cross(ca, r)) > 0.01:
        return set()
    return {p for p in (a, b, c, d)
            if on_segment(p, a, b) and on_segment(p, c, d)}


def copper_graph(board: pcbnew.BOARD, net: str) -> dict[tuple, list[tuple]]:
    segments = [(point(t.GetStart()), point(t.GetEnd()))
                for t in board.GetTracks()
                if not isinstance(t, pcbnew.PCB_VIA)
                and t.GetLayer() == pcbnew.F_Cu and t.GetNetname() == net]
    splits = [{a, b} for a, b in segments]
    for i, (a, b) in enumerate(segments):
        for j in range(i + 1, len(segments)):
            shared = crossings(a, b, *segments[j])
            splits[i].update(shared)
            splits[j].update(shared)
    graph: dict[tuple, list[tuple]] = collections.defaultdict(list)
    for (a, b), nodes in zip(segments, splits):
        ordered = sorted(nodes, key=lambda p: math.dist(a, p))
        for u, v in zip(ordered, ordered[1:]):
            length = math.dist(u, v)
            graph[u].append((v, length))
            graph[v].append((u, length))
    return graph


def pad_nodes(pad: pcbnew.PAD, graph: dict) -> list[tuple[tuple, float]]:
    center = point(pad.GetPosition())
    box = pad.GetBoundingBox()
    left, right = pcbnew.ToMM(box.GetLeft()), pcbnew.ToMM(box.GetRight())
    top, bottom = pcbnew.ToMM(box.GetTop()), pcbnew.ToMM(box.GetBottom())
    return [(node, math.dist(center, node)) for node in graph
            if left - 0.02 <= node[0] <= right + 0.02
            and top - 0.02 <= node[1] <= bottom + 0.02]


def local_length(graph: dict, source: pcbnew.PAD, target: pcbnew.PAD) -> float:
    starts = pad_nodes(source, graph)
    ends = dict(pad_nodes(target, graph))
    if not starts or not ends:
        raise AssertionError("A named pad has no F.Cu centreline endpoint")
    heap = [(distance, node) for node, distance in starts]
    heapq.heapify(heap)
    distance_by_node = {node: distance for node, distance in starts}
    best = math.inf
    while heap:
        distance, node = heapq.heappop(heap)
        if distance > distance_by_node[node] + 1e-9:
            continue
        if node in ends:
            best = min(best, distance + ends[node])
        if distance >= best:
            continue
        for neighbor, length in graph[node]:
            next_distance = distance + length
            if next_distance + 1e-9 < distance_by_node.get(neighbor, math.inf):
                distance_by_node[neighbor] = next_distance
                heapq.heappush(heap, (next_distance, neighbor))
    if not math.isfinite(best):
        raise AssertionError("Named pads have no continuous L1 copper path")
    return best


def audit(board_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    result = {}
    for label, net, jack_ref, jack_pin, tvs_ref, tvs_pin in PAIRS:
        jack = next(p for p in footprints[jack_ref].Pads() if p.GetNumber() == jack_pin)
        tvs = next(p for p in footprints[tvs_ref].Pads() if p.GetNumber() == tvs_pin)
        if jack.GetNetname() != net or tvs.GetNetname() != net:
            raise AssertionError(f"{label}: pad net differs from {net}")
        length = local_length(copper_graph(board, net), jack, tvs)
        if length > LIMIT_MM + 1e-6:
            raise AssertionError(f"{label}: local L1 path {length:.3f} > {LIMIT_MM} mm")
        result[label] = round(length, 3)
    return {
        "board": board_path.name,
        "method": "shortest named-pad F.Cu centreline path, with same-net junctions",
        "provisional_limit_mm": LIMIT_MM,
        "local_routes_mm": result,
        "system_iec_esd": "HOLD: discharge return, nonlinear loading and system test",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(audit(args.board), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
