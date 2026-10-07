"""Turn placed geometry into the parasitics a PDN simulation needs.

Every value here is derived from the board: the capacitor's package sets its
ESL, the distance from its pads to the nearest vias sets the mounting
inductance, and the solved copper network sets the series resistance.  Nothing
is assumed about how the part "should" have been placed.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from . import design_intent as di
from . import rules

#: Typical MLCC self-inductance and ESR by package, from the body length.
#: (Murata/TDK characterisation data; the figures are package properties and
#: vary little between vendors.)
PACKAGE_PARASITICS = {
    "0201": {"esl_h": 0.30e-9, "esr_ohm": 0.040},
    "0402": {"esl_h": 0.40e-9, "esr_ohm": 0.030},
    "0603": {"esl_h": 0.55e-9, "esr_ohm": 0.025},
    "0805": {"esl_h": 0.70e-9, "esr_ohm": 0.020},
    "1206": {"esl_h": 1.00e-9, "esr_ohm": 0.015},
    "1210": {"esl_h": 1.20e-9, "esr_ohm": 0.015},
}
DEFAULT_PACKAGE = "0603"

#: Electrolytic / tantalum bulk parts have far higher ESR than an MLCC.
_BULK_ESR_OHM = 0.15
_BULK_THRESHOLD_F = 22e-6

_PKG_RE = re.compile(r"_(\d{4})_", )


def package_of(library: str | None) -> str:
    """Imperial package code from a KiCad library name such as
    ``Capacitor_SMD:C_0402_1005Metric``."""
    if not library:
        return DEFAULT_PACKAGE
    m = _PKG_RE.search(library)
    if m and m.group(1) in PACKAGE_PARASITICS:
        return m.group(1)
    for code in PACKAGE_PARASITICS:
        if code in library:
            return code
    return DEFAULT_PACKAGE


def capacitor_parasitics(library: str | None, farads: float) -> dict:
    pkg = package_of(library)
    data = dict(PACKAGE_PARASITICS.get(pkg, PACKAGE_PARASITICS[DEFAULT_PACKAGE]))
    if farads >= _BULK_THRESHOLD_F:
        data["esr_ohm"] = _BULK_ESR_OHM
    data["package"] = pkg
    return data


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


class ViaIndex:
    """Nearest-via lookup, bucketed by net."""

    def __init__(self, model):
        self._by_net = defaultdict(list)
        for v in model["vias"]:
            self._by_net[v["net"]].append(v)

    def nearest(self, net: str, point, max_mm: float = 3.0):
        best, best_d = None, max_mm
        for v in self._by_net.get(net, ()):
            d = _dist(v["pos_mm"], point)
            if d < best_d:
                best, best_d = v, d
        return best, (best_d if best else None)


def mounting_inductance_h(model, via_index: ViaIndex, pads, plane_height_mm,
                          board_thickness_mm=1.6, return_net="GND"):
    """Loop inductance of one decoupling capacitor's mounting.

    The loop is: signal pad -> its via -> plane -> return via -> ground pad.
    The vias run only as far as the first plane, not through the whole board,
    so ``plane_height_mm`` -- not the board thickness -- sets the via length.
    The surface run from each pad to its via adds a microstrip section over
    that same plane.  Returns ``(inductance_H, detail)``; ``detail`` records
    what was found so a reviewer can see whether the number came from real
    vias or a fallback.
    """
    pwr = [p for p in pads if p["net"] != "GND"]
    gnd = [p for p in pads if p["net"] == "GND"]
    if not pwr or not gnd:
        return None, {"reason": "not a two-terminal power/ground part"}

    vp, dp = via_index.nearest(pwr[0]["net"], pwr[0]["pos_mm"])
    vg, dg = via_index.nearest(return_net, gnd[0]["pos_mm"])
    if vp is None or vg is None:
        # No via within reach: the part is fed by surface copper only, which is
        # a materially worse mounting.  Fall back to the pad-to-pad span as the
        # loop, which understates rather than invents a good result.
        span = _dist(pwr[0]["pos_mm"], gnd[0]["pos_mm"])
        detail = {"vias": False, "pad_span_mm": round(span, 3),
                  "note": "no via within 3 mm of the pad; surface-fed"}
        return rules.trace_inductance_h(span, 0.5, plane_height_mm), detail

    pitch = _dist(vp["pos_mm"], vg["pos_mm"])
    drill = max(min(vp["drill_mm"], vg["drill_mm"]), 0.05)
    l_pair = rules.via_pair_inductance_h(pitch, drill, plane_height_mm)
    l_run = (rules.trace_inductance_h(dp, 0.5, plane_height_mm)
             + rules.trace_inductance_h(dg, 0.5, plane_height_mm))
    detail = {"vias": True, "via_pitch_mm": round(pitch, 3),
              "via_drill_mm": drill,
              "pad_to_via_mm": [round(dp, 3), round(dg, 3)],
              "l_via_pair_nh": round(l_pair * 1e9, 3),
              "l_surface_nh": round(l_run * 1e9, 3)}
    return l_pair + l_run, detail


def decoupling_network(model, rail: str, plane_height_mm: float,
                       include_cross_rail: bool = True):
    """Every capacitor that bypasses ``rail``, with extracted parasitics.

    Capacitors to GND are the obvious case.  A dual-supply analogue stage is
    very often decoupled *rail to rail* instead -- a 100 nF from V+ to V-
    straddling the op-amp -- and ignoring those would wrongly report the stage
    as undecoupled.  Cross-rail parts are returned with ``cross_rail`` set to
    the far rail so the caller can model the extra return path.
    """
    by_ref_pads = defaultdict(list)
    for p in model["pads"]:
        by_ref_pads[p["ref"]].append(p)
    fps = {f["ref"]: f for f in model["footprints"]}
    index = ViaIndex(model)
    rail_names = set(di.RAILS)

    caps = []
    for ref, pads in by_ref_pads.items():
        if not di.is_capacitor(ref):
            continue
        nets = {p["net"] for p in pads}
        if rail not in nets or len(nets) != 2:
            continue
        other = next(iter(nets - {rail}))
        cross = None
        if other != "GND":
            if not include_cross_rail or other not in rail_names:
                continue
            cross = other
        fp = fps.get(ref, {})
        if fp.get("dnp"):
            continue
        farads = di.parse_capacitance(fp.get("value") or "")
        if not farads:
            continue
        par = capacitor_parasitics(fp.get("library"), farads)
        # For a cross-rail part the "return" terminal is the far rail, not
        # GND, so measure the mounting loop against that pad instead.
        loop_pads = pads
        if cross:
            loop_pads = [dict(p, net=("GND" if p["net"] == cross else p["net"]))
                         for p in pads]
        l_mount, detail = mounting_inductance_h(
            model, index, loop_pads, plane_height_mm,
            return_net=(cross or "GND"))
        if l_mount is None:
            continue
        caps.append({
            "ref": ref,
            "farads": farads,
            "package": par["package"],
            "esr_ohm": par["esr_ohm"],
            "esl_h": par["esl_h"],
            "l_mount_h": l_mount,
            "l_total_h": par["esl_h"] + l_mount,
            "pos_mm": fp.get("pos_mm"),
            "cross_rail": cross,
            "mount": detail,
        })
    caps.sort(key=lambda c: -c["farads"])
    return caps
