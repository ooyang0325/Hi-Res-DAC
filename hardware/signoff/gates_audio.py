"""Audio-specific gates: output path, feedback loops and port protection.

These gates use the solved copper network, so the resistances quoted are the
drawn geometry's, not a straight-line estimate.
"""

from __future__ import annotations

import math
from collections import defaultdict

from . import design_intent as di
from . import geom
from .framework import gate
from .netgraph import OPEN_OHM, build_for_net
from .rules import AUDIO

OTT_SRC = "H. Ott, Electromagnetic Compatibility Engineering, ch. 11-12"
ESD_SRC = "IEC 61000-4-2 (ESD immunity) with TVS stub-inductance let-through"
SELF_SRC = "D. Self, Audio Power Amplifier Design (output impedance / damping)"


def _pad_lookup(model):
    out = defaultdict(list)
    for p in model["pads"]:
        out[p["net"]].append(p)
    return out


def _terminal_resistance(model, stack, net, ref_a, ref_b):
    """Solved copper resistance between two components on one net."""
    nn = build_for_net(net, model, stack, include_zones=True)
    if nn.node_count == 0:
        return None
    src = [n for k, nodes in nn.pad_nodes.items()
           if k.split(".")[0] == ref_a for n in nodes]
    dst = [n for k, nodes in nn.pad_nodes.items()
           if k.split(".")[0] == ref_b for n in nodes]
    if not src or not dst:
        return None
    reff = nn.effective_resistances(src, dst)
    vals = [v for v in reff.values() if v <= OPEN_OHM]
    return min(vals) if vals else None


def series_path_resistance(model, stack, net):
    """Copper resistance of the load-current path of one output net.

    Measured between the parts that carry headphone current
    (``design_intent.OUTPUT_SERIES_TERMINALS``); for a net that serves two
    jacks, the worse path.  Sense taps hanging off the net are excluded.
    """
    vals = [_terminal_resistance(model, stack, net, a, b)
            for a, b in di.OUTPUT_SERIES_TERMINALS.get(net, [])]
    if not vals or any(v is None for v in vals):
        return None
    return max(vals)


@gate(
    "G30",
    "Headphone output path resistance and channel matching",
    "Series copper resistance in the balanced headphone output stays small "
    "against the load so the damping factor is preserved, and the two channels "
    "match closely enough not to shift the stereo image.",
    sources=[SELF_SRC],
)
def g30_output_path(model, ctx, r):
    stack = ctx["stack"]
    load = AUDIO["headphone_load_ohm"]
    budget = AUDIO["max_output_trace_resistance_ohm"]
    mismatch_budget = AUDIO["max_channel_resistance_mismatch_ohm"]
    r.metrics["load_ohm"] = load
    r.metrics["trace_resistance_budget_ohm"] = budget
    r.metrics["channel_mismatch_budget_ohm"] = mismatch_budget
    r.assume(
        "Only drawn copper is included: connector contact, relay contact and "
        "amplifier output impedance are additional to these numbers."
    )
    r.assume(
        "Each net is measured along its load-current path between the parts in "
        "design_intent.OUTPUT_SERIES_TERMINALS; the high-value sense-divider "
        "taps on LEG_xx carry no headphone current and are excluded."
    )

    names = set(model["nets"].values())
    pads = _pad_lookup(model)
    resistances = {}

    for net in sorted(di.OUTPUT_PATH_NETS):
        if net not in names:
            continue
        nn = build_for_net(net, model, stack, include_zones=True)
        if nn.node_count == 0 or not nn.pad_nodes:
            continue
        res = series_path_resistance(model, stack, net)
        if res is None:
            r.fail("OUTPUT_NET_OPEN",
                   f"{net}: no DC path between its load-current terminals.", net=net)
            continue
        resistances[net] = res

    r.metrics["output_net_resistance_ohm"] = {
        k: round(v, 5) for k, v in sorted(resistances.items())
    }

    over = {k: v for k, v in resistances.items() if v > budget}
    if over:
        r.warn("OUTPUT_RESISTANCE",
               f"{len(over)} output net(s) exceed the {budget} ohm copper "
               f"budget; damping factor into {load} ohm is reduced.",
               count=len(over),
               worst={k: round(v, 5) for k, v in
                      sorted(over.items(), key=lambda kv: -kv[1])[:8]})

    worst_df = None
    for net, res in resistances.items():
        df = load / res if res > 0 else float("inf")
        if worst_df is None or df < worst_df[1]:
            worst_df = (net, df)
    if worst_df and math.isfinite(worst_df[1]):
        r.metrics["worst_damping_factor"] = round(worst_df[1], 1)
        r.metrics["worst_damping_net"] = worst_df[0]
        if worst_df[1] < AUDIO["min_damping_factor"]:
            r.warn("DAMPING_FACTOR",
                   f"{worst_df[0]} alone limits the damping factor to "
                   f"{worst_df[1]:.0f}, below the {AUDIO['min_damping_factor']:.0f} "
                   f"target.",
                   net=worst_df[0], damping_factor=round(worst_df[1], 1))

    # -- channel matching -------------------------------------------------
    mismatches = {}
    for a, b in di.OUTPUT_CHANNEL_PAIRS:
        if a in resistances and b in resistances:
            delta = abs(resistances[a] - resistances[b])
            mismatches[f"{a}/{b}"] = round(delta, 5)
    r.metrics["channel_mismatch_ohm"] = mismatches
    bad = {k: v for k, v in mismatches.items() if v > mismatch_budget}
    if bad:
        r.warn("CHANNEL_MISMATCH",
               f"{len(bad)} channel pair(s) differ by more than "
               f"{mismatch_budget} ohm of copper.",
               count=len(bad), worst=bad)


@gate(
    "G31",
    "I/V and feedback loop geometry",
    "The inverting summing node and its feedback loop are kept physically "
    "small, since that node is the highest-impedance point in the signal path.",
    sources=[OTT_SRC, "TI SBOA015 / OPA.. inverting-input layout guidance"],
)
def g31_feedback_loops(model, ctx, r):
    max_area = AUDIO["iv_feedback_loop_area_max_mm2"]
    max_trace = AUDIO["iv_feedback_trace_max_mm"]
    max_summing = AUDIO["summing_node_max_trace_mm"]
    r.metrics["feedback_loop_area_budget_mm2"] = max_area
    r.metrics["feedback_trace_budget_mm"] = max_trace
    r.metrics["summing_node_budget_mm"] = max_summing

    names = set(model["nets"].values())
    tracks_by_net = defaultdict(list)
    for t in model["tracks"]:
        tracks_by_net[t["net"]].append(t)
    pads = _pad_lookup(model)

    long_fb, big_loop, lengths, areas = [], [], {}, {}
    for net in sorted(di.FEEDBACK_NETS | di.IV_OUTPUT_NETS):
        if net not in names:
            continue
        segs = tracks_by_net.get(net, [])
        if not segs:
            continue
        length = sum(t.get("length_mm") or geom.dist(t["start_mm"], t["end_mm"])
                     for t in segs)
        lengths[net] = round(length, 2)

        # Loop area: the convex hull of the net's copper and its pads is an
        # upper bound on the area the feedback loop can enclose.
        pts = []
        for t in segs:
            pts.append(tuple(t["start_mm"]))
            pts.append(tuple(t["end_mm"]))
        for p in pads.get(net, []):
            pts.append(tuple(p["pos_mm"]))
        hull = geom.convex_hull(pts)
        area = abs(geom.polygon_area(hull)) if len(hull) >= 3 else 0.0
        areas[net] = round(area, 2)

        limit = max_summing if net in di.FEEDBACK_NETS else max_trace
        if length > limit:
            long_fb.append({"net": net, "length_mm": round(length, 2),
                            "limit_mm": limit})
        if area > max_area:
            big_loop.append({"net": net, "area_mm2": round(area, 2)})

    r.metrics["feedback_net_lengths_mm"] = dict(
        sorted(lengths.items(), key=lambda kv: -kv[1])[:15])
    r.metrics["feedback_loop_areas_mm2"] = dict(
        sorted(areas.items(), key=lambda kv: -kv[1])[:15])

    if long_fb:
        r.warn("FEEDBACK_TRACE_LONG",
               f"{len(long_fb)} feedback/summing net(s) are longer than their "
               f"budget, raising noise pickup at a high-impedance node.",
               count=len(long_fb),
               worst=sorted(long_fb, key=lambda d: -d["length_mm"])[:10])
    if big_loop:
        r.warn("FEEDBACK_LOOP_AREA",
               f"{len(big_loop)} feedback net(s) enclose more than "
               f"{max_area} mm^2, so the loop is a larger magnetic antenna.",
               count=len(big_loop),
               worst=sorted(big_loop, key=lambda d: -d["area_mm2"])[:10])


@gate(
    "G32",
    "External port ESD protection",
    "Every externally exposed pin reaches its protection device through a short "
    "stub, so the let-through voltage from stub inductance stays bounded.",
    sources=[ESD_SRC],
)
def g32_esd_ports(model, ctx, r):
    stack = ctx["stack"]
    max_stub = AUDIO["esd_max_stub_mm"]
    di_dt = AUDIO["esd_di_dt_a_per_s"]
    r.metrics["esd_stub_budget_mm"] = max_stub
    r.assume(
        "The stub is the shortest copper path from the connector pin to the "
        "nearest clamp, which is what the strike current actually traverses; "
        "copper beyond the clamp is downstream and is not counted."
    )

    names = set(model["nets"].values())
    pads = _pad_lookup(model)
    values = {f["ref"]: (f.get("value") or "") for f in model["footprints"]}

    unprotected, long_stub, detail = [], [], {}
    for net in sorted(di.EXTERNAL_PORT_NETS):
        if net not in names:
            continue
        refs = sorted({p["ref"] for p in pads.get(net, [])})
        connectors = [x for x in refs if di.ref_prefix(x) == "J"]
        protectors = [x for x in refs
                      if di.is_protection_device(x, values.get(x, ""))]

        bonded = _ground_bond(net, model, values)
        entry = {"parts": refs[:12], "protection": protectors,
                 "connector": connectors}
        if bonded:
            entry["ground_bond"] = bonded
        detail[net] = entry
        if not protectors and not bonded:
            unprotected.append(net)
            continue
        if not protectors:
            # A shell/shield pin bonded straight to GND already has its
            # discharge path; there is no clamp stub to measure.
            continue

        stub = _stub_path_mm(net, model, stack, connectors, protectors)
        if stub is None:
            continue
        entry["stub_mm"] = round(stub, 2)
        if stub > max_stub:
            let_through = di_dt * _stub_inductance_h(stub)
            long_stub.append({"net": net, "stub_mm": round(stub, 2),
                              "let_through_v": round(let_through, 1),
                              "clamp": protectors})

    r.metrics["ports"] = detail
    if unprotected:
        r.warn("PORT_UNPROTECTED",
               f"{len(unprotected)} external port net(s) have no identifiable "
               f"protection device on the net.",
               count=len(unprotected), nets=unprotected)
    if long_stub:
        r.warn("ESD_STUB_LONG",
               f"{len(long_stub)} port net(s) reach their clamp through more "
               f"than {max_stub} mm of copper, so stub inductance raises the "
               f"ESD let-through.",
               count=len(long_stub),
               worst=sorted(long_stub, key=lambda d: -d["stub_mm"])[:10])


def _ground_bond(net, model, values):
    """Parts that tie this port net straight to GND (shield termination).

    A connector shell bonded to GND through a 0 ohm link, a ferrite or a
    capacitor already has a defined discharge path, so it does not need a
    separate clamp.
    """
    by_ref = defaultdict(dict)
    for p in model["pads"]:
        by_ref[p["ref"]][p["pad"]] = p["net"]

    bonds = []
    for ref, padmap in by_ref.items():
        nets = set(padmap.values())
        if net not in nets or "GND" not in nets or len(nets) != 2:
            continue
        pre = di.ref_prefix(ref)
        val = values.get(ref, "")
        if pre in {"FB", "L", "C"}:
            bonds.append(ref)
        elif pre == "R":
            ohms = di.parse_resistance(val)
            if ohms is not None and ohms <= 1.0:
                bonds.append(ref)
    return sorted(bonds)


def _stub_path_mm(net, model, stack, connectors, protectors):
    """Shortest copper distance from a connector pin to its nearest clamp."""
    if not connectors or not protectors:
        return None
    nn = build_for_net(net, model, stack, include_zones=True)
    if nn.node_count == 0:
        return None
    src = [n for k, nodes in nn.pad_nodes.items()
           if k.split(".")[0] in set(connectors) for n in nodes]
    dst = [n for k, nodes in nn.pad_nodes.items()
           if k.split(".")[0] in set(protectors) for n in nodes]
    return nn.shortest_copper_path_mm(src, dst)


def _stub_inductance_h(length_mm: float) -> float:
    """Rule-of-thumb 1 nH per mm of routed stub."""
    return length_mm * 1e-9
