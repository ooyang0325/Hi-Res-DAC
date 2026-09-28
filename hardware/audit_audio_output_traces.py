#!/usr/bin/env python3
"""Plan the routed output conductor/impedance budget from KiCad copper.

The result is an engineering estimate, not a pass of R-15. It omits via
variation, contact maxima, sleeve-return impedance and extracted AC behavior.
"""

from __future__ import annotations

import argparse
import collections
import heapq
import json
import math
from pathlib import Path

import pcbnew

from audit_local_tvs_paths import crossings, point


LAYER = {pcbnew.F_Cu, pcbnew.B_Cu}
SHEET_MOHM_PER_SQUARE = 0.551  # v1.1 package, 35 µm copper at 50 °C.


def graph(board: pcbnew.BOARD, net: str):
    segments = [
        (t.GetLayer(), point(t.GetStart()), point(t.GetEnd()), pcbnew.ToMM(t.GetWidth()))
        for t in board.GetTracks()
        if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net and t.GetLayer() in LAYER
    ]
    splits = [{a, b} for _, a, b, _ in segments]
    for i, (layer, a, b, _) in enumerate(segments):
        for j in range(i + 1, len(segments)):
            layer2, c, d, _ = segments[j]
            if layer == layer2:
                shared = crossings(a, b, c, d)
                splits[i].update(shared)
                splits[j].update(shared)
    result = collections.defaultdict(list)
    for (layer, a, b, width), nodes in zip(segments, splits):
        ordered = sorted(nodes, key=lambda p: math.dist(a, p))
        for u, v in zip(ordered, ordered[1:]):
            length = math.dist(u, v)
            result[layer, u].append(((layer, v), length / width, length))
            result[layer, v].append(((layer, u), length / width, length))
    for via in board.GetTracks():
        if isinstance(via, pcbnew.PCB_VIA) and via.GetNetname() == net:
            where = point(via.GetPosition())
            for a, b in ((pcbnew.F_Cu, pcbnew.B_Cu), (pcbnew.B_Cu, pcbnew.F_Cu)):
                result[a, where].append(((b, where), 0.0, 0.0))
    return result


def pad(footprints, ref, number):
    return next(p for p in footprints[ref].Pads() if p.GetNumber() == number)


def pad_nodes(pad_item, g):
    box = pad_item.GetBoundingBox()
    xmin = pcbnew.ToMM(box.GetLeft()) - .02
    xmax = pcbnew.ToMM(box.GetRight()) + .02
    ymin = pcbnew.ToMM(box.GetTop()) - .02
    ymax = pcbnew.ToMM(box.GetBottom()) + .02
    return [node for node in g if node[0] == pcbnew.F_Cu
            and xmin <= node[1][0] <= xmax and ymin <= node[1][1] <= ymax]


def route(board: pcbnew.BOARD, footprints, net, first, last):
    g = graph(board, net)
    starts = pad_nodes(pad(footprints, *first), g)
    ends = set(pad_nodes(pad(footprints, *last), g))
    if not starts or not ends:
        raise ValueError((net, first, last, 'no pad nodes'))
    heap = [(0.0, 0.0, x) for x in starts]
    heapq.heapify(heap)
    seen = {x: 0.0 for x in starts}
    while heap:
        squares, length, node = heapq.heappop(heap)
        if squares > seen[node] + 1e-9:
            continue
        if node in ends:
            return squares, length
        for neighbor, ds, dl in g[node]:
            value = squares + ds
            if value + 1e-9 < seen.get(neighbor, math.inf):
                seen[neighbor] = value
                heapq.heappush(heap, (value, length + dl, neighbor))
    raise ValueError((net, first, last, 'no path'))


CHANNELS = {
    'LP': ('U401', '9', 'R417', 'K601', [('J701', '7'), ('J701', '8'), ('J702', '4')]),
    'LN': ('U401', '7', 'R418', 'K602', [('J701', '6')]),
    'RP': ('U402', '9', 'R419', 'K603', [('J701', '4'), ('J701', '5'), ('J702', '3')]),
    'RN': ('U402', '7', 'R420', 'K604', [('J701', '2'), ('J701', '3')]),
}


def via_mohm_20um_plating() -> float:
    """Illustrative 1.6 mm, 0.20 mm drill via at 50 °C, not a fab minimum."""
    resistivity = 1.724e-8 * (1 + 0.00393 * (50 - 20))
    bore_radius = 0.10e-3
    plating = 0.020e-3
    wall_area = math.pi * ((bore_radius + plating) ** 2 - bore_radius ** 2)
    return resistivity * 1.6e-3 / wall_area * 1000


def audit(board_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    result = {}
    via_count = {}
    for leg, (op, pin, link, relay, contacts) in CHANNELS.items():
        first = route(board, footprints, f'N4_{leg}_OUT', (op, pin), (link, '1'))
        second = route(board, footprints, f'LEG_{leg}', (link, '2'), (relay, '4'))
        via_count[leg] = sum(isinstance(t, pcbnew.PCB_VIA)
                             and t.GetNetname() == f'N4_{leg}_OUT'
                             for t in board.GetTracks())
        if via_count[leg] != 2:
            raise AssertionError(f'{leg}: expected two routed output signal vias')
        contacts_result = {}
        for jack in contacts:
            third = route(board, footprints, f'JACK_{leg}', (relay, '6'), jack)
            squares = first[0] + second[0] + third[0]
            contacts_result[jack[0] + '.' + jack[1]] = {
                'trace_mohm_50c_excluding_vias': round(squares * SHEET_MOHM_PER_SQUARE, 2),
                'routed_mm': round(first[1] + second[1] + third[1], 2),
            }
        result[leg] = contacts_result

    via_mohm = via_mohm_20um_plating()
    balanced = {}
    high_frequency_sensitivity = {}
    for channel, pos, neg in [('left', 'LP', 'LN'), ('right', 'RP', 'RN')]:
        positive = [v['trace_mohm_50c_excluding_vias'] for k, v in result[pos].items()
                    if k.startswith('J701.')]
        negative = [v['trace_mohm_50c_excluding_vias'] for k, v in result[neg].items()
                    if k.startswith('J701.')]
        via_total = (via_count[pos] + via_count[neg]) * via_mohm
        # R-15 v1.1: 0.383 ohm at 1 kHz includes an assumed 0.020 ohm
        # pairwise trace term. Replace only that term with routed copper.
        nontrace = 0.383 - 0.020
        best = nontrace + (min(positive) + min(negative) + via_total) / 1000
        worst = nontrace + (max(positive) + max(negative) + via_total) / 1000
        balanced[channel] = {
            'best_contact_path_ohm': round(best, 4),
            'worst_contact_path_ohm': round(worst, 4),
            'worst_planning_margin_to_0p5_mohm': round((0.5 - worst) * 1000, 1),
        }
        # v1.1 analog model: OPA1622 closed-loop output impedance rises from
        # 0.33 mOhm/leg at 1 kHz to 6.7 mOhm/leg at 20 kHz. This is a
        # sensitivity, not a measured board or a frequency-qualified spec.
        worst_20khz = worst + 2 * (6.7 - 0.33) / 1000
        high_frequency_sensitivity[channel] = {
            'worst_contact_path_ohm': round(worst_20khz, 4),
            'margin_to_0p5_mohm_if_same_limit': round((0.5 - worst_20khz) * 1000, 1),
        }
    se = {}
    for leg in ('LP', 'RP'):
        trace = result[leg][f'J702.{4 if leg == "LP" else 3}'][
            'trace_mohm_50c_excluding_vias']
        # The sleeve return is unrouted; this is only a signal-side bound.
        se[leg] = round(0.251 - 0.020 + (trace + via_count[leg] * via_mohm) / 1000, 4)
    return {
        'board': board_path.name,
        'method': 'least-resistance connected copper path; pads and vias have zero cost in the trace term',
        'sheet_mohm_per_square_35um_50c': SHEET_MOHM_PER_SQUARE,
        'trace_paths': result,
        'signal_vias_per_leg': via_count,
        'illustrative_via_mohm_each_20um_wall_1p6mm_50c': round(via_mohm, 2),
        'balanced_4p4_planning_estimate_1khz': balanced,
        'balanced_4p4_model_sensitivity_20khz': high_frequency_sensitivity,
        'trs_3p5_signal_only_lower_bound_ohm': se,
        'release': 'HOLD: contact maxima, sleeve return, L3/L4 return, AC output impedance and loaded measurements',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(audit(args.board), indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(result)
    print(result, end='')


if __name__ == '__main__':
    main()
