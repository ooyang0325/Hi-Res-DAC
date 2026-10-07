"""Run the sign-off gate suite against an extracted board model.

Usage (from the repository root)::

    python -m hardware.signoff.run --model hardware/signoff/out/model_integrated.json

The runner owns three jobs:

1. build the analysis context (layer stack, rail sources, LTspice path),
2. execute every registered gate in isolation so one broken gate cannot
   hide the rest,
3. emit a machine-readable JSON result and a human-readable Markdown
   report, then set the process exit code from the worst gate status.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
import traceback
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
if __package__ in (None, ""):  # allow `python run.py`
    sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))
    __package__ = "hardware.signoff"

from . import design_intent as di
from .framework import FAIL, INFO, PASS, SKIP, WARN, GateResult, registered
from .netgraph import LayerStack

GATE_MODULES = [
    "gates_fab",
    "gates_power",
    "gates_signal",
    "gates_audio",
    "gates_spice",
]

_STATUS_RANK = {PASS: 0, INFO: 1, SKIP: 1, WARN: 2, FAIL: 3}
_BADGE = {PASS: "PASS", INFO: "INFO", SKIP: "SKIP", WARN: "WARN", FAIL: "FAIL"}


def load_gate_modules():
    """Import every gate module that exists, reporting import failures."""
    loaded, failed = [], []
    for name in GATE_MODULES:
        path = os.path.join(_HERE, name + ".py")
        if not os.path.exists(path):
            continue
        try:
            importlib.import_module("." + name, __package__)
            loaded.append(name)
        except Exception as exc:  # pragma: no cover - surfaced in the report
            failed.append((name, "".join(traceback.format_exception_only(type(exc), exc)).strip()))
    return loaded, failed


def infer_rail_sources(model):
    """Guess which component regulates each rail.

    A rail source is a component that has pads on the rail *and* on a
    different power net: that is what a regulator, ferrite or charge pump
    looks like in the netlist.  Pure loads only touch one rail, so they are
    never selected.  The guess is reported in the context dump so a reviewer
    can override it.
    """
    rails = set(di.RAILS) - {"GND"}
    nets_by_ref = defaultdict(set)
    for pad in model["pads"]:
        net = pad.get("net")
        if net:
            nets_by_ref[pad["ref"]].add(net)

    pin_count = defaultdict(int)
    for pad in model["pads"]:
        pin_count[pad["ref"]] += 1

    sources, evidence = {}, {}
    for rail in rails:
        best, best_score = None, -1
        for ref, nets in nets_by_ref.items():
            if rail not in nets:
                continue
            other_rails = (nets & rails) - {rail}
            if not other_rails:
                continue
            # Prefer ICs over passives, then the part bridging the most rails.
            score = len(other_rails) * 10 + pin_count[ref]
            if ref.startswith("U"):
                score += 100
            if score > best_score:
                best, best_score = ref, score
        if best:
            sources[rail] = best
            evidence[rail] = sorted(nets_by_ref[best])
    return sources, evidence


def build_stack(model):
    """Build the layer stack, honouring an explicit stackup when present."""
    names = [l["name"] for l in model["copper_layers"]]
    stackup = model.get("stackup") or {}
    thickness = stackup.get("board_thickness_mm") or 1.6
    outer_oz = stackup.get("outer_copper_oz")
    inner_oz = stackup.get("inner_copper_oz")
    copper = [row for row in stackup.get("layers", []) if row.get("type") == "copper"]
    if stackup.get("defined") and len(copper) >= 2 and all(r.get("thickness_mm") for r in copper):
        # 1 oz = 0.0347 mm; outer from F.Cu, inner from the first internal layer.
        outer_oz = round(copper[0]["thickness_mm"] / 0.0347, 3)
        inner_oz = round(copper[1]["thickness_mm"] / 0.0347, 3) if len(copper) > 2 else outer_oz
    assumed = outer_oz is None or inner_oz is None
    return LayerStack(
        names,
        board_thickness_mm=thickness,
        outer_oz=outer_oz or 1.0,
        inner_oz=inner_oz or 0.5,
        assumed=assumed,
    )


def run_gates(model, ctx, only=None):
    results = []
    for spec in registered():
        if only and spec["id"] not in only:
            continue
        res = GateResult(
            gate_id=spec["id"],
            title=spec["title"],
            criterion=spec["criterion"],
            sources=list(spec["sources"]),
        )
        started = time.time()
        try:
            spec["fn"](model, ctx, res)
        except Exception:
            res.status = FAIL
            res.error = traceback.format_exc(limit=8)
            res.add(FAIL, "GATE_ERROR",
                    f"Gate {spec['id']} raised an exception and did not evaluate.")
        res.metrics.setdefault("_runtime_s", round(time.time() - started, 3))
        results.append(res)
    return results


def worst_status(results):
    worst = PASS
    for r in results:
        if _STATUS_RANK[r.status] > _STATUS_RANK[worst]:
            worst = r.status
    return worst


def render_markdown(model, ctx, results, import_failures):
    lines = []
    lines.append("# Independent layout sign-off report")
    lines.append("")
    lines.append(f"- Board: `{model['source']}`")
    lines.append(f"- Extracted with KiCad {model.get('kicad_version', '?')}")
    lines.append(f"- Copper layers: {model['copper_layer_count']} "
                 f"({', '.join(l['name'] for l in model['copper_layers'])})")
    lines.append(f"- Footprints {len(model['footprints'])}, pads {len(model['pads'])}, "
                 f"tracks {len(model['tracks'])}, vias {len(model['vias'])}, "
                 f"nets {len(model['nets'])}")
    stack = ctx["stack"]
    lines.append(f"- Layer stack: {'ASSUMED' if stack.assumed else 'from stackup'} "
                 f"({stack.board_thickness_mm} mm board)")
    lines.append("")

    counts = defaultdict(int)
    for r in results:
        counts[r.status] += 1
    verdict = worst_status(results)
    lines.append(f"## Verdict: {_BADGE[verdict]}")
    lines.append("")
    lines.append(f"{counts[FAIL]} gate(s) FAIL, {counts[WARN]} WARN, "
                 f"{counts[PASS]} PASS, {counts[INFO] + counts[SKIP]} informational.")
    lines.append("")

    if import_failures:
        lines.append("### Gate modules that failed to import")
        lines.append("")
        for name, err in import_failures:
            lines.append(f"- `{name}`: {err}")
        lines.append("")

    lines.append("## Gate summary")
    lines.append("")
    lines.append("| Gate | Status | Title | FAIL | WARN |")
    lines.append("| --- | --- | --- | ---: | ---: |")
    for r in results:
        c = r.counts()
        lines.append(f"| {r.gate_id} | **{_BADGE[r.status]}** | {r.title} "
                     f"| {c.get(FAIL, 0)} | {c.get(WARN, 0)} |")
    lines.append("")

    lines.append("## Gate detail")
    lines.append("")
    for r in results:
        lines.append(f"### {r.gate_id} — {r.title} · {_BADGE[r.status]}")
        lines.append("")
        lines.append(f"**Criterion.** {r.criterion}")
        lines.append("")
        if r.sources:
            lines.append("**Sources.** " + "; ".join(r.sources))
            lines.append("")
        if r.assumptions:
            lines.append("**Assumptions.**")
            lines.append("")
            for a in r.assumptions:
                lines.append(f"- {a}")
            lines.append("")
        metrics = {k: v for k, v in r.metrics.items() if not k.startswith("_")}
        if metrics:
            lines.append("**Metrics.**")
            lines.append("")
            for k, v in metrics.items():
                lines.append(f"- `{k}` = {v}")
            lines.append("")
        if r.error:
            lines.append("```")
            lines.append(r.error.strip())
            lines.append("```")
            lines.append("")
        shown = [f for f in r.findings if f.severity in (FAIL, WARN)]
        extra = len(r.findings) - len(shown)
        if shown:
            lines.append("**Findings.**")
            lines.append("")
            for f in shown[:40]:
                lines.append(f"- `{f.severity}` **{f.code}** — {f.message}")
            if len(shown) > 40:
                lines.append(f"- … {len(shown) - 40} more at this severity in the JSON result.")
            lines.append("")
        if extra:
            lines.append(f"_{extra} informational finding(s) in the JSON result._")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=os.path.join(_HERE, "out", "model_integrated.json"))
    ap.add_argument("--outdir", default=os.path.join(_HERE, "out"))
    ap.add_argument("--gate", action="append", default=None,
                    help="Run only these gate ids (repeatable).")
    ap.add_argument("--no-spice", action="store_true",
                    help="Skip gates that shell out to LTspice.")
    ap.add_argument("--ltspice", default=None, help="Path to LTspice.exe")
    args = ap.parse_args(argv)

    with open(args.model, "r", encoding="utf-8-sig") as fh:
        model = json.load(fh)

    loaded, import_failures = load_gate_modules()

    stack = build_stack(model)
    rail_sources, rail_evidence = infer_rail_sources(model)
    ctx = {
        "stack": stack,
        "rail_sources": rail_sources,
        "rail_source_evidence": rail_evidence,
        "outdir": os.path.abspath(args.outdir),
        "spice_dir": os.path.join(os.path.abspath(args.outdir), "spice"),
        "ltspice": args.ltspice or find_ltspice(),
        "enable_spice": not args.no_spice,
        "model_path": os.path.abspath(args.model),
    }
    os.makedirs(ctx["outdir"], exist_ok=True)
    os.makedirs(ctx["spice_dir"], exist_ok=True)

    results = run_gates(model, ctx, only=set(args.gate) if args.gate else None)
    verdict = worst_status(results)

    payload = {
        "board": model["source"],
        "kicad_version": model.get("kicad_version"),
        "verdict": verdict,
        "gate_modules_loaded": loaded,
        "gate_module_import_failures": [
            {"module": n, "error": e} for n, e in import_failures
        ],
        "context": {
            "layer_stack_assumed": stack.assumed,
            "board_thickness_mm": stack.board_thickness_mm,
            "copper_thickness_mm": stack.thickness_mm,
            "rail_sources": rail_sources,
            "rail_source_evidence": rail_evidence,
            "ltspice": ctx["ltspice"],
        },
        "gates": [r.to_dict() for r in results],
    }

    json_path = os.path.join(ctx["outdir"], "signoff_result.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    md_path = os.path.join(ctx["outdir"], "SIGNOFF_REPORT.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(model, ctx, results, import_failures))

    for r in results:
        c = r.counts()
        print(f"{r.gate_id:5s} {_BADGE[r.status]:4s} {r.title[:52]:54s} "
              f"F={c.get(FAIL, 0):<4d} W={c.get(WARN, 0):<4d} {r.metrics.get('_runtime_s')}s")
    print("")
    print(f"VERDICT: {verdict}")
    print(f"JSON:    {json_path}")
    print(f"REPORT:  {md_path}")
    return 1 if verdict == FAIL else 0


def find_ltspice():
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\ADI\LTspice\LTspice.exe"),
        os.path.expandvars(r"%ProgramFiles%\ADI\LTspice\LTspice.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\ADI\LTspice\LTspice.exe"),
        os.path.expandvars(r"%ProgramFiles%\LTC\LTspiceXVII\XVIIx64.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # macOS: LTspice ships as a Wine bottle; ltspice_wine.sh gives it the LTspice.exe CLI.
    if os.path.exists("/Applications/LTspice.app/Contents/SharedSupport/ltspice/LTspice/wine"):
        return os.path.join(_HERE, "ltspice_wine.sh")
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
