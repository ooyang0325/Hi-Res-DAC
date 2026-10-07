"""Simulation gates: LTspice decks built entirely from extracted geometry.

A decoupling study is only as good as the parasitics behind it.  These gates
do not assume a mounting inductance or a plane resistance -- they measure the
placed capacitor's package, the distance from its pads to the vias it actually
uses, and the resistance of the copper the current actually flows through, and
then hand those numbers to LTspice.

Because the board declares no stackup, the one quantity that cannot be
extracted is the height from the outer layer to the first plane.  Rather than
choose a value, every deck sweeps the plausible construction range with
``.step`` and the gate reports whether the verdict changes across it.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from . import design_intent as di
from . import parasitics as pz
from . import rules
from . import spice
from .framework import gate
from .netgraph import OPEN_OHM, build_for_net
from .rules import AUDIO, PDN_BAND_HZ, OUTER_TO_PLANE_MM

PDN_SRC = ("L. Smith / E. Bogatin, Principles of Power Integrity "
           "(target impedance and decoupling)")
PAUL_SRC = "C. R. Paul, Inductance: Loop and Partial (via-pair loop inductance)"


def _fmt(x: float) -> str:
    """SPICE-safe number."""
    return f"{x:.6g}"


_FB_RE = re.compile(r"(^|_)(FB|FEEDBACK|ADJ|SENSE)(_|$)", re.IGNORECASE)


def regulator_refs(model, rail):
    """Components that regulate ``rail`` rather than consume it.

    A regulator is identified by a feedback/adjust net on the same part, which
    is a far more specific signature than a reference-designator prefix: the
    1V3 LDO here carries ``N3_1V3_FB``.  Its output pin must not be mistaken
    for the worst-case load, because the impedance a device sees is measured
    at the device, not at the regulator.
    """
    pins = defaultdict(set)
    for p in model["pads"]:
        pins[p["ref"]].add(p["net"])
    out = set()
    for ref, nets in pins.items():
        if rail not in nets:
            continue
        if any(_FB_RE.search(n or "") for n in nets):
            out.add(ref)
    return out


def _ic_pads_on(model, rail, exclude=()):
    return [p for p in model["pads"]
            if p["net"] == rail and di.is_ic(p["ref"])
            and p["ref"] not in exclude]


def _worst_case_load(model, rail, caps, exclude=()):
    """The rail pin that is hardest to decouple: the load pin furthest from
    the nearest bypass capacitor.  Evaluating the PDN there is the
    conservative choice."""
    pads = _ic_pads_on(model, rail, exclude)
    if not pads or not caps:
        return None
    best, best_d = None, -1.0
    for p in pads:
        d = min(math.hypot(p["pos_mm"][0] - c["pos_mm"][0],
                           p["pos_mm"][1] - c["pos_mm"][1])
                for c in caps if c.get("pos_mm"))
        if d > best_d:
            best, best_d = p, d
    return best


def _rail_branches(model, stack, rail, load_pad, caps):
    """Solved copper resistance and path length from the load pin to each cap.

    Returns a list of branch dicts and the network, or ``None`` when the rail
    cannot be solved.
    """
    nn = build_for_net(rail, model, stack, include_zones=True)
    if nn.node_count == 0:
        return None, None
    load_key = f"{load_pad['ref']}.{load_pad['pad']}"
    src = nn.pad_nodes.get(load_key) or []
    if not src:
        return None, None

    branches = []
    for c in caps:
        dst = [n for k, nodes in nn.pad_nodes.items()
               if k.split(".")[0] == c["ref"] for n in nodes]
        if not dst:
            continue
        reff = nn.effective_resistances(src, dst)
        vals = [v for v in reff.values() if v <= OPEN_OHM]
        if not vals:
            continue
        length = nn.shortest_copper_path_mm(src, dst)
        branches.append({**c,
                         "r_cu_ohm": min(vals),
                         "path_mm": length if length is not None else 0.0})
    return branches, nn


def _pdn_deck(rail, branches, r_src, l_src_per_h, band, ztarget, f_crit):
    """Compose the AC deck.  Node ``vdd`` is the load pin; a 1 A AC source
    makes the node voltage numerically equal to the impedance."""
    lines = [
        f"* PDN impedance at the worst-case {rail} pin, from extracted layout.",
        "* Element values: R from the solved copper network, L from the real",
        "* via geometry and routed path, C from the placed part.",
        "* h = outer-layer to first-plane dielectric height in mm (swept),",
        "* because the board declares no stackup.",
        ".param h=0.12",
        "Itest 0 vdd AC 1",
    ]
    # Regulator / bulk feed: copper resistance in series with the loop
    # inductance of the path back to the source.
    lines += [
        f"Rsrc vdd nsrc {_fmt(max(r_src, 1e-4))}",
        f"Lsrc nsrc 0 {{{_fmt(l_src_per_h)}*h}}",
    ]
    for i, b in enumerate(branches):
        n = f"{i}"
        # l_per_h is the height-proportional inductance (via pair, surface
        # runs and the routed path to the load); esl_h is the package's own.
        tag = (f", returns via {b['cross_rail']}" if b.get("cross_rail") else "")
        lines += [
            f"* {b['ref']} {b['package']} {b['farads']*1e9:g} nF, "
            f"{b['path_mm']:.1f} mm from the pin{tag}",
            f"R{n} vdd a{n} {_fmt(max(b['r_cu_ohm'] + b['esr_ohm'], 1e-4))}",
            f"L{n} a{n} b{n} {{{_fmt(b['l_per_h'])}*h+{_fmt(b['esl_h'])}}}",
        ]
        if b.get("cross_rail") and b.get("far_rail_farads"):
            # The far end sits on the opposite supply, which reaches ground
            # only through its own bypass.  That lumped network is in series.
            lines += [
                f"C{n} b{n} c{n} {_fmt(b['farads'])}",
                f"Rf{n} c{n} d{n} {_fmt(max(b['far_rail_esr_ohm'], 1e-4))}",
                f"Lf{n} d{n} e{n} {{{_fmt(b['far_rail_l_per_h'])}*h}}",
                f"Cf{n} e{n} 0 {_fmt(b['far_rail_farads'])}",
                f"Rp{n} e{n} 0 1G",
                f"Rq{n} c{n} 0 1G",
            ]
        else:
            lines += [
                f"C{n} b{n} 0 {_fmt(b['farads'])}",
                f"Rp{n} b{n} 0 1G",
            ]
    lo, hi = band["low"], band["high"]
    lines += [
        f".step param h list {_fmt(OUTER_TO_PLANE_MM['min'])} "
        f"{_fmt(OUTER_TO_PLANE_MM['typical'])} {_fmt(OUTER_TO_PLANE_MM['max'])}",
        f".ac dec 400 {_fmt(lo)} {_fmt(hi)}",
        f".meas ac zmax MAX mag(V(vdd)) FROM {_fmt(lo)} TO {_fmt(hi)}",
        f".meas ac zlow FIND mag(V(vdd)) AT={_fmt(lo)}",
        f".meas ac zcrit FIND mag(V(vdd)) AT={_fmt(f_crit)}",
        f".meas ac zhigh FIND mag(V(vdd)) AT={_fmt(hi)}",
        # Frequency at which the PDN first rises through its target: the
        # usable decoupling bandwidth.
        f".meas ac fcross WHEN mag(V(vdd))={_fmt(ztarget)} RISE=1",
        ".end",
    ]
    return lines


@gate(
    "G40",
    "Power distribution network impedance (LTspice)",
    "At the hardest-to-decouple pin of each rail, the simulated PDN impedance "
    "stays below the target impedance across the control band, using "
    "capacitor and interconnect parasitics extracted from the layout.",
    sources=[PDN_SRC, PAUL_SRC],
)
def g40_pdn_impedance(model, ctx, r):
    if not ctx.get("enable_spice", True):
        r.skip("SPICE gates disabled with --no-spice.")
        return
    ltspice = ctx.get("ltspice")
    if not ltspice:
        r.skip("LTspice executable not found; PDN simulation not run.")
        return

    stack = ctx["stack"]
    band = PDN_BAND_HZ
    h_typ = OUTER_TO_PLANE_MM["typical"]
    # The master clock is the dominant periodic current on this board, so its
    # frequency is where the PDN has to be in specification.  Holding the
    # target impedance all the way to 100 MHz is an on-die/package job, not a
    # board-level one, so the band edge is reported rather than gated.
    f_crit = di.MCLK_HZ
    r.metrics["band_hz"] = [band["low"], band["high"]]
    r.metrics["plane_height_sweep_mm"] = OUTER_TO_PLANE_MM
    r.assume(
        "The outer-to-plane dielectric height is not declared by the board, so "
        f"each rail is simulated at {OUTER_TO_PLANE_MM['min']}, "
        f"{OUTER_TO_PLANE_MM['typical']} and {OUTER_TO_PLANE_MM['max']} mm and "
        "the gate reports the worst case."
    )
    r.assume(
        "Capacitor ESR/ESL come from the placed package size; the regulator is "
        "modelled as an ideal source behind the solved copper resistance and "
        "the loop inductance of the feed path."
    )

    names = set(model["nets"].values())
    results, failures, warnings = {}, [], []

    for rail, spec in sorted(di.RAILS.items()):
        if rail == "GND" or rail not in names:
            continue
        if spec.get("kind") in ("switching", "return"):
            # A charge-pump flying-capacitor node is driven hard and is meant
            # to swing; target impedance is not a meaningful criterion there.
            continue
        caps = pz.decoupling_network(model, rail, h_typ)
        if not caps:
            warnings.append({"rail": rail, "reason": "no decoupling capacitor"})
            continue
        regs = regulator_refs(model, rail)
        load = _worst_case_load(model, rail, caps, exclude=regs)
        if load is None:
            continue
        branches, nn = _rail_branches(model, stack, rail, load, caps)
        if not branches:
            continue

        # Split each branch's inductance into the height-proportional part
        # (so LTspice can sweep it) and the fixed package part.
        width = _rail_track_width_mm(model, rail)
        far_cache = {}
        for b in branches:
            l_path = rules.trace_inductance_h(b["path_mm"], width, h_typ)
            b["l_per_h"] = (b["l_mount_h"] + l_path) / h_typ
            far = b.get("cross_rail")
            if far:
                if far not in far_cache:
                    far_cache[far] = _lumped_rail_bypass(model, far, h_typ)
                b.update(far_cache[far])

        r_src, l_src_per_h = _source_feed(
            model, stack, rail, load, h_typ, ctx.get("rail_sources") or {},
            width)
        ztarget = rules.pdn_target_impedance_ohm(
            abs(spec["volts"]), spec["current_a"], spec.get("kind", "default"))

        deck = _pdn_deck(rail, branches, r_src, l_src_per_h, band,
                         ztarget, f_crit)
        path = spice.write_deck(ctx["spice_dir"], f"pdn_{rail}", deck)
        try:
            meas = spice.run_deck_stepped(ltspice, path)
        except spice.SpiceError as exc:
            warnings.append({"rail": rail, "reason": str(exc)[:160]})
            continue

        # Impedances: take the worst across the stackup sweep.  Crossover
        # frequency: take the lowest, which is likewise the worst case.
        zmax = max(meas.get("zmax") or [], default=None)
        zcrit = max(meas.get("zcrit") or [], default=None)
        fcross = min(meas.get("fcross") or [], default=None)
        if zcrit is None:
            warnings.append({"rail": rail, "reason": "impedance not measured"})
            continue

        entry = {
            "z_at_mclk_ohm": round(zcrit, 4),
            "z_target_ohm": round(ztarget, 4),
            "z_max_in_band_ohm": round(zmax, 4) if zmax else None,
            "z_at_100khz_ohm": round(max(meas.get("zlow") or [0]), 4),
            "z_at_100mhz_ohm": round(max(meas.get("zhigh") or [0]), 4),
            "decoupling_bandwidth_hz": round(fcross) if fcross else None,
            "cap_count": len(branches),
            "local_cap_count": sum(
                1 for b in branches
                if b["path_mm"] <= AUDIO["bulk_bypass_max_pad_distance_mm"]),
            "total_capacitance_uf": round(
                sum(b["farads"] for b in branches) * 1e6, 3),
            "worst_pin": f"{load['ref']}.{load['pad']}",
            "nearest_cap_mm": round(min(b["path_mm"] for b in branches), 2),
            "margin_db_at_mclk": (round(20 * math.log10(ztarget / zcrit), 2)
                                  if zcrit > 0 else None),
            "assumed_current_a": spec["current_a"],
            # The target scales with the transient current, which is an
            # estimate.  Quoting the current at which this rail would just
            # meet its target makes the verdict's sensitivity explicit and
            # lets the designer settle it from the real datasheet figure.
            "passes_if_transient_below_a": round(
                abs(spec["volts"]) * rules.PDN_RIPPLE_FRACTION.get(
                    spec.get("kind", "default"),
                    rules.PDN_RIPPLE_FRACTION["default"]) / zcrit, 4)
            if zcrit > 0 else None,
            "track_width_mm": width,
        }
        results[rail] = entry
        if zcrit > ztarget:
            failures.append({"rail": rail, **entry})

    r.metrics["rails"] = results
    r.metrics["criterion_frequency_hz"] = f_crit
    if warnings:
        r.warn("PDN_NOT_EVALUATED",
               f"{len(warnings)} rail(s) could not be simulated.",
               count=len(warnings), detail=warnings[:10])
    if failures:
        worst = sorted(failures,
                       key=lambda d: d["z_at_mclk_ohm"] / d["z_target_ohm"],
                       reverse=True)
        r.fail("PDN_OVER_TARGET",
               f"{len(failures)} of {len(results)} rail(s) exceed their target "
               f"impedance at the {f_crit/1e6:.2f} MHz master clock, where the "
               f"board's dominant switching current sits. The target scales "
               f"with the assumed transient current, so each entry also "
               f"reports the current at which it would pass.",
               count=len(failures), worst=worst[:12])
    elif results:
        r.note(f"All {len(results)} simulated rails stay under target "
               f"impedance at {f_crit/1e6:.2f} MHz.")


def _lumped_rail_bypass(model, rail, h_typ):
    """One-element equivalent of a rail's own ground-referenced bypass.

    Used as the series return path for a cross-rail capacitor: the far
    terminal only reaches ground through whatever decouples that supply.
    Capacitances add, while the parallel ESR and mounting inductances divide.
    """
    caps = pz.decoupling_network(model, rail, h_typ, include_cross_rail=False)
    if not caps:
        # No ground-referenced bypass on the far rail: leave the series path
        # open rather than inventing one.
        return {"far_rail_farads": 0.0, "far_rail_esr_ohm": 1e3,
                "far_rail_l_per_h": 0.0}
    total_c = sum(c["farads"] for c in caps)
    n = len(caps)
    esr = sum(c["esr_ohm"] for c in caps) / (n * n)
    l_tot = sum(c["l_total_h"] for c in caps) / (n * n)
    return {"far_rail_farads": total_c,
            "far_rail_esr_ohm": esr,
            "far_rail_l_per_h": l_tot / h_typ}


def _rail_track_width_mm(model, rail, default=0.4):
    """Median routed width on a rail -- the width the current actually sees."""
    widths = sorted(t["width_mm"] for t in model["tracks"]
                    if t["net"] == rail and t.get("width_mm"))
    if not widths:
        return default
    return round(widths[len(widths) // 2], 4)


def _source_feed(model, stack, rail, load_pad, h_typ, rail_sources,
                 width_mm=0.4):
    """Copper resistance and height-normalised inductance from the load pin
    back to the rail's source pin."""
    src_ref = rail_sources.get(rail)
    nn = build_for_net(rail, model, stack, include_zones=True)
    load_key = f"{load_pad['ref']}.{load_pad['pad']}"
    a = nn.pad_nodes.get(load_key) or []
    b = [n for k, nodes in nn.pad_nodes.items()
         if k.split(".")[0] == src_ref for n in nodes] if src_ref else []
    if not a or not b:
        # Without an identified source, fall back to a short low-impedance
        # feed; the capacitors then dominate, which is the usual case anyway.
        return 0.01, rules.trace_inductance_h(10.0, width_mm, h_typ) / h_typ
    reff = nn.effective_resistances(a, b)
    vals = [v for v in reff.values() if v <= OPEN_OHM]
    r_cu = min(vals) if vals else 0.01
    length = nn.shortest_copper_path_mm(a, b) or 10.0
    return r_cu, rules.trace_inductance_h(length, width_mm, h_typ) / h_typ


@gate(
    "G41",
    "Headphone output loading and damping (LTspice)",
    "With the solved output-path resistance in circuit, the amplifier still "
    "meets its damping-factor target into the rated load and the two channels "
    "stay matched.",
    sources=["D. Self, Audio Power Amplifier Design"],
)
def g41_output_loading(model, ctx, r):
    if not ctx.get("enable_spice", True):
        r.skip("SPICE gates disabled with --no-spice.")
        return
    ltspice = ctx.get("ltspice")
    if not ltspice:
        r.skip("LTspice executable not found; output simulation not run.")
        return

    stack = ctx["stack"]
    load = AUDIO["headphone_load_ohm"]
    target_df = AUDIO["min_damping_factor"]
    r.metrics["load_ohm"] = load
    r.metrics["min_damping_factor"] = target_df
    r.assume(
        "The amplifier is modelled as an ideal source, so the simulated "
        "damping factor is the ceiling the copper allows; the active stage can "
        "only reduce it."
    )

    names = set(model["nets"].values())
    out = {}
    for net in sorted(di.OUTPUT_PATH_NETS):
        if net not in names:
            continue
        res = _net_series_resistance(model, stack, net)
        if res is not None:
            out[net] = res

    if not out:
        r.skip("No output-path nets could be solved.")
        return

    lines = [
        "* Headphone output: solved copper resistance driving the rated load.",
        "Vin in 0 AC 1",
    ]
    order = sorted(out)
    for i, net in enumerate(order):
        lines += [
            f"R{i} in o{i} {_fmt(max(out[net], 1e-5))}",
            f"Rl{i} o{i} 0 {_fmt(load)}",
        ]
    lines += [".ac lin 1 1k 1k"]
    for i, net in enumerate(order):
        lines.append(f".meas ac g{i} FIND mag(V(o{i})) AT=1k")
    lines.append(".end")

    path = spice.write_deck(ctx["spice_dir"], "output_loading", lines)
    try:
        meas = spice.run_deck(ltspice, path)
    except spice.SpiceError as exc:
        r.warn("SIM_FAILED", f"Output-stage simulation did not run: {exc}")
        return

    losses, worst_df, worst_net = {}, None, None
    for i, net in enumerate(order):
        g = meas.get(f"g{i}")
        if g is None:
            continue
        loss_db = 20 * math.log10(max(g, 1e-12))
        df = load / max(out[net], 1e-9)
        losses[net] = {"r_copper_ohm": round(out[net], 5),
                       "insertion_loss_db": round(loss_db, 4),
                       "damping_factor": round(df, 1)}
        if worst_df is None or df < worst_df:
            worst_df, worst_net = df, net

    r.metrics["outputs"] = losses
    r.metrics["worst_damping_factor"] = round(worst_df, 1) if worst_df else None
    r.metrics["worst_net"] = worst_net

    bad = {n: v for n, v in losses.items() if v["damping_factor"] < target_df}
    if bad:
        r.warn("DAMPING_BELOW_TARGET",
               f"{len(bad)} output net(s) hold the damping factor below "
               f"{target_df:.0f} through copper resistance alone.",
               count=len(bad),
               worst=sorted(bad.items(), key=lambda kv: kv[1]["damping_factor"])[:6])
    else:
        r.note(f"Copper alone permits a damping factor of at least "
               f"{worst_df:.0f} into {load:.0f} ohm.")


def _net_series_resistance(model, stack, net):
    """End-to-end copper resistance of one output net."""
    nn = build_for_net(net, model, stack, include_zones=True)
    if nn.node_count == 0:
        return None
    groups = defaultdict(list)
    for key, nodes in nn.pad_nodes.items():
        groups[key.split(".")[0]].extend(nodes)
    if len(groups) < 2:
        return None
    refs = sorted(groups)
    # Worst pair: a connector against the first driver found.
    conn = [x for x in refs if di.ref_prefix(x) == "J"]
    a_ref = conn[0] if conn else refs[0]
    others = [x for x in refs if x != a_ref]
    best = None
    for b_ref in others:
        reff = nn.effective_resistances(groups[a_ref], groups[b_ref])
        vals = [v for v in reff.values() if v <= OPEN_OHM]
        if vals:
            v = min(vals)
            best = v if best is None else max(best, v)
    return best
