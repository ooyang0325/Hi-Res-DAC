"""Fabrication, assembly and documentation gates.

G01  Fabricator process window (JLCPCB multilayer).
G02  IPC-2221B electrical clearance vs the configured design rules.
G03  Plated-hole geometry: annular ring and aspect ratio (IPC-6012).
G04  Assembly geometry: courtyard overlap, board-edge keepout (IPC-7351B).
G05  Fabrication documentation: stackup, impedance spec, legend.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from . import design_intent as di
from . import geom
from .framework import gate
from .rules import (
    ASPECT_RATIO_FAIL,
    ASPECT_RATIO_WARN,
    IPC6012_CLASS2_ANNULAR_MM,
    JLC,
    ipc2221_clearance_mm,
)

JLC_SRC = "JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com"
IPC2221_SRC = "IPC-2221B Table 6-1 (electrical conductor spacing)"
IPC6012_SRC = "IPC-6012 (qualification and performance, rigid boards)"
IPC7351_SRC = "IPC-7351B (land pattern and courtyard requirements)"


@gate(
    "G01",
    "Fabricator process window",
    "Every drawn feature is inside the JLCPCB multilayer process window, with "
    "the surcharge-free and recommended values treated as warnings.",
    sources=[JLC_SRC],
)
def g01_process_window(model, ctx, r):
    tracks = model["tracks"]
    vias = model["vias"]

    # ---- track width --------------------------------------------------
    widths = Counter(round(t["width_mm"], 4) for t in tracks)
    min_w = min(widths) if widths else None
    r.metrics["track_width_histogram_mm"] = {str(k): v for k, v in sorted(widths.items())}
    r.metrics["min_track_width_mm"] = min_w
    if min_w is not None:
        if min_w < JLC["min_track_mm"]:
            offenders = [t for t in tracks if t["width_mm"] < JLC["min_track_mm"]]
            r.fail(
                "TRACK_BELOW_PROCESS",
                f"{len(offenders)} track(s) at {min_w} mm are below the "
                f"{JLC['min_track_mm']} mm multilayer etch limit.",
                min_mm=min_w, limit_mm=JLC["min_track_mm"], count=len(offenders),
            )
        elif min_w < JLC["preferred_track_mm"]:
            n = sum(c for w, c in widths.items() if w < JLC["preferred_track_mm"])
            r.info(
                "TRACK_BELOW_PREFERRED",
                f"{n} track(s) are narrower than the {JLC['preferred_track_mm']} mm "
                f"preferred width (minimum drawn {min_w} mm). Manufacturable, but "
                f"yield-sensitive at the +/-20% width tolerance.",
                min_mm=min_w, preferred_mm=JLC["preferred_track_mm"], count=n,
            )

    # ---- via geometry ---------------------------------------------------
    via_specs = Counter((round(v["diameter_mm"], 3), round(v["drill_mm"], 3)) for v in vias)
    r.metrics["via_specs"] = {f"{d}/{h}": c for (d, h), c in sorted(via_specs.items())}
    r.metrics["via_count"] = len(vias)

    blind = [v for v in vias if v["type"] in ("blind", "buried", "microvia")]
    if blind:
        r.fail(
            "BLIND_BURIED_VIA",
            f"{len(blind)} blind/buried/micro via(s) present; the quoted process "
            f"is through-hole only.",
            count=len(blind),
        )

    for (dia, drill), count in sorted(via_specs.items()):
        if drill < JLC["min_via_drill_mm"]:
            r.fail("VIA_DRILL_BELOW_PROCESS",
                   f"{count} via(s) drill {drill} mm < {JLC['min_via_drill_mm']} mm.",
                   drill_mm=drill, count=count)
        elif drill < JLC["preferred_via_drill_mm"]:
            r.warn("VIA_DRILL_SURCHARGE",
                   f"{count} via(s) drill {drill} mm attract the fine-drill surcharge "
                   f"(preferred {JLC['preferred_via_drill_mm']} mm).",
                   drill_mm=drill, count=count)
        if dia < drill + JLC["via_diameter_over_drill_mm"] - 1e-9:
            r.fail("VIA_PAD_TOO_SMALL",
                   f"{count} via(s) pad {dia} mm is less than drill + "
                   f"{JLC['via_diameter_over_drill_mm']} mm.",
                   diameter_mm=dia, drill_mm=drill, count=count)
        if drill <= 0.25 and dia < JLC["surcharge_free_via_pad_mm"]:
            r.warn("VIA_PAD_SURCHARGE",
                   f"{count} via(s) with {drill} mm drill have a {dia} mm pad, below "
                   f"the {JLC['surcharge_free_via_pad_mm']} mm surcharge-free pad.",
                   diameter_mm=dia, drill_mm=drill, count=count)

    # ---- hole-to-hole ---------------------------------------------------
    idx = geom.GridIndex(2.0)
    holes = []
    for v in vias:
        holes.append({"kind": "via",
                      "pad": {"pos_mm": v["pos_mm"],
                              "drill_mm": [v["drill_mm"], v["drill_mm"]],
                              "orientation_deg": 0.0},
                      "pos": v["pos_mm"], "drill": v["drill_mm"],
                      "id": f"via@{v['pos_mm']}", "net": v["net"]})
    for p in model["pads"]:
        d = max(p["drill_mm"])
        if d > 0:
            holes.append({"kind": "pad", "pad": p, "pos": p["pos_mm"], "drill": d,
                          "id": f"{p['ref']}.{p['pad']}", "net": p["net"]})
    for h in holes:
        x, y = h["pos"]
        half = h["drill"] / 2.0
        idx.insert((x - half, y - half, x + half, y + half), h)

    worst = None
    h2h_fails = []
    seen_pairs = set()
    for h in holes:
        x, y = h["pos"]
        reach = 2.0 + h["drill"] / 2.0
        for other in idx.query_point((x, y), reach):
            if other is h:
                continue
            pair = tuple(sorted((id(h), id(other))))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            # Slot-aware: a hole is a capsule, not a circle of its long axis.
            gap = geom.hole_gap_mm(h["pad"], other["pad"])
            limit = (JLC["pad_hole_to_hole_mm"]
                     if "pad" in (h["kind"], other["kind"])
                     else JLC["via_hole_to_hole_mm"])
            if worst is None or gap < worst[0]:
                worst = (gap, h["id"], other["id"], limit)
            if gap < limit - 1e-6:
                key = tuple(sorted((h["id"], other["id"])))
                h2h_fails.append((key, round(gap, 4), limit))
    if worst:
        r.metrics["min_hole_to_hole_mm"] = round(worst[0], 4)
        r.metrics["min_hole_to_hole_between"] = [worst[1], worst[2]]
    uniq = {k: v for k, v, _ in h2h_fails}
    if uniq:
        sample = sorted(uniq.items(), key=lambda kv: kv[1])[:10]
        r.fail("HOLE_TO_HOLE",
               f"{len(uniq)} hole pair(s) closer than the hole-to-hole minimum.",
               count=len(uniq), worst=sample)

    # ---- copper to board edge ------------------------------------------
    outline = model["outline"]["polygons"]
    if outline:
        ring = outline[0]
        edges = list(zip(ring, ring[1:] + ring[:1]))
        limit = JLC["copper_to_edge_routed_mm"]
        worst_edge = None
        breaches = []
        for t in model["tracks"]:
            for pt in (t["start_mm"], t["end_mm"]):
                d = min(geom.seg_point_distance(pt, a, b) for a, b in edges)
                clear = d - t["width_mm"] / 2.0
                if worst_edge is None or clear < worst_edge[0]:
                    worst_edge = (clear, f"track {t['net']} @ {pt}")
                if clear < limit:
                    breaches.append((t["net"], round(clear, 4)))
        for v in model["vias"]:
            d = min(geom.seg_point_distance(v["pos_mm"], a, b) for a, b in edges)
            clear = d - v["diameter_mm"] / 2.0
            if worst_edge is None or clear < worst_edge[0]:
                worst_edge = (clear, f"via {v['net']} @ {v['pos_mm']}")
            if clear < limit:
                breaches.append((v["net"], round(clear, 4)))
        if worst_edge:
            r.metrics["min_copper_to_edge_mm"] = round(worst_edge[0], 4)
            r.metrics["min_copper_to_edge_at"] = worst_edge[1]
        if breaches:
            r.fail("COPPER_TO_EDGE",
                   f"{len(breaches)} copper feature(s) closer than {limit} mm to the "
                   f"board outline.",
                   count=len(breaches), limit_mm=limit,
                   worst=sorted(breaches, key=lambda b: b[1])[:10])

    # ---- NPTH -----------------------------------------------------------
    npth = [p for p in model["pads"] if p["attr"] == "npth"]
    small_npth = [p for p in npth if max(p["drill_mm"]) < JLC["min_npth_mm"]]
    r.metrics["npth_count"] = len(npth)
    if small_npth:
        r.fail("NPTH_TOO_SMALL",
               f"{len(small_npth)} non-plated hole(s) below {JLC['min_npth_mm']} mm.",
               count=len(small_npth))

    # ---- silkscreen ------------------------------------------------------
    silk = model.get("silkscreen", [])
    strokes = [s["stroke_mm"] for s in silk if s.get("stroke_mm", 0) > 0]
    if strokes:
        r.metrics["min_silk_stroke_mm"] = round(min(strokes), 4)
        thin = [s for s in strokes if s < JLC["silk_line_mm"] - 1e-9]
        if thin:
            r.warn("SILK_LINE_THIN",
                   f"{len(thin)} silkscreen stroke(s) below {JLC['silk_line_mm']} mm "
                   f"(thinnest {min(thin)} mm); these may not render.",
                   count=len(thin), min_mm=round(min(thin), 4))
    zero = [s for s in silk if s.get("stroke_mm", None) == 0.0]
    if zero:
        r.info("SILK_DEFAULT_STROKE",
               f"{len(zero)} silkscreen item(s) use the board default stroke width "
               f"rather than an explicit one.",
               count=len(zero))
    heights = [s["height_mm"] for s in silk if s.get("height_mm")]
    if heights:
        r.metrics["min_silk_text_mm"] = round(min(heights), 3)
        small = [h for h in heights if h < JLC["silk_text_height_mm"] - 1e-9]
        if small:
            r.warn("SILK_TEXT_SMALL",
                   f"{len(small)} silkscreen text item(s) below "
                   f"{JLC['silk_text_height_mm']} mm.",
                   count=len(small))


@gate(
    "G02",
    "Electrical clearance (IPC-2221B)",
    "Every net class enforces at least the IPC-2221B Table 6-1 clearance for the "
    "worst-case peak potential across the gap, and at least the fabricator's "
    "etch minimum.",
    sources=[IPC2221_SRC, JLC_SRC],
)
def g02_clearance(model, ctx, r):
    project = model.get("project", {})
    classes = project.get("netclasses", [])
    rules = project.get("design_rules", {})

    worst_v = di.MAX_CONDUCTOR_DELTA_V
    need_internal = ipc2221_clearance_mm(worst_v, internal=True)
    need_external_coated = ipc2221_clearance_mm(worst_v, internal=False, coated=True)
    need_external_bare = ipc2221_clearance_mm(worst_v, internal=False, coated=False)
    floor = max(need_internal, need_external_coated, JLC["min_clearance_mm"])

    r.metrics["worst_case_delta_v"] = worst_v
    r.metrics["ipc2221_required_mm"] = {
        "internal_B1": need_internal,
        "external_coated_B4": need_external_coated,
        "external_uncoated_B2": need_external_bare,
    }
    r.metrics["governing_minimum_mm"] = round(floor, 4)
    r.assume(
        "Worst-case conductor pair is VPOS (+15 V) against VNEG (-15 V) = 30 V peak; "
        "no mains or high-voltage net is present."
    )
    r.assume(
        "Soldermask is treated as a permanent polymer coating (IPC-2221B column B4) "
        "for external layers; exposed pads and test points fall back to B2."
    )

    global_clearance = rules.get("min_clearance")
    if global_clearance is not None:
        r.metrics["board_min_clearance_rule_mm"] = global_clearance
        if global_clearance < floor - 1e-9:
            r.fail("GLOBAL_CLEARANCE_LOW",
                   f"Board minimum clearance {global_clearance} mm is below the "
                   f"governing {floor:.3f} mm.",
                   rule_mm=global_clearance, required_mm=floor)

    for nc in classes:
        name = nc.get("name")
        clearance = nc.get("clearance")
        if clearance is None:
            continue
        if clearance < JLC["min_clearance_mm"] - 1e-9:
            r.fail("NETCLASS_BELOW_PROCESS",
                   f"Net class '{name}' clearance {clearance} mm is below the "
                   f"{JLC['min_clearance_mm']} mm etch minimum.",
                   netclass=name, clearance_mm=clearance)
        elif clearance < need_external_bare - 1e-9:
            r.info("NETCLASS_RELIES_ON_MASK",
                   f"Net class '{name}' clearance {clearance} mm is below the "
                   f"{need_external_bare} mm uncoated figure, so it depends on "
                   f"continuous soldermask over those gaps.",
                   netclass=name, clearance_mm=clearance,
                   uncoated_required_mm=need_external_bare)
    r.metrics["netclass_clearances_mm"] = {
        nc.get("name"): nc.get("clearance") for nc in classes
    }


@gate(
    "G03",
    "Plated-hole geometry (IPC-6012)",
    "Annular ring meets IPC-6012 Class 2 and the fabricator minimum; drill "
    "aspect ratio stays inside the plating window.",
    sources=[IPC6012_SRC, JLC_SRC],
)
def g03_hole_geometry(model, ctx, r):
    thickness = model["stackup"]["board_thickness_mm"]
    r.metrics["board_thickness_mm"] = thickness

    worst_ar = None
    ar_warn, ar_fail = [], []
    for v in model["vias"]:
        if v["drill_mm"] <= 0:
            continue
        ar = thickness / v["drill_mm"]
        if worst_ar is None or ar > worst_ar[0]:
            worst_ar = (ar, v["drill_mm"])
        if ar >= ASPECT_RATIO_FAIL:
            ar_fail.append((v["drill_mm"], round(ar, 2)))
        elif ar >= ASPECT_RATIO_WARN:
            ar_warn.append((v["drill_mm"], round(ar, 2)))
    if worst_ar:
        r.metrics["worst_via_aspect_ratio"] = round(worst_ar[0], 2)
        r.metrics["worst_via_aspect_drill_mm"] = worst_ar[1]
    if ar_fail:
        r.fail("ASPECT_RATIO", f"{len(ar_fail)} via(s) exceed {ASPECT_RATIO_FAIL}:1 "
                               f"aspect ratio.", count=len(ar_fail))
    elif ar_warn:
        drills = Counter(d for d, _ in ar_warn)
        r.warn("ASPECT_RATIO_TIGHT",
               f"{len(ar_warn)} via(s) sit at or above {ASPECT_RATIO_WARN}:1 aspect "
               f"ratio ({thickness} mm board). Barrel plating thickness must be "
               f"confirmed with the fabricator.",
               count=len(ar_warn), drills_mm={str(k): v for k, v in drills.items()},
               worst=round(worst_ar[0], 2))

    # Via annular ring.
    worst_ring = None
    ring_fail = []
    for v in model["vias"]:
        ring = (v["diameter_mm"] - v["drill_mm"]) / 2.0
        if worst_ring is None or ring < worst_ring[0]:
            worst_ring = (ring, v["diameter_mm"], v["drill_mm"])
        if ring < IPC6012_CLASS2_ANNULAR_MM - 1e-9:
            ring_fail.append((v["diameter_mm"], v["drill_mm"], round(ring, 4)))
    if worst_ring:
        r.metrics["min_via_annular_ring_mm"] = round(worst_ring[0], 4)
    if ring_fail:
        r.fail("VIA_ANNULAR_RING",
               f"{len(ring_fail)} via(s) below the IPC-6012 Class 2 annular ring of "
               f"{IPC6012_CLASS2_ANNULAR_MM} mm.", count=len(ring_fail))

    # Through-hole pad annular ring.
    pth_rings = []
    for p in model["pads"]:
        if p["attr"] != "pth":
            continue
        drill = max(p["drill_mm"])
        if drill <= 0:
            continue
        # Measured per axis in the pad's own frame: a slotted pad's land and
        # its slot share an orientation, so mixing axes invents a negative ring.
        ring = geom.pad_annular_ring_mm(p)
        if ring is None:
            continue
        pth_rings.append((p["ref"] + "." + p["pad"], round(ring, 4),
                          p["drill_mm"], p["size_mm"]))
    if pth_rings:
        worst = min(pth_rings, key=lambda x: x[1])
        r.metrics["min_pth_annular_ring_mm"] = worst[1]
        r.metrics["min_pth_annular_at"] = worst[0]
        bad = [p for p in pth_rings if p[1] < JLC["min_pth_annular_mm"] - 1e-9]
        tight = [p for p in pth_rings
                 if JLC["min_pth_annular_mm"] - 1e-9 <= p[1] < JLC["preferred_pth_annular_mm"]]
        if bad:
            r.fail("PTH_ANNULAR_RING",
                   f"{len(bad)} through-hole pad(s) below the {JLC['min_pth_annular_mm']} mm "
                   f"annular minimum.", count=len(bad), worst=bad[:10])
        elif tight:
            r.info("PTH_ANNULAR_TIGHT",
                   f"{len(tight)} through-hole pad(s) are between the minimum and the "
                   f"{JLC['preferred_pth_annular_mm']} mm recommended annular ring.",
                   count=len(tight))


@gate(
    "G04",
    "Assembly geometry (IPC-7351B)",
    "Component courtyards do not overlap and nothing intrudes on the board edge "
    "keepout.",
    sources=[IPC7351_SRC],
)
def g04_assembly(model, ctx, r):
    placed = [f for f in model["footprints"]
              if not f["exclude_from_pos"] and f["courtyard"]]
    r.metrics["footprints_total"] = len(model["footprints"])
    r.metrics["footprints_with_courtyard"] = len(placed)

    missing = [f["ref"] for f in model["footprints"]
               if not f["courtyard"] and not f["exclude_from_pos"]]
    if missing:
        r.warn("NO_COURTYARD",
               f"{len(missing)} placed footprint(s) have no courtyard, so their "
               f"spacing cannot be verified.",
               count=len(missing), sample=sorted(missing)[:15])

    boxes = []
    for f in placed:
        pts = [p for ring in f["courtyard"].values() for poly in ring for p in poly]
        if not pts:
            continue
        boxes.append((f["ref"], f["layer"], geom.polygon_bbox(pts)))

    idx = geom.GridIndex(5.0)
    for item in boxes:
        idx.insert(item[2], item)

    overlaps = {}
    for ref, layer, bb in boxes:
        for oref, olayer, obb in idx.query(bb, 0.0):
            if oref == ref or olayer != layer:
                continue
            area = geom.bbox_overlap_area(bb, obb)
            if area > 0.01:
                key = tuple(sorted((ref, oref)))
                overlaps[key] = max(overlaps.get(key, 0.0), round(area, 4))
    r.metrics["courtyard_overlap_pairs"] = len(overlaps)
    if overlaps:
        worst = sorted(overlaps.items(), key=lambda kv: -kv[1])[:15]
        r.fail("COURTYARD_OVERLAP",
               f"{len(overlaps)} component pair(s) have overlapping courtyards.",
               count=len(overlaps),
               worst=[{"pair": list(k), "area_mm2": v} for k, v in worst])


@gate(
    "G05",
    "Fabrication documentation",
    "The board carries the data a fabricator needs to build it to spec: a defined "
    "stackup, an impedance specification for any controlled-impedance net class, "
    "and a readable legend.",
    sources=[JLC_SRC, "IPC-2581 / IPC-D-325 fabrication data requirements"],
)
def g05_documentation(model, ctx, r):
    stack = model["stackup"]
    project = model.get("project", {})
    layer_count = model["copper_layer_count"]
    r.metrics["copper_layers"] = [l["name"] for l in model["copper_layers"]]
    r.metrics["copper_layer_count"] = layer_count
    r.metrics["stackup_defined"] = bool(stack.get("defined")) or bool(project.get("stackup"))

    if not r.metrics["stackup_defined"]:
        r.fail(
            "NO_STACKUP",
            f"No physical stackup is defined for this {layer_count}-layer board. "
            f"Dielectric heights, copper weights and the impedance build are left "
            f"to the fabricator, so no controlled-impedance target can be held and "
            f"the inner-layer copper weight that the ampacity and IR-drop results "
            f"depend on is unconfirmed.",
            layer_count=layer_count,
        )

    classes = {c.get("name"): c for c in project.get("netclasses", [])}
    patterns = project.get("netclass_patterns", [])
    diff_classes = {p.get("netclass") for p in patterns
                    if p.get("netclass") in classes
                    and classes[p["netclass"]].get("diff_pair_width")}
    impedance_classes = sorted(
        n for n in diff_classes
        if n and n.lower() not in ("default",)
    )
    r.metrics["differential_netclasses"] = impedance_classes
    if impedance_classes and not r.metrics["stackup_defined"]:
        r.fail("IMPEDANCE_UNSPECIFIABLE",
               f"Net class(es) {impedance_classes} are routed as differential pairs "
               f"but no stackup exists to specify their impedance to the fabricator.",
               netclasses=impedance_classes)

    # Legend / reference designators.
    silk_text = [s for s in model.get("silkscreen", []) if s.get("text")]
    r.metrics["silkscreen_text_items"] = len(silk_text)
    r.metrics["silkscreen_items"] = len(model.get("silkscreen", []))
    if not silk_text:
        r.warn("NO_SILK_REFDES",
               "No reference designators are printed on the silkscreen. The "
               "assembled board cannot be inspected, reworked or serviced against "
               "the schematic without a separate assembly drawing.",
               silkscreen_items=len(model.get("silkscreen", [])))

    # Fiducials: required for automated assembly.
    fids = [f for f in model["footprints"]
            if "fiducial" in (f["library"] or "").lower()
            or "fid" in (f["ref"] or "").lower()[:3]]
    r.metrics["fiducial_candidates"] = [f["ref"] for f in fids]
    if len(fids) < 3:
        r.warn("FIDUCIALS",
               f"Found {len(fids)} fiducial(s). Automated optical placement "
               f"normally expects three global fiducials on the board or its panel "
               f"rails.",
               count=len(fids))


@gate(
    "G06",
    "Drill-to-copper clearance",
    "Every drilled hole keeps the fabricator's minimum clearance to copper it "
    "is not connected to, so the drill tolerance cannot break out into a "
    "neighbouring net.",
    sources=[JLC_SRC, IPC6012_SRC],
)
def g06_hole_to_copper(model, ctx, r):
    limit = JLC["pth_hole_to_track_min_mm"]
    preferred = JLC["pth_hole_to_track_preferred_mm"]
    r.metrics["hole_to_copper_limit_mm"] = limit
    r.assume(
        "Drill and copper are compared at their drawn positions; the "
        "fabricator's drill registration tolerance is additional to this gap."
    )

    holes = []
    for p in model["pads"]:
        slot = geom.drill_slot(p)
        if slot is None:
            continue
        holes.append({
            "id": f"{p['ref']}.{p['pad']}",
            "slot": slot,
            "net": p["net"],
            "layers": p.get("on_copper") or [],
            "npth": p["attr"] == "npth",
        })
    for v in model["vias"]:
        if v["drill_mm"] <= 0:
            continue
        pseudo = {"pos_mm": v["pos_mm"], "drill_mm": [v["drill_mm"], v["drill_mm"]],
                  "orientation_deg": 0.0}
        holes.append({
            "id": f"via@{v['pos_mm']}",
            "slot": geom.drill_slot(pseudo),
            "net": v["net"],
            "layers": None,          # through via: every copper layer
            "npth": False,
        })

    pad_idx = defaultdict(lambda: geom.GridIndex(2.0))
    for p in model["pads"]:
        x, y = p["pos_mm"]
        hx, hy = p["size_mm"][0] / 2.0, p["size_mm"][1] / 2.0
        reach = math.hypot(hx, hy)
        for layer in p.get("on_copper") or []:
            pad_idx[layer].insert((x - reach, y - reach, x + reach, y + reach), p)

    track_idx = defaultdict(lambda: geom.GridIndex(2.0))
    for t in model["tracks"]:
        x1, y1 = t["start_mm"]
        x2, y2 = t["end_mm"]
        half = t["width_mm"] / 2.0
        track_idx[t["layer"]].insert(
            (min(x1, x2) - half, min(y1, y2) - half,
             max(x1, x2) + half, max(y1, y2) + half), t)

    all_layers = [l["name"] for l in model["copper_layers"]]
    breaches, tight = {}, {}
    worst = None

    for h in holes:
        p1, p2, rad = h["slot"]
        layers = h["layers"] if h["layers"] else all_layers
        # An unplated hole carries no net, so all copper is foreign to it.
        hnet = None if h["npth"] else (h["net"] or None)
        bx1, bx2 = sorted((p1[0], p2[0]))
        by1, by2 = sorted((p1[1], p2[1]))
        probe = (bx1 - rad, by1 - rad, bx2 + rad, by2 + rad)

        for layer in layers:
            for pad in pad_idx[layer].query(probe, preferred + 0.2):
                if hnet is not None and pad["net"] == hnet:
                    continue
                if f"{pad['ref']}.{pad['pad']}" == h["id"]:
                    continue
                gap = geom.seg_pad_distance(p1, p2, pad) - rad
                _record_hole_gap(h, f"{pad['ref']}.{pad['pad']}", layer, gap,
                                 limit, preferred, breaches, tight)
                if worst is None or gap < worst[0]:
                    worst = (gap, h["id"], f"{pad['ref']}.{pad['pad']}", layer)

            for t in track_idx[layer].query(probe, preferred + 0.2):
                if hnet is not None and t["net"] == hnet:
                    continue
                gap = (geom.seg_seg_distance(p1, p2, t["start_mm"], t["end_mm"])
                       - rad - t["width_mm"] / 2.0)
                _record_hole_gap(h, f"track[{t['net']}]", layer, gap,
                                 limit, preferred, breaches, tight)
                if worst is None or gap < worst[0]:
                    worst = (gap, h["id"], f"track[{t['net']}]", layer)

    if worst:
        r.metrics["min_hole_to_copper_mm"] = round(worst[0], 4)
        r.metrics["min_hole_to_copper_between"] = [worst[1], worst[2], worst[3]]

    if breaches:
        sample = sorted(breaches.items(), key=lambda kv: kv[1][0])[:12]
        r.fail("HOLE_TO_COPPER",
               f"{len(breaches)} hole/copper pair(s) are closer than the "
               f"{limit} mm drill-to-copper minimum; the drill can break out "
               f"into copper it is not connected to.",
               count=len(breaches), limit_mm=limit,
               worst=[{"hole": k[0], "copper": k[1], "layer": k[2],
                       "gap_mm": v[0]} for k, v in sample])
    elif tight:
        r.warn("HOLE_TO_COPPER_TIGHT",
               f"{len(tight)} hole/copper pair(s) sit between the {limit} mm "
               f"minimum and the {preferred} mm recommended clearance.",
               count=len(tight))


def _record_hole_gap(hole, other_id, layer, gap, limit, preferred, breaches, tight):
    key = (hole["id"], other_id, layer)
    if gap < limit - 1e-6:
        prev = breaches.get(key)
        if prev is None or gap < prev[0]:
            breaches[key] = (round(gap, 4), limit)
    elif gap < preferred - 1e-6:
        prev = tight.get(key)
        if prev is None or gap < prev[0]:
            tight[key] = (round(gap, 4), preferred)
