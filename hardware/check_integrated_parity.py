#!/usr/bin/env python3
"""KiCad DRC with schematic parity for the integrated board (layout review D3).

The board's project name has no schematic of its own, so the board, its rules and project file are
copied next to the captured schematic (DAC_HPA.kicad_sch and sheets) in a scratch directory under
the DAC_HPA name, and kicad-cli runs `pcb drc --schematic-parity` there. Fails on any violation,
unconnected item or parity issue.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = "DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY"
MAC_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"


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
        "first_items": [v["description"] for v in (drc["violations"] + drc["schematic_parity"])[:20]],
    }
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if result["violations"] or result["unconnected_items"] or result["schematic_parity_issues"]:
        raise SystemExit(f"DRC/parity not clean: {result}")
    print(f"PASS: 0 DRC violations, 0 unconnected, 0 schematic parity issues ({result['kicad_version']})")


if __name__ == "__main__":
    main()
