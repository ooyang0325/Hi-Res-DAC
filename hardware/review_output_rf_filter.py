#!/usr/bin/env python3
"""Review-only OPA1622 switch-model sweep for the proposed output RF filter ECO.

Uses the *unchanged* calibrated model from Calculation Package v1.1. The
R417-R420 0-ohm link (0.05 ohm + 5 nH) is replaced by a ferrite-bead model and a
C0G capacitor is added from LEG to GND, as proposed in EMS_VERIFICATION_2026-09-30.md
(hardware/sim/ems_headphone_rf.cir). Bead models are linear approximations
(DCR + (L || R)); saturation, nonlinearity and hardware THD+N are not assessed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ZIP = HERE.parent / "doc" / "DAC_HPA_Calculation_Package_v1.1.zip"
BASE = "calc_package_v11/analog/"
SWITCH_SHA256 = "f1a371e91fc82faea06ecaa023c0f33d93a29718a3aebb2d5dfad85d55f11c95"
FILES = (
    "scripts/mna_v.py", "scripts/models_v.py", "scripts/stability_switch.py",
    "ds/opa1622_digitized.json", "ds/opa1622_calibrated.json",
)


def study() -> dict:
    import numpy as np

    with tempfile.TemporaryDirectory(prefix="dac-hpa-out-rf-") as temp_name:
        root = Path(temp_name)
        with zipfile.ZipFile(ZIP) as archive:
            for name in FILES:
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(BASE + name))
        source_path = root / "scripts" / "stability_switch.py"
        source = source_path.read_text()
        if hashlib.sha256(source.encode()).hexdigest() != SWITCH_SHA256:
            raise SystemExit("Calculation Package switch model changed; review the sweep before running")
        # Compile only the model/function definitions. The package's full
        # sweep would write its own result file and is outside this comparison.
        source = source.split("lines = [__doc__", 1)[0]
        link = "c.R('OUT', 'lk', 0.05); c.L('lk', 'LEG', 5e-9)"
        assert source.count("drive=False):") == 1 and source.count(link) == 1
        source = source.replace("drive=False):", "drive=False, bead=None, leg_cap=0.0):")
        source = source.replace(link, (
            "if bead is None:\n        " + link + "\n    else:\n"
            "        c.R('OUT', 'b0', bead[0]); c.L('b0', 'b1', 5e-9); c.L('b1', 'LEG', bead[1]); c.R('b1', 'LEG', bead[2])\n"
            "    if leg_cap: c.C('LEG', 'lc', leg_cap); c.L('lc', '0', 1e-9)"))
        sys.path.insert(0, str(root / "scripts"))
        try:
            context = {"__file__": str(source_path), "__name__": "j702_sensitivity"}
            exec(compile(source, str(source_path), "exec"), context)
            build = context["build"]
            margins = context["margins"]
            frequency = context["FR"]
            model = context["OPA1622v"]
            conditions = (
                (16, 1e-9, True), (32, 1e-9, True),
                (300, 1e-9, True), (32, 2e-9, False),
            )
            variants = [("as built: 0 ohm link", None, 0.0)]
            for bname, bead in (("120 ohm bead", (0.05, 190e-9, 180.0)), ("220 ohm bead", (0.10, 350e-9, 300.0)),
                                ("600 ohm bead", (0.30, 1e-6, 600.0))):
                for cap in (47e-12, 100e-12, 220e-12, 470e-12, 1e-9):
                    variants.append((f"{bname} + {cap * 1e12:.0f} pF", bead, cap))
            cases = []
            for name, bead, leg_cap in variants:
                worst = {"phase_margin_deg": 999.0,
                         "gain_margin_db": 999.0, "peak_sensitivity_db": -999.0}
                for load, cable_cap, cable in conditions:
                    for gbw_scale in (0.8, 1.25):
                        opamp = model("CAL", gbw_scale)
                        for ct_scale, lead_delta in ((0.95, -0.5e-12),
                                                     (1.05, 0.5e-12)):
                            circuit = build(
                                load, cable_cap, opamp, cable,
                                ("closed", 0.081, 15e-9),
                                Ct=1.8e-9 * ct_scale,
                                Cl=10e-12 + lead_delta,
                                bead=bead, leg_cap=leg_cap,
                            )
                            result = margins(frequency, circuit.loop_gain(frequency, "U"))
                            worst["phase_margin_deg"] = min(
                                worst["phase_margin_deg"],
                                result["pm_worst"] if result["pm_worst"] is not None else 999.0,
                            )
                            worst["gain_margin_db"] = min(
                                worst["gain_margin_db"],
                                result["gm"] if result["gm"] is not None else 999.0,
                            )
                            worst["peak_sensitivity_db"] = max(
                                worst["peak_sensitivity_db"],
                                20 * math.log10(1 / result["vector_margin"]),
                            )
                cases.append({"variant": name,
                              **{key: round(value, 3) for key, value in worst.items()}})
            return {
                "scope": "Selected closed-switch calibrated-model corners; linear bead + LEG capacitor models only",
                "source_zip": ZIP.name,
                "switch_model_sha256": SWITCH_SHA256,
                "loads_ohm": [16, 32, 300],
                "cable_cap_pf": 1000,
                "stress_32ohm_cap_pf": 2000,
                "results": cases,
            }
        finally:
            sys.path.remove(str(root / "scripts"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(study(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
