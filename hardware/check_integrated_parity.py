#!/usr/bin/env python3
"""KiCad DRC with schematic parity for the integrated board (layout review D3).

The board's project name has no schematic of its own, so the board, its rules and project file are
copied next to the captured schematic (DAC_HPA.kicad_sch and sheets) in a scratch directory under
the DAC_HPA name, and kicad-cli runs `pcb drc --schematic-parity` there. Fails on any violation,
unconnected item or parity issue.

Layout review v1.1 OD-14d: the board gives every BOM footprint an SMD/THT type, while the shared
library copies stay untyped for the frozen study boards. The scratch library copies get the board's
type (only where the library has none), so KiCad's library comparison still checks everything else.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = "DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY"
MAC_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"


def type_library_copies(work: Path) -> int:
    board = (work / "DAC_HPA.kicad_pcb").read_text()
    kinds: dict[str, set[str]] = {}
    for block in re.finditer(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', board, re.S):
        attr = re.search(r'\n\t\t\(attr ([^)]*)\)', block.group(2))
        kind = next((k for k in ("smd", "through_hole") if attr and k in attr.group(1).split()), None)
        if kind:
            kinds.setdefault(block.group(1), set()).add(kind)
    typed = 0
    for fpid, kind in sorted(kinds.items()):
        if len(kind) != 1:
            raise SystemExit(f"{fpid}: board copies disagree on the footprint type {kind}")
        nickname, name = fpid.split(":", 1)
        if nickname not in ("DAC_HPA", "JLC_Imported"):   # KiCad stock libraries are typed already
            continue
        path = work / f"{nickname}.pretty" / f"{name}.kicad_mod"
        text = path.read_text()
        attr = re.search(r'\n\s*\(attr([^)]*)\)', text)
        if attr and {"smd", "through_hole"} & set(attr.group(1).split()):
            continue
        line = f"\n  (attr {kind.pop()}{attr.group(1) if attr else ''})"
        text = text.replace(attr.group(0), line) if attr else re.sub(r'(\n\s*\(layer "F\.Cu"\))', lambda m: m.group(1) + line, text, count=1)
        path.write_text(text)
        typed += 1
    return typed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "INTEGRATED_AUDIO_DRC_PARITY.json")
    args = parser.parse_args()
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or MAC_CLI
    with tempfile.TemporaryDirectory(prefix="dac-hpa-parity-") as scratch:
        work = Path(scratch)
        for path in [*HERE.glob("*.kicad_sch"), HERE / "DAC_HPA.kicad_sym", HERE / "sym-lib-table", HERE / "fp-lib-table"]:
            shutil.copy(path, work / path.name)
        for lib in ("DAC_HPA.pretty", "JLC_Imported.pretty"):
            shutil.copytree(HERE / lib, work / lib)
        for ext in ("kicad_pcb", "kicad_dru", "kicad_pro"):
            shutil.copy(HERE / f"{BOARD}.{ext}", work / f"DAC_HPA.{ext}")
        typed = type_library_copies(work)
        report = work / "drc.json"
        subprocess.run([cli, "pcb", "drc", "--schematic-parity", "--format", "json", "--severity-error",
                        "--severity-warning", "-o", str(report), str(work / "DAC_HPA.kicad_pcb")],
                       check=True, capture_output=True)
        drc = json.loads(report.read_text())
    result = {
        "board": f"{BOARD}.kicad_pcb",
        "schematic": "DAC_HPA.kicad_sch",
        "kicad_version": drc.get("kicad_version"),
        "violations": len(drc["violations"]),
        "unconnected_items": len(drc["unconnected_items"]),
        "schematic_parity_issues": len(drc["schematic_parity"]),
        "library_footprints_typed_in_scratch_copy": typed,
        "first_items": [v["description"] for v in (drc["violations"] + drc["schematic_parity"])[:20]],
    }
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if result["violations"] or result["unconnected_items"] or result["schematic_parity_issues"]:
        raise SystemExit(f"DRC/parity not clean: {result}")
    print(f"PASS: 0 DRC violations, 0 unconnected, 0 schematic parity issues ({result['kicad_version']})")


if __name__ == "__main__":
    main()
