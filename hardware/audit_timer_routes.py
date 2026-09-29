#!/usr/bin/env python3
"""Measure each protection timer branch by its shortest actual F.Cu path.

KiCad's fromTo length rule can count a sibling branch on these shared timer
nets. The 8 mm design target applies to each named IC-to-R/C/Q connection.
Open branches are reported as routing HOLD; --require-complete is the release
gate. Timer nodes stay on F.Cu with no vias unless separately requalified.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
from pathlib import Path

import pcbnew

from audit_local_tvs_paths import copper_graph, local_length, pad_nodes, point


LIMIT_MM = 8.0
BRANCHES = (
    ("LP_L", "N6_TLP_L", "U609", "8",
     (("C631", "1"), ("Q623", "3"), ("R920", "2"))),
    ("LN_L", "N6_TLN_L", "U609", "10",
     (("C632", "1"), ("Q624", "3"), ("R921", "2"))),
    ("LP_R", "N6_TLP_R", "U610", "8",
     (("C633", "1"), ("Q625", "3"), ("R922", "2"))),
    ("LN_R", "N6_TLN_R", "U610", "10",
     (("C634", "1"), ("Q626", "3"), ("R923", "2"))),
)
FILM_CAPACITORS = ("C631", "C632", "C633", "C634")


def local_ground_return(board: pcbnew.BOARD, pad: pcbnew.PAD,
                        graph: dict) -> float | None:
    """Find F.Cu copper from a film GND pad to a via on filled L2 GND."""
    connected = board.GetConnectivity().GetConnectedItems(pad)
    if not any(item.GetClass() == "ZONE" and item.GetNetname() == "GND"
               and item.IsOnLayer(pcbnew.In1_Cu) for item in connected):
        return None
    via_nodes = {point(item.GetPosition()) for item in connected
                 if item.GetClass() == "PCB_VIA"
                 and item.GetNetname() == "GND"
                 and item.IsOnLayer(pcbnew.F_Cu)
                 and item.IsOnLayer(pcbnew.In1_Cu)}
    starts = pad_nodes(pad, graph)
    if not starts:
        return None
    heap = [(distance, node) for node, distance in starts]
    heapq.heapify(heap)
    distances = {node: distance for node, distance in starts}
    while heap:
        distance, node = heapq.heappop(heap)
        if distance > distances[node] + 1e-9:
            continue
        if node in via_nodes:
            return distance
        for neighbor, length in graph[node]:
            candidate = distance + length
            if candidate + 1e-9 < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                heapq.heappush(heap, (candidate, neighbor))
    return None


def audit(board_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    board.BuildConnectivity()
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}

    def pad(ref: str, number: str, net: str) -> pcbnew.PAD:
        matches = [item for item in footprints[ref].Pads()
                   if item.GetNumber() == number]
        if len(matches) != 1 or matches[0].GetNetname() != net:
            raise AssertionError(f"Timer pad identity changed: {ref}.{number} {net}")
        return matches[0]

    routes = {}
    open_routes = []
    violations = []
    via_count = {}
    for label, net, source_ref, source_pin, targets in BRANCHES:
        source = pad(source_ref, source_pin, net)
        graph = copper_graph(board, net)
        via_count[net] = sum(isinstance(item, pcbnew.PCB_VIA)
                             and item.GetNetname() == net
                             for item in board.GetTracks())
        if via_count[net]:
            violations.append(f"{net}: {via_count[net]} timer-node vias")
        for target_ref, target_pin in targets:
            target = pad(target_ref, target_pin, net)
            name = f"{label} {source_ref}.{source_pin}→{target_ref}.{target_pin}"
            try:
                length = local_length(graph, source, target)
            except AssertionError:
                routes[name] = None
                open_routes.append(name)
                continue
            routes[name] = round(length, 3)
            if length > LIMIT_MM + 1e-6:
                violations.append(f"{name}: {length:.3f} > {LIMIT_MM:.1f} mm")
    ground_graph = copper_graph(board, "GND")
    ground_returns = {}
    open_ground_returns = []
    for ref in FILM_CAPACITORS:
        capacitor = pad(ref, "2", "GND")
        length = local_ground_return(board, capacitor, ground_graph)
        if length is None:
            open_ground_returns.append(f"{ref}.2→L2 GND")
        else:
            ground_returns[ref] = round(length, 3)
    return {
        "board": board_path.name,
        "limit_mm": LIMIT_MM,
        "method": "shortest F.Cu centreline path between named pad centres,"
                  " splitting same-net junctions; unconnected branches are"
                  " reported separately",
        "timer_vias_by_net": via_count,
        "connected_routes_mm": {name: length for name, length in routes.items()
                                if length is not None},
        "open_routes": open_routes,
        "film_cap_ground_returns_mm": ground_returns,
        "open_film_cap_ground_returns": open_ground_returns,
        "violations": violations,
        "release_status": "HOLD" if (open_routes or open_ground_returns
                                      or violations) else "geometry-pass",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gate", action="store_true",
                        help="Fail on connected path over 8 mm or timer via")
    parser.add_argument("--require-complete", action="store_true",
                        help="Also fail while any timer path remains open")
    args = parser.parse_args()
    result = audit(args.board)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    if args.gate and result["violations"]:
        raise SystemExit(f"{len(result['violations'])} protection timer"
                         " route limit violations")
    if args.require_complete and (result["open_routes"]
                                  or result["open_film_cap_ground_returns"]):
        raise SystemExit(f"{len(result['open_routes'])} timer branches and "
                         f"{len(result['open_film_cap_ground_returns'])}"
                         " film-capacitor GND returns still open")


if __name__ == "__main__":
    main()
