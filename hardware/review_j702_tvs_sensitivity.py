#!/usr/bin/env python3
"""Review-only OPA1622 switch-model sweep for a second LP/RP jack TVS.

Uses the *unchanged* calibrated model from Calculation Package v1.1. Only the
linear JACK-to-GND TVS capacitance term is varied. This cannot assess nonlinear
capacitance, ESD clamping, leakage distortion, PCB parasitics, or hardware THD.
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

    with tempfile.TemporaryDirectory(prefix="dac-hpa-j702-esd-") as temp_name:
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
        assert source.count("drive=False):") == 1
        assert source.count("c.C('JACK', '0', 15e-12)") == 1
        source = source.replace("drive=False):", "drive=False, esd_cap=15e-12):")
        source = source.replace("c.C('JACK', '0', 15e-12)",
                                "c.C('JACK', '0', esd_cap)")
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
            cases = []
            for esd_pf in (15, 30, 36):
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
                                esd_cap=esd_pf * 1e-12,
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
                cases.append({"jack_tvs_cap_pf": esd_pf,
                              **{key: round(value, 3) for key, value in worst.items()}})
            return {
                "scope": "Selected closed-switch calibrated-model corners; linear TVS capacitance only",
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
