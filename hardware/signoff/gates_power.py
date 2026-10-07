"""Power-integrity gates.

G10  Conductor ampacity (IPC-2221B).
G11  Via ampacity and parallelism.
G12  DC IR drop, solved on the real copper network.
G13  Decoupling placement and mounted self-resonance.
"""

from __future__ import annotations

import math
from collections import defaultdict

from . import design_intent as di
from . import geom
from .framework import gate
from .netgraph import OPEN_OHM, LayerStack, build_for_net
from .rules import (
    AUDIO,
    INNER_CU_OZ,
    IR_DROP_BUDGET_PCT,
    OUTER_CU_OZ,
    OZ_TO_MM,
    DESIGN_DELTA_T_K,
    ipc2221_current_a,
    ipc2221_width_mm,
    via_current_a,
    via_pair_inductance_h,
    pdn_target_impedance_ohm,
)

IPC2221_SRC = "IPC-2221B eq. 6-4, I = k*dT^0.44*A^0.725 (k=0.048 external, 0.024 internal)"
IPC2152_SRC = "IPC-2152 (current capacity; 2221 retained as the conservative floor)"
PAUL_SRC = "C. R. Paul, Inductance: Loop and Partial, Wiley 2010, ch. 5"


def _stack(model):
    names = [l["name"] for l in model["copper_layers"]]
    defined = model["stackup"].get("defined") or model.get("project", {}).get("stackup")
    return LayerStack(
        names,
        board_thickness_mm=model["stackup"]["board_thickness_mm"],
        outer_oz=OUTER_CU_OZ,
        inner_oz=INNER_CU_OZ,
        assumed=not defined,
    )



def _minor(spec):
    return spec.get("minor_load_a", 0.001)


def solved_item_currents(model, stack, net, spec):
    """[(track/via, A)] with each declared load drawn at its own pads.

    Returns None when the rail declares no loads, so the gate falls back to the
    full budget through every conductor.
    """
    loads, sources = spec.get("loads"), spec.get("source")
    if not loads or not sources:
        return None
    nn = build_for_net(net, model, stack, include_zones=True)
    src = [n for k, nodes in nn.pad_nodes.items()
           if k.split(".")[0] in sources for n in nodes]
    if not src or nn.node_count > 6000:
        return None
    pads_by_ref = defaultdict(list)
    for k, nodes in nn.pad_nodes.items():
        pads_by_ref[k.split(".")[0]].append(nodes)
    draw = defaultdict(float)
    for ref, groups in pads_by_ref.items():
        if ref in sources:
            continue
        if ref in loads:
            amps = loads[ref]
        elif di.ref_prefix(ref) in ("C", "TP", "FID", "MH"):
            continue
        else:
            amps = _minor(spec)
        for nodes in groups:
            draw[nodes[0]] += amps / len(groups)
    return nn.item_currents(src, draw)

@gate(
    "G10",
    "Conductor ampacity (IPC-2221B)",
    f"Every power conductor is wide enough to carry its budgeted DC current at a "
    f"{DESIGN_DELTA_T_K:.0f} K rise, on the layer it is drawn on.",
    sources=[IPC2221_SRC, IPC2152_SRC],
)
def g10_ampacity(model, ctx, r):
    stack = ctx["stack"]
    r.assume(
        f"Copper weights assumed {OUTER_CU_OZ} oz outer / {INNER_CU_OZ} oz inner "
        f"(fabricator default); no stackup is defined on the board."
        if stack.assumed else
        f"Copper weights taken from the board stackup."
    )
    r.assume(
        "DC current budgets are the declared values in design_intent.RAILS and are "
        "upper bounds, not measurements. Where a rail declares its loads, each "
        "conductor is held to the current the solved copper network puts through "
        "it with every load at its maximum; otherwise to the full rail budget."
    )
    r.metrics["delta_t_k"] = DESIGN_DELTA_T_K
    r.metrics["layer_copper_mm"] = {k: round(v, 5) for k, v in stack.thickness_mm.items()}

    by_net = defaultdict(list)
    for t in model["tracks"]:
        by_net[t["net"]].append(t)

    results = {}
    for net, spec in di.RAILS.items():
        if net == "GND":
            continue
        segs = by_net.get(net)
        if not segs:
            continue
        current = spec["current_a"]
        solved = solved_item_currents(model, stack, net, spec)
        if solved is not None:
            per_track = {id(t): amps for t, amps in solved if "layer" in t}
        worst = None
        for t in segs:
            internal = not stack.is_outer(t["layer"])
            th = stack.thickness_mm.get(t["layer"])
            if not th:
                continue
            if solved is not None:
                current = max(per_track.get(id(t), 0.0), 1e-6)
            cap = ipc2221_current_a(t["width_mm"], th, internal=internal)
            need = ipc2221_width_mm(current, th, internal=internal)
            margin = cap / current if current > 0 else float("inf")
            if worst is None or margin < worst["margin"]:
                worst = {
                    "margin": margin,
                    "layer": t["layer"],
                    "width_mm": t["width_mm"],
                    "required_width_mm": round(need, 4),
                    "capacity_a": round(cap, 4),
                    "length_mm": round(t.get("length_mm", 0.0), 3),
                    "at": t["start_mm"],
                    "current_a": round(current, 4),
                    "solved": solved is not None,
                }
        if worst is None:
            continue
        # The capacity scales with copper thickness as A^0.725, so when the
        # weight is assumed rather than declared the verdict can hinge on it.
        # Report the capacity at double the assumed weight so the reader can
        # see immediately whether the finding survives a 1 oz inner layer.
        if stack.assumed and not stack.is_outer(worst["layer"]):
            worst["capacity_at_double_copper_a"] = round(
                worst["capacity_a"] * (2 ** 0.725), 4)

        current = worst["current_a"]
        results[net] = {
            "budget_a": spec["current_a"],
            "conductor_current_a": current,
            "current_basis": "solved per segment" if worst["solved"] else "full rail budget",
            "narrowest_mm": worst["width_mm"],
            "layer": worst["layer"],
            "required_mm": worst["required_width_mm"],
            "capacity_a": worst["capacity_a"],
            "margin_x": round(worst["margin"], 3),
            "capacity_at_double_copper_a": worst.get("capacity_at_double_copper_a"),
        }
        if worst["margin"] < 1.0:
            doubled = worst.get("capacity_at_double_copper_a")
            caveat = ""
            if doubled:
                caveat = (f" At 1 oz inner copper the same conductor would "
                          f"carry {doubled} A, which would "
                          f"{'clear' if doubled >= current else 'still miss'} "
                          f"the budget, so confirm the stackup before acting.")
            r.fail(
                "AMPACITY",
                f"{net}: narrowest conductor {worst['width_mm']} mm on {worst['layer']} "
                f"carries {worst['capacity_a']} A but must carry {current} A "
                f"({results[net]['current_basis']}) "
                f"(needs {worst['required_width_mm']} mm).{caveat}",
                net=net, **worst,
            )
        elif worst["margin"] < 1.5:
            r.warn(
                "AMPACITY_MARGIN",
                f"{net}: narrowest conductor has only {worst['margin']:.2f}x margin "
                f"over the {current} A it carries ({results[net]['current_basis']}).",
                net=net, **worst,
            )
    r.metrics["rails"] = results


@gate(
    "G11",
    "Via ampacity",
    "Each rail has enough plated barrel area at every layer transition to carry "
    "its budgeted current.",
    sources=[IPC2221_SRC, "JLCPCB: 18 um average through-hole plating"],
)
def g11_via_ampacity(model, ctx, r):
    stack = ctx["stack"]
    r.assume("Barrel plating assumed 18 um (fabricator stated average).")
    r.assume("A via barrel is evaluated with the IPC-2221B internal constant "
             "because it is enclosed by laminate.")

    per_via = {}
    for drill in sorted({round(v["drill_mm"], 3) for v in model["vias"]}):
        per_via[str(drill)] = round(via_current_a(drill), 4)
    r.metrics["single_via_capacity_a"] = per_via

    # Group vias of a rail by location cluster: vias that sit within 3 mm of
    # each other are carrying current in parallel at the same transition.
    by_net = defaultdict(list)
    for v in model["vias"]:
        by_net[v["net"]].append(v)

    summary = {}
    for net, spec in di.RAILS.items():
        if net == "GND":
            continue
        vias = by_net.get(net)
        if not vias:
            continue
        current = spec["current_a"]
        solved = solved_item_currents(model, stack, net, spec)
        if solved is not None:
            # Each via against the current the solved network puts through it;
            # parallel vias share their transition automatically.
            per_via = {id(v): amps for v, amps in solved if "drill_mm" in v}
            worst = None
            for v in vias:
                amps = max(per_via.get(id(v), 0.0), 1e-6)
                cap = via_current_a(v["drill_mm"])
                if worst is None or cap / amps < worst[0]:
                    worst = (cap / amps, cap, amps, v)
            margin, cap, amps, v = worst
            summary[net] = {"budget_a": current, "via_current_a": round(amps, 4),
                            "current_basis": "solved per via",
                            "weakest_via_capacity_a": round(cap, 4),
                            "margin_x": round(margin, 2), "at": v["pos_mm"]}
            detail = dict(capacity_a=cap, via_count=1, at=v["pos_mm"],
                          drills_mm=[round(v["drill_mm"], 3)], solved_current_a=round(amps, 4))
            if margin < 1.0:
                r.fail("VIA_AMPACITY", f"{net}: a {v['drill_mm']} mm via at {v['pos_mm']} carries "
                       f"{amps:.3f} A (solved) against a {cap:.3f} A capacity.", net=net, **detail)
            elif margin < 1.5:
                r.warn("VIA_AMPACITY_MARGIN", f"{net}: weakest via has {margin:.2f}x margin "
                       f"({amps:.3f} A solved).", net=net, **detail)
            continue
        uf = geom.UnionFind()
        idx = geom.GridIndex(4.0)
        for i, v in enumerate(vias):
            x, y = v["pos_mm"]
            idx.insert((x, y, x, y), (i, x, y))
            uf.find(i)
        for i, v in enumerate(vias):
            x, y = v["pos_mm"]
            for j, ox, oy in idx.query_point((x, y), 3.0):
                if j != i and math.hypot(ox - x, oy - y) <= 3.0:
                    uf.union(i, j)
        clusters = defaultdict(list)
        for i in range(len(vias)):
            clusters[uf.find(i)].append(vias[i])

        worst = None
        for members in clusters.values():
            cap = sum(via_current_a(v["drill_mm"]) for v in members)
            if worst is None or cap < worst["capacity_a"]:
                worst = {
                    "capacity_a": cap,
                    "via_count": len(members),
                    "at": members[0]["pos_mm"],
                    "drills_mm": sorted({round(v["drill_mm"], 3) for v in members}),
                }
        if worst is None:
            continue
        margin = worst["capacity_a"] / current if current else float("inf")
        summary[net] = {
            "budget_a": current,
            "weakest_transition_a": round(worst["capacity_a"], 4),
            "via_count": worst["via_count"],
            "margin_x": round(margin, 2),
            "at": worst["at"],
        }
        if margin < 1.0:
            r.fail("VIA_AMPACITY",
                   f"{net}: a layer transition made of {worst['via_count']} via(s) "
                   f"carries {worst['capacity_a']:.3f} A against a {current} A budget.",
                   net=net, **worst)
        elif margin < 1.5:
            r.warn("VIA_AMPACITY_MARGIN",
                   f"{net}: weakest via transition has {margin:.2f}x margin "
                   f"({worst['via_count']} via(s), {current} A budget).",
                   net=net, **worst)
    r.metrics["rails"] = summary


@gate(
    "G12",
    "DC IR drop (solved)",
    "Static voltage drop from each rail's source to its loads stays inside the "
    "rail budget, solved as a nodal network on the actual copper.",
    sources=["Nodal analysis of the extracted copper graph",
             "IPC-2152 (conductor resistance basis)"],
)
def g12_ir_drop(model, ctx, r):
    stack = ctx["stack"]
    r.assume(
        "Return-path (GND) drop is excluded: GND is a filled plane on four layers "
        "and its spreading resistance is not extracted here."
    )
    r.assume(
        "The rail current budget is distributed equally across the rail's load "
        "pads; R_eff values reported per pad are independent of that split."
    )
    r.assume("Copper resistivity 1.724e-8 ohm*m at 20 C.")

    pads_by_net = defaultdict(list)
    for p in model["pads"]:
        pads_by_net[p["net"]].append(p)

    rails = {}
    for net, spec in di.RAILS.items():
        if net == "GND":
            continue
        pads = pads_by_net.get(net, [])
        if len(pads) < 2:
            continue
        nn = build_for_net(net, model, stack, include_zones=True)
        if nn.node_count == 0 or nn.node_count > 2500:
            r.info("NET_SKIPPED",
                   f"{net}: {nn.node_count} nodes, outside the dense-solve window.",
                   net=net, nodes=nn.node_count)
            continue

        source_ref = ctx["rail_sources"].get(net)
        source_nodes = []
        if source_ref:
            for key, nodes in nn.pad_nodes.items():
                if key.split(".")[0] == source_ref:
                    source_nodes.extend(nodes)
        if not source_nodes:
            # Fall back to the pad with the most copper attached to it.
            degree = defaultdict(int)
            for i, j, _ in nn._edges:
                degree[i] += 1
                degree[j] += 1
            best, best_d = None, -1
            for key, nodes in nn.pad_nodes.items():
                d = sum(degree.get(n, 0) for n in nodes)
                if d > best_d:
                    best, best_d = key, d
            if best is None:
                continue
            source_ref = best
            source_nodes = nn.pad_nodes[best]

        load_keys = [k for k in nn.pad_nodes
                     if not k.startswith(str(source_ref).split(".")[0] + ".")]
        if not load_keys:
            continue
        probe = []
        for k in load_keys:
            probe.extend(nn.pad_nodes[k])
        reff = nn.effective_resistances(source_nodes, probe)
        if not reff:
            continue

        per_pad = {}
        for k in load_keys:
            vals = [reff[n] for n in nn.pad_nodes[k] if n in reff]
            if vals:
                per_pad[k] = min(vals)
        if not per_pad:
            continue

        budget_pct = IR_DROP_BUDGET_PCT.get(spec["kind"], IR_DROP_BUDGET_PCT["default"])
        volts = abs(spec["volts"]) or 1.0
        budget_v = volts * budget_pct / 100.0

        # An unreachable pad has no DC path at all.  Its "resistance" is a
        # solver sentinel, not a measurement, so it must never be turned into
        # a voltage drop -- that would report a meaningless number.  Opens are
        # reported on their own, and the IR-drop statistics are computed from
        # the pads that are actually connected.
        unreachable = sorted(k for k, v in per_pad.items() if v > OPEN_OHM)
        connected = {k: v for k, v in per_pad.items() if v <= OPEN_OHM}

        if unreachable:
            r.fail("RAIL_OPEN",
                   f"{net}: {len(unreachable)} of {len(per_pad)} load pad(s) have no "
                   f"DC path to the source {source_ref}; the rail is not fully routed.",
                   net=net, count=len(unreachable), total=len(per_pad),
                   source=source_ref, sample=unreachable[:12])

        if not connected:
            rails[net] = {
                "source": source_ref,
                "load_pads": len(per_pad),
                "connected_pads": 0,
                "open_pads": len(unreachable),
                "nodes": nn.node_count,
                "note": "no connected load pad; IR drop not evaluated",
            }
            continue

        share = spec["current_a"] / max(len(connected), 1)
        drops = {k: v * share for k, v in connected.items()}
        worst_key = max(drops, key=drops.get)
        worst_drop = drops[worst_key]
        worst_r = connected[worst_key]

        rails[net] = {
            "source": source_ref,
            "load_pads": len(per_pad),
            "connected_pads": len(connected),
            "open_pads": len(unreachable),
            "worst_pad": worst_key,
            "worst_r_eff_ohm": round(worst_r, 5),
            "worst_drop_mv": round(worst_drop * 1e3, 3),
            "budget_mv": round(budget_v * 1e3, 2),
            "budget_pct": budget_pct,
            "nodes": nn.node_count,
        }
        if worst_drop > budget_v:
            r.fail("IR_DROP",
                   f"{net}: {worst_drop*1e3:.1f} mV drop to {worst_key} exceeds the "
                   f"{budget_v*1e3:.0f} mV ({budget_pct}%) budget.",
                   net=net, **rails[net])
        elif worst_drop > budget_v * 0.7:
            r.warn("IR_DROP_MARGIN",
                   f"{net}: {worst_drop*1e3:.1f} mV drop is within 30% of the "
                   f"{budget_v*1e3:.0f} mV budget.",
                   net=net, **rails[net])
    r.metrics["rails"] = rails


@gate(
    "G13",
    "Decoupling placement and mounted resonance",
    "Every device supply pin has a high-frequency bypass capacitor close enough "
    "that the mounted loop inductance keeps its self-resonance above the "
    "frequencies the device actually needs decoupled.",
    sources=[PAUL_SRC, "Ott, Electromagnetic Compatibility Engineering, ch. 11"],
)
def g13_decoupling(model, ctx, r):
    stack = ctx["stack"]
    r.assume("Capacitor values are parsed from the footprint Value field.")
    r.assume("Mounting inductance counts the via pair under the capacitor plus the "
             "pad-to-via run; the capacitor's own ESL is taken as 0.6 nH for 0402 "
             "and 0.9 nH for 0603, typical MLCC values.")

    caps = {}
    for f in model["footprints"]:
        if not di.is_capacitor(f["ref"]):
            continue
        val = di.parse_capacitance(f["value"])
        if val:
            caps[f["ref"]] = {"farads": val, "pos": f["pos_mm"],
                              "library": f["library"], "value": f["value"]}
    r.metrics["capacitors_parsed"] = len(caps)

    pads_by_ref = defaultdict(list)
    for p in model["pads"]:
        pads_by_ref[p["ref"]].append(p)

    # Index capacitor pads by net so a supply pin can find its bypass.
    # A bypass is not only a cap to GND: a dual-supply analogue stage is
    # commonly decoupled rail to rail (V+ straight to V- across the op-amp),
    # and treating those as "not a bypass" wrongly reports the stage as
    # undecoupled.  Either terminal of such a part bypasses its own rail.
    cap_pads_by_net = defaultdict(list)
    for ref, info in caps.items():
        nets = {p["net"] for p in pads_by_ref.get(ref, [])}
        if len(nets) != 2:
            continue
        is_to_gnd = "GND" in nets
        is_rail_to_rail = all(n in di.RAILS for n in nets)
        if not (is_to_gnd or is_rail_to_rail):
            continue
        for p in pads_by_ref.get(ref, []):
            if p["net"] and p["net"] != "GND":
                cap_pads_by_net[p["net"]].append((ref, p, info))

    via_by_net = defaultdict(list)
    for v in model["vias"]:
        via_by_net[v["net"]].append(v)

    esl_for = {"0402": 0.6e-9, "0603": 0.9e-9, "0805": 1.2e-9, "1206": 1.6e-9}

    def cap_esl(library):
        for k, v in esl_for.items():
            if k in (library or ""):
                return v
        return 1.0e-9

    checked = []
    for p in model["pads"]:
        net = p["net"]
        spec = di.RAILS.get(net)
        if not spec or net == "GND" or not spec.get("supply", True):
            continue
        if not di.is_ic(p["ref"]) or p["ref"] in spec.get("source", ()):
            continue                          # a regulator's own output pin is not a load
        candidates = cap_pads_by_net.get(net, [])
        if not candidates:
            r.fail("NO_BYPASS",
                   f"{p['ref']}.{p['pad']} ({net}) has no bypass capacitor on its rail.",
                   ref=p["ref"], pad=p["pad"], net=net)
            continue
        best = min(candidates, key=lambda c: geom.dist(p["pos_mm"], c[1]["pos_mm"]))
        ref, cpad, info = best
        d = geom.dist(p["pos_mm"], cpad["pos_mm"])

        # Mounting inductance: via pair under the capacitor, if present.
        gnd_pad = next((q for q in pads_by_ref.get(ref, []) if q["net"] == "GND"), None)
        pitch = geom.dist(cpad["pos_mm"], gnd_pad["pos_mm"]) if gnd_pad else 1.0
        near_vias = [v for v in via_by_net.get(net, [])
                     if geom.dist(v["pos_mm"], cpad["pos_mm"]) < 1.5]
        near_gnd = [v for v in via_by_net.get("GND", [])
                    if gnd_pad and geom.dist(v["pos_mm"], gnd_pad["pos_mm"]) < 1.5]
        if near_vias and near_gnd:
            drill = min(v["drill_mm"] for v in near_vias)
            # Barrel length to the nearest plane layer.
            h = stack.separation_mm(stack.names[0], stack.names[1])
            l_mount = via_pair_inductance_h(max(pitch, drill * 1.1), drill, max(h, 0.05))
            has_vias = True
        else:
            l_mount = via_pair_inductance_h(max(pitch, 0.3), 0.3,
                                            stack.board_thickness_mm)
            has_vias = False
        l_total = l_mount + cap_esl(info["library"])
        srf = 1.0 / (2 * math.pi * math.sqrt(max(l_total * info["farads"], 1e-30)))

        entry = {
            "pin": f"{p['ref']}.{p['pad']}",
            "net": net,
            "cap": ref,
            "cap_value": info["value"],
            "distance_mm": round(d, 3),
            "mount_inductance_nh": round(l_mount * 1e9, 3),
            "mounted_srf_mhz": round(srf / 1e6, 2),
            "local_vias": has_vias,
        }
        checked.append(entry)

        limit = AUDIO["hf_bypass_max_pad_distance_mm"]
        if info["farads"] <= 1e-6 and d > limit:
            r.warn("BYPASS_DISTANCE",
                   f"{p['ref']}.{p['pad']} ({net}): nearest bypass {ref} "
                   f"({info['value']}) is {d:.2f} mm away, beyond the {limit} mm "
                   f"high-frequency guideline.",
                   **entry)
        if l_mount * 1e9 > AUDIO["hf_bypass_max_mount_inductance_nh"]:
            r.warn("BYPASS_INDUCTANCE",
                   f"{p['ref']}.{p['pad']} ({net}): bypass {ref} mounts with "
                   f"{l_mount*1e9:.2f} nH, above the "
                   f"{AUDIO['hf_bypass_max_mount_inductance_nh']} nH guideline; "
                   f"mounted self-resonance falls to {srf/1e6:.1f} MHz.",
                   **entry)

    r.metrics["pins_checked"] = len(checked)
    if checked:
        worst = sorted(checked, key=lambda e: -e["distance_mm"])[:15]
        r.metrics["worst_by_distance"] = worst
        r.metrics["median_distance_mm"] = round(
            sorted(e["distance_mm"] for e in checked)[len(checked) // 2], 3)
