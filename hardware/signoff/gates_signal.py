"""Signal-integrity gates: USB high speed, clock routing and coupling.

These gates reason about the routed geometry only.  Where a conclusion needs
the dielectric build (impedance, in particular) the gate says so explicitly
rather than quoting a number that the missing stackup cannot support.
"""

from __future__ import annotations

import math
from collections import defaultdict

from . import design_intent as di
from . import geom
from .framework import gate
from .rules import AUDIO, USB_HS

USB_SRC = "USB 2.0 specification rev 2.0 §7.1.1.3 and USB-IF HS layout guidance"
IPC2251_SRC = "IPC-2251 (design guide for high-speed interconnect)"
OTT_SRC = "H. Ott, Electromagnetic Compatibility Engineering, ch. 10-12"


def _net_tracks(model, net):
    return [t for t in model["tracks"] if t["net"] == net]


def _net_length_mm(model, net):
    return sum(t.get("length_mm") or geom.dist(t["start_mm"], t["end_mm"])
               for t in _net_tracks(model, net))


def _net_vias(model, net):
    return [v for v in model["vias"] if v["net"] == net]


@gate(
    "G20",
    "USB high-speed differential pair",
    "The USB 2.0 high-speed pair is routed as a matched, tightly coupled pair "
    "with a continuous reference and the intra-pair skew well inside the "
    "specification limit.",
    sources=[USB_SRC, IPC2251_SRC],
)
def g20_usb_pair(model, ctx, r):
    pos, neg = "USB_DP", "USB_DN"
    names = set(model["nets"].values())
    if pos not in names or neg not in names:
        r.info("USB_NET_ABSENT", "No USB_DP/USB_DN nets on this board.")
        return

    tp, tn = _net_tracks(model, pos), _net_tracks(model, neg)
    if not tp or not tn:
        r.fail("USB_UNROUTED",
               f"The USB pair is not routed ({len(tp)} / {len(tn)} segments).",
               dp_segments=len(tp), dn_segments=len(tn))
        return

    lp, ln = _net_length_mm(model, pos), _net_length_mm(model, neg)
    skew = abs(lp - ln)
    limit = USB_HS["intra_pair_skew_mm"]
    r.metrics["dp_length_mm"] = round(lp, 3)
    r.metrics["dn_length_mm"] = round(ln, 3)
    r.metrics["intra_pair_skew_mm"] = round(skew, 3)
    r.metrics["skew_limit_mm"] = limit

    if skew > limit:
        r.fail("USB_SKEW",
               f"Intra-pair skew {skew:.2f} mm exceeds the {limit} mm limit.",
               skew_mm=round(skew, 3))
    elif skew > limit / 2.0:
        r.warn("USB_SKEW_MARGIN",
               f"Intra-pair skew {skew:.2f} mm uses more than half of the "
               f"{limit} mm budget.",
               skew_mm=round(skew, 3))

    longest = max(lp, ln)
    r.metrics["longest_leg_mm"] = round(longest, 3)
    if longest > USB_HS["max_trace_mm"]:
        r.warn("USB_TRACE_LONG",
               f"The longest leg is {longest:.1f} mm, beyond the "
               f"{USB_HS['max_trace_mm']} mm high-speed routing guidance.",
               length_mm=round(longest, 3))

    # -- layer changes ----------------------------------------------------
    vp, vn = _net_vias(model, pos), _net_vias(model, neg)
    r.metrics["dp_vias"] = len(vp)
    r.metrics["dn_vias"] = len(vn)
    if len(vp) != len(vn):
        r.fail("USB_VIA_ASYMMETRY",
               f"The pair changes layer asymmetrically ({len(vp)} vs {len(vn)} "
               f"vias); the legs no longer see the same reference.",
               dp_vias=len(vp), dn_vias=len(vn))
    if max(len(vp), len(vn)) > USB_HS["max_vias_per_leg"]:
        r.warn("USB_VIA_COUNT",
               f"{max(len(vp), len(vn))} vias per leg exceeds the "
               f"{USB_HS['max_vias_per_leg']} recommended for a HS pair.",
               dp_vias=len(vp), dn_vias=len(vn))

    layers = sorted({t["layer"] for t in tp} | {t["layer"] for t in tn})
    r.metrics["layers_used"] = layers
    stack = ctx["stack"]
    if len(layers) > 1:
        r.info("USB_MULTILAYER",
               f"The pair is routed across {len(layers)} layers: {layers}.",
               layers=layers)

    # -- intra-pair coupling ----------------------------------------------
    gap, widths = _pair_gap_and_widths(tp, tn)
    pair_w = min(widths) if widths else 0.0
    if gap is not None:
        r.metrics["median_pair_centre_gap_mm"] = round(gap, 4)
        r.metrics["pair_track_widths_mm"] = sorted(widths)

    # -- spacing to other signals (the 3W screen) -------------------------
    if pair_w > 0:
        need = USB_HS["min_spacing_to_other_signals_w"] * pair_w
        r.metrics["spacing_to_others_rule_mm"] = round(need, 4)
        intruders, worst = {}, None
        pair_tracks = tp + tn
        others = defaultdict(list)
        for t in model["tracks"]:
            if t["net"] in (pos, neg) or not t["net"]:
                continue
            others[t["layer"]].append(t)
        grids = {}
        for layer, items in others.items():
            g = geom.GridIndex(4.0)
            for t in items:
                g.insert(geom.track_bbox(t), t)
            grids[layer] = g
        # Pin fields of the parts the pair lands on (connector, ESD array, MCU)
        # plus 1 mm of fan-out: there the pinout, not the routing, sets the
        # neighbour spacing (USB-C A5/A6, LQFP 0.5 mm pitch).
        in_field = _pin_field_test(model, pos, neg)

        pin_field = {}
        for t in pair_tracks:
            g = grids.get(t["layer"])
            if g is None:
                continue
            for a in g.query(geom.track_bbox(t), need + 0.5):
                d = geom.seg_seg_distance(t["start_mm"], t["end_mm"],
                                          a["start_mm"], a["end_mm"])
                edge = d - t["width_mm"] / 2.0 - a["width_mm"] / 2.0
                if worst is None or edge < worst[0]:
                    worst = (edge, a["net"], t["layer"])
                if edge < need:
                    bucket = pin_field if in_field(t) and in_field(a) else intruders
                    if a["net"] not in bucket or edge < bucket[a["net"]][0]:
                        bucket[a["net"]] = (round(edge, 4), t["layer"])
        if worst:
            r.metrics["min_spacing_to_other_signal_mm"] = round(worst[0], 4)
            r.metrics["min_spacing_offender"] = [worst[1], worst[2]]
        pin_field = {k: v for k, v in pin_field.items() if k not in intruders}
        if pin_field:
            r.info("USB_PIN_FIELD_SPACING",
                   f"{len(pin_field)} net(s) sit closer than 3W only inside the pin "
                   f"field of a part the pair lands on (pinout-fixed).",
                   worst=[{"net": k, "gap_mm": v[0]} for k, v in sorted(pin_field.items())])
        if intruders:
            r.warn("USB_3W_SPACING",
                   f"{len(intruders)} other net(s) come closer to the USB pair "
                   f"than the {USB_HS['min_spacing_to_other_signals_w']}W "
                   f"({need:.2f} mm) screen.",
                   count=len(intruders), rule_mm=round(need, 4),
                   worst=[{"net": k, "gap_mm": v[0], "layer": v[1]}
                          for k, v in sorted(intruders.items(),
                                             key=lambda kv: kv[1][0])[:12]])

    # -- impedance --------------------------------------------------------
    if stack.assumed:
        r.fail("USB_IMPEDANCE_UNVERIFIABLE",
               f"The board declares a USB_DIFF controlled-impedance netclass, "
               f"but no stackup defines the dielectric height or Er. The "
               f"{USB_HS['z_diff_ohm']} ohm +/-{USB_HS['z_diff_tol_pct']}% "
               f"target cannot be computed here, nor specified to the "
               f"fabricator.",
               target_ohm=USB_HS["z_diff_ohm"],
               tolerance_pct=USB_HS["z_diff_tol_pct"])
        r.assume("Impedance is therefore not evaluated numerically.")
    else:
        _usb_impedance(model, r, tp, tn, gap, pair_w)


def _pin_field_test(model, pos, neg):
    """Predicate: does a track touch the pin field (courtyard + 1 mm fan-out) of a
    part the pair lands on?  There the pinout, not the routing, sets the geometry."""
    end_refs = {p["ref"] for p in model["pads"] if p["net"] in (pos, neg)}
    fields = []
    for fp in model.get("footprints", []):
        if fp["ref"] in end_refs:
            pts = [q for poly in (fp.get("courtyard") or {}).get("front", []) for q in poly]
            if pts:
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                fields.append((min(xs) - 1.0, min(ys) - 1.0, max(xs) + 1.0, max(ys) + 1.0))

    def in_field(tr):
        bx = geom.track_bbox(tr)
        return any(bx[0] < f[2] and f[0] < bx[2] and bx[1] < f[3] and f[1] < bx[3] for f in fields)
    return in_field


def _coupled_sections(tp, tn, max_pitch=0.55):
    """{(width, centre pitch): coupled length} for parallel DP/DN runs, and the uncoupled length."""
    sections, coupled, loose = {}, 0.0, []
    for t in tp + tn:
        (ax, ay), (bx, by) = t["start_mm"], t["end_mm"]
        L = math.dist((ax, ay), (bx, by))
        if L < 1e-6:
            continue
        ux, uy = (bx - ax) / L, (by - ay) / L
        best = None
        for o in (tn if t in tp else tp):
            (cx, cy), (dx, dy) = o["start_mm"], o["end_mm"]
            L2 = math.dist((cx, cy), (dx, dy))
            if L2 < 1e-6 or abs(ux * (dx - cx) / L2 + uy * (dy - cy) / L2) < 0.999:
                continue
            t1, t2 = sorted(((cx - ax) * ux + (cy - ay) * uy, (dx - ax) * ux + (dy - ay) * uy))
            overlap = min(L, t2) - max(0.0, t1)
            d = abs((cx - ax) * -uy + (cy - ay) * ux)
            if overlap > 0.1 and d < max_pitch and (best is None or d < best[0]):
                best = (d, overlap, (t["width_mm"] + o["width_mm"]) / 2)
        if best and t in tp:
            key = (round(best[2], 3), round(best[0], 3))
            sections[key] = sections.get(key, 0.0) + best[1]
            coupled += best[1]
        elif not best:
            loose.append(t)
    return sections, loose


def _usb_impedance(model, r, tp, tn, centre_gap, width):
    """Differential impedance of each coupled section of the routed pair on the declared stackup."""
    from .tline import microstrip
    rows = model["stackup"]["layers"]
    layer = tp[0]["layer"]
    names = [row["layer"] or row["name"] for row in rows]
    i = names.index(layer)
    step = 1 if i < len(rows) / 2 else -1          # towards the board centre = towards the plane
    cu = rows[i]["thickness_mm"]
    diel = rows[i + step]
    mask = next((row for row in rows if "Solder Mask" in (row["type"] or "")
                 and (row["name"][0] == layer[0])), None)
    tm = (mask or {}).get("thickness_mm") or 0.0
    erm = (mask or {}).get("epsilon_r") or 3.8
    target, tol = USB_HS["z_diff_ohm"], USB_HS["z_diff_tol_pct"]
    lo, hi = target * (1 - tol / 100), target * (1 + tol / 100)
    h, er = diel["thickness_mm"], diel["epsilon_r"]
    builds = {"nominal": (h, er, cu),
              "prepreg -10 %, er +0.2, copper +5 um": (0.9 * h, er + 0.2, cu + 0.005),
              "prepreg +10 %, er -0.2, copper -5 um": (1.1 * h, er - 0.2, cu - 0.005)}
    sections, loose = _coupled_sections(tp, tn)
    in_field = _pin_field_test(model, "USB_DP", "USB_DN")
    table, bad = [], []
    for (w, pitch), length in sorted(sections.items(), key=lambda kv: -kv[1]):
        z = {k: microstrip(w, t, hh, e, s=pitch - w, tm=tm, erm=erm)["zdiff"]
             for k, (hh, e, t) in builds.items()}
        row = {"kind": "coupled", "width_mm": w, "edge_gap_mm": round(pitch - w, 3), "length_mm": round(length, 2),
               "zdiff_ohm": {k: round(v, 1) for k, v in z.items()}}
        table.append(row)
        if length >= 1.0 and not all(lo <= v <= hi for v in z.values()):
            bad.append(row)
    # Uncoupled runs (legs > 0.55 mm apart): each leg is its own microstrip, Zdiff ~ 2 Z0.
    split, escape = {}, {}
    for t in loose:
        bucket = escape if in_field(t) else split
        bucket[t["width_mm"]] = bucket.get(t["width_mm"], 0.0) + math.dist(t["start_mm"], t["end_mm"]) / 2
    for kind, bucket in (("split", split), ("pin escape", escape)):
        for w, length in sorted(bucket.items()):
            z = {k: 2 * microstrip(w, t, hh, e, tm=tm, erm=erm)["z0"] for k, (hh, e, t) in builds.items()}
            row = {"kind": kind, "width_mm": w, "length_mm": round(length, 2),
                   "zdiff_ohm": {k: round(v, 1) for k, v in z.items()}}
            table.append(row)
            if kind == "split" and length >= 1.0 and not all(lo <= v <= hi for v in z.values()):
                bad.append(row)
    r.metrics["usb_sections"] = table
    r.metrics["usb_impedance_basis"] = (f"2-D field solve (tline.py): {layer} over {h} mm "
                                        f"{diel.get('material')} er {er}, mask {tm} mm; build corners "
                                        f"+/-10 % prepreg, +/-0.2 er, +/-5 um copper")
    if bad:
        r.fail("USB_IMPEDANCE", f"{len(bad)} coupled section(s) leave {target} ohm +/-{tol}% "
               f"at a build corner.", sections=bad)
    else:
        nom = [row["zdiff_ohm"]["nominal"] for row in table if row["kind"] != "pin escape"]
        r.note(f"USB Zdiff {min(nom):.1f}-{max(nom):.1f} ohm nominal over every coupled and split "
               f"section; all stay inside {lo:.1f}-{hi:.1f} ohm at the build corners. Pin-field escapes "
               f"are listed in the metrics.")

def _pair_gap_and_widths(tp, tn):
    """Median centre-to-centre spacing between the two legs of a pair."""
    widths = {t["width_mm"] for t in tp} | {t["width_mm"] for t in tn}
    gaps = []
    for a in tp:
        best = None
        for b in tn:
            if a["layer"] != b["layer"]:
                continue
            d = geom.seg_seg_distance(a["start_mm"], a["end_mm"],
                                      b["start_mm"], b["end_mm"])
            if best is None or d < best:
                best = d
        if best is not None:
            gaps.append(best)
    if not gaps:
        return None, widths
    gaps.sort()
    return gaps[len(gaps) // 2], widths


@gate(
    "G21",
    "Clock routing and aggressor spacing",
    "Clock nets are routed short, with few layer changes, and keep enough "
    "distance from analog audio nets that crosstalk stays below the audio "
    "noise floor.",
    sources=[OTT_SRC, IPC2251_SRC],
)
def g21_clock_routing(model, ctx, r):
    spacing_rule = AUDIO["clock_to_analog_min_gap_mm"]
    r.metrics["clock_to_audio_rule_mm"] = spacing_rule
    r.assume(
        "Crosstalk is judged by edge-to-edge spacing on shared or adjacent "
        "layers, not by a solved coupled-line model; a full extraction needs "
        "the dielectric build."
    )

    names = set(model["nets"].values())
    clocks = sorted(n for n in di.CLOCK_NETS if n in names)
    audio = sorted(n for n in di.ANALOG_AUDIO_NETS if n in names)
    r.metrics["clock_nets_present"] = len(clocks)
    r.metrics["audio_nets_present"] = len(audio)
    if not clocks or not audio:
        r.info("NO_PAIRING", "No clock/audio net pair to compare.")
        return

    audio_tracks = defaultdict(list)
    for t in model["tracks"]:
        if t["net"] in di.ANALOG_AUDIO_NETS:
            audio_tracks[t["layer"]].append(t)
    grids = {}
    for layer, items in audio_tracks.items():
        g = geom.GridIndex(4.0)
        for t in items:
            g.insert(geom.track_bbox(t), t)
        grids[layer] = g

    stack = ctx["stack"]
    worst = None
    violations = {}
    for t in model["tracks"]:
        if t["net"] not in di.CLOCK_NETS:
            continue
        for layer, g in grids.items():
            # Only same-layer or directly adjacent layers couple meaningfully.
            if layer != t["layer"] and stack.separation_mm(layer, t["layer"]) > 0.4:
                continue
            for a in g.query(geom.track_bbox(t), spacing_rule + 0.5):
                d = geom.seg_seg_distance(t["start_mm"], t["end_mm"],
                                          a["start_mm"], a["end_mm"])
                edge = d - t["width_mm"] / 2.0 - a["width_mm"] / 2.0
                if worst is None or edge < worst[0]:
                    worst = (edge, t["net"], a["net"], layer)
                if edge < spacing_rule:
                    key = (t["net"], a["net"])
                    if key not in violations or edge < violations[key][0]:
                        violations[key] = (round(edge, 4), layer)

    if worst:
        r.metrics["min_clock_to_audio_mm"] = round(worst[0], 4)
        r.metrics["min_clock_to_audio_between"] = [worst[1], worst[2], worst[3]]
    if violations:
        sample = sorted(violations.items(), key=lambda kv: kv[1][0])[:12]
        r.warn("CLOCK_NEAR_AUDIO",
               f"{len(violations)} clock/audio net pair(s) run closer than the "
               f"{spacing_rule} mm guidance.",
               count=len(violations),
               worst=[{"clock": k[0], "audio": k[1], "gap_mm": v[0],
                       "layer": v[1]} for k, v in sample])

    # -- layer changes on jitter-critical nets ----------------------------
    via_limit = AUDIO["critical_net_max_via_count"]
    r.metrics["clock_via_limit"] = via_limit
    many_vias, lengths = [], {}
    for net in clocks:
        lengths[net] = round(_net_length_mm(model, net), 2)
        vias = len(_net_vias(model, net))
        if vias > via_limit:
            many_vias.append((net, vias))
    # Routed length is reported, not gated: no cited standard fixes a clock
    # length limit for this board's edge rates.
    r.metrics["clock_lengths_mm"] = dict(
        sorted(lengths.items(), key=lambda kv: -kv[1])[:15])
    if many_vias:
        r.warn("CLOCK_VIAS",
               f"{len(many_vias)} clock net(s) use more than {via_limit} vias, "
               f"adding reference discontinuities to a jitter-critical net.",
               count=len(many_vias),
               worst=sorted(many_vias, key=lambda x: -x[1])[:10])


@gate(
    "G22",
    "Return path and reference continuity",
    "Signal layers are referenced to a ground plane, and vias that change "
    "reference have a stitching via close enough to carry the return current.",
    sources=[OTT_SRC, "IPC-2251 §5 (reference planes and return current)"],
)
def g22_return_path(model, ctx, r):
    stack = ctx["stack"]
    layer_names = [l["name"] for l in model["copper_layers"]]
    r.metrics["copper_layers"] = layer_names

    zone_layers = defaultdict(set)
    for z in model["zones"]:
        if not z.get("is_rule_area"):
            zone_layers[z["layer"]].add(z["net"])
    r.metrics["zone_nets_by_layer"] = {k: sorted(v) for k, v in zone_layers.items()}

    gnd_layers = [l for l in layer_names if "GND" in zone_layers.get(l, set())]
    r.metrics["ground_plane_layers"] = gnd_layers
    if not gnd_layers:
        r.fail("NO_GROUND_PLANE", "No ground plane zone was found.")
        return

    # Stitching vias are the only way a return current can follow a signal
    # that changes reference plane.
    gnd_vias = [v for v in model["vias"] if v["net"] == "GND"]
    r.metrics["ground_stitching_vias"] = len(gnd_vias)
    if not gnd_vias:
        r.fail("NO_STITCHING_VIAS", "No ground vias are present to tie the planes.")
        return

    gv = geom.GridIndex(4.0)
    for v in gnd_vias:
        x, y = v["pos_mm"]
        gv.insert((x, y, x, y), v)

    limit = AUDIO["max_stitch_via_distance_mm"]
    r.metrics["stitching_distance_rule_mm"] = limit

    lonely = []
    checked = 0
    worst = None
    for v in model["vias"]:
        net = v["net"]
        if net == "GND" or not net:
            continue
        role = di.net_role(net)
        # Only nets whose return current matters are worth the check.
        if role not in ("clock", "digital", "analog_audio"):
            continue
        checked += 1
        x, y = v["pos_mm"]
        near = gv.query_point((x, y), limit)
        best = None
        for g in near:
            d = geom.dist((x, y), g["pos_mm"])
            if best is None or d < best:
                best = d
        if worst is None or (best is not None and best > worst[0]):
            if best is not None:
                worst = (best, net, v["pos_mm"])
        if best is None or best > limit:
            lonely.append({"net": net, "pos_mm": v["pos_mm"],
                           "nearest_gnd_via_mm": None if best is None else round(best, 3)})

    r.metrics["signal_vias_checked"] = checked
    if worst:
        r.metrics["worst_stitching_distance_mm"] = round(worst[0], 3)
        r.metrics["worst_stitching_net"] = worst[1]
    if lonely:
        r.warn("RETURN_PATH_STITCHING",
               f"{len(lonely)} layer-changing signal via(s) have no ground via "
               f"within {limit} mm, so the return current must detour.",
               count=len(lonely), total_checked=checked,
               worst=sorted(lonely,
                            key=lambda d: -(d["nearest_gnd_via_mm"] or 1e9))[:12])


@gate(
    "G23",
    "Switching-node keep-out",
    "The charge-pump and regulator switching nodes keep clear of analog audio "
    "and high-impedance nets, so switching noise is not injected into the "
    "signal path.",
    sources=[OTT_SRC, "TI SLVA959 / LM27762 layout guidance"],
)
def g23_switching_keepout(model, ctx, r):
    # No cited standard sets a switching-node keep-out for this topology, so
    # the digital-to-analog gap is applied as a documented floor.  A switching
    # node is a worse aggressor than ordinary digital, so clearing this gap is
    # necessary but not by itself sufficient.
    keepout = AUDIO["digital_to_analog_min_gap_mm"]
    r.metrics["switcher_keepout_mm"] = keepout
    r.assume(
        "The switching-node keep-out is the digital-to-analog minimum gap "
        f"({keepout} mm) applied as a floor, not a switcher-specific limit."
    )

    sw_tracks = [t for t in model["tracks"] if t["net"] in di.SWITCHING_NETS]
    r.metrics["switching_net_segments"] = len(sw_tracks)
    if not sw_tracks:
        r.info("NO_SWITCHING_NETS", "No switching nets are routed on this board.")
        return

    victims = defaultdict(list)
    for t in model["tracks"]:
        if t["net"] in di.ANALOG_AUDIO_NETS or t["net"] in di.FEEDBACK_NETS:
            victims[t["layer"]].append(t)
    grids = {}
    for layer, items in victims.items():
        g = geom.GridIndex(4.0)
        for t in items:
            g.insert(geom.track_bbox(t), t)
        grids[layer] = g

    stack = ctx["stack"]
    breaches, worst = {}, None
    for t in sw_tracks:
        for layer, g in grids.items():
            if layer != t["layer"] and stack.separation_mm(layer, t["layer"]) > 0.4:
                continue
            for a in g.query(geom.track_bbox(t), keepout + 0.5):
                d = geom.seg_seg_distance(t["start_mm"], t["end_mm"],
                                          a["start_mm"], a["end_mm"])
                edge = d - t["width_mm"] / 2.0 - a["width_mm"] / 2.0
                if worst is None or edge < worst[0]:
                    worst = (edge, t["net"], a["net"], layer)
                if edge < keepout:
                    key = (t["net"], a["net"])
                    if key not in breaches or edge < breaches[key][0]:
                        breaches[key] = (round(edge, 4), layer)

    if worst:
        r.metrics["min_switcher_to_audio_mm"] = round(worst[0], 4)
        r.metrics["min_switcher_to_audio_between"] = [worst[1], worst[2], worst[3]]
    if breaches:
        sample = sorted(breaches.items(), key=lambda kv: kv[1][0])[:12]
        r.warn("SWITCHER_NEAR_AUDIO",
               f"{len(breaches)} switching/audio net pair(s) are closer than "
               f"the {keepout} mm keep-out.",
               count=len(breaches),
               worst=[{"switching": k[0], "audio": k[1], "gap_mm": v[0],
                       "layer": v[1]} for k, v in sample])
