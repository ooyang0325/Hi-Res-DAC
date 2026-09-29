#!/usr/bin/env python3
"""Compare the captured discharge circuit with the shipped power model.

This audit reports a known release hold. Its RC estimate is a narrow,
no-load illustration, not a shutdown-time guarantee for either regulator.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import zipfile
from pathlib import Path

from generate_schematic import read_source


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "doc/DAC_HPA_Calculation_Package_v1.1.zip"
RAIL_NETS = ("3V3D", "N2_V33_CPLD", "DVCC", "1V3")


def capacitance_uf(value: str) -> float:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([µu]F|nF|pF)\s*", value)
    if not match:
        raise ValueError(f"Unrecognized capacitor value: {value!r}")
    scale = {"µF": 1.0, "uF": 1.0, "nF": 0.001, "pF": 0.000001}
    return float(match.group(1)) * scale[match.group(2)]


def resistance_ohm(value: str) -> float:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*Ω\s*", value)
    if not match:
        raise ValueError(f"Unrecognized discharge resistance: {value!r}")
    return float(match.group(1))


def audit() -> dict:
    parts, pins, _ = read_source()
    by_net = {net: [] for net in RAIL_NETS}
    for ref, pin_group in pins.items():
        if not ref.startswith("C") or len(pin_group) != 2:
            continue
        nets = {pin.net for pin in pin_group}
        for net in RAIL_NETS:
            if nets == {net, "GND"}:
                by_net[net].append((ref, capacitance_uf(parts[ref].value)))

    cap_totals = {net: round(sum(value for _, value in items), 6)
                  for net, items in by_net.items()}
    digital_nominal = sum(cap_totals[net] for net in RAIL_NETS[:3])
    digital_plus_10pct = digital_nominal * 1.1
    v3v3d_high = 3.3 * 1.01
    v3v3a_high = 3.3 * 1.02
    r527_min = resistance_ohm(parts["R527"].value) * 0.99
    r529_min = resistance_ohm(parts["R529"].value) * 0.99
    r530_min = resistance_ohm(parts["R530"].value) * 0.99
    # These assumptions deliberately match c06's simple gate/resistor screen.
    # They omit regulator drive, reverse current, bead impedance and loading.
    illustrative_gate_s = 89e-6
    illustrative_rds_ohm = 0.048 * 1.15
    illustrative_r_ohm = resistance_ohm(parts["R529"].value) * 1.01 + illustrative_rds_ohm
    rc_ms = 1000 * (illustrative_gate_s + illustrative_r_ohm
                    * digital_plus_10pct * 1e-6 * math.log(v3v3d_high / 0.1))
    with zipfile.ZipFile(PACKAGE) as archive:
        c06 = archive.read("calc_package_v11/power/calc/c06_discharge.py").decode()
        c12 = archive.read("calc_package_v11/power/calc/c12_u303_tlv758p.py").decode()
    captured_u303_en = {pin.number: pin.net for pin in pins["U303"]}["3"]
    captured_u504_en = {pin.number: pin.net for pin in pins["U504"]}["4"]
    c06_old_en = "TLV767 and TLV758P both disabled at t = 0 by AUD_EN low" in c06
    c12_old_en = "3 EN = AUD_EN" in c12
    mismatch = captured_u303_en != "AUD_EN" and (c06_old_en or c12_old_en)
    return {
        "release_status": "HOLD" if mismatch else "review",
        "source_workbook": "DAC_HPA_Parts_List_v0.9.xlsx",
        "calculation_package": PACKAGE.name,
        "captured_u303_pin3_en_net": captured_u303_en,
        "captured_u504_pin4_en_net": captured_u504_en,
        "calculation_package_assumes_u303_en_aud_en": {"c06": c06_old_en, "c12": c12_old_en},
        "enable_model_mismatch": mismatch,
        "capacitors_by_net_uf": {
            net: {ref: value for ref, value in sorted(items)}
            for net, items in by_net.items()
        },
        "nominal_capacitance_uf": cap_totals,
        "three_digital_domains_nominal_uf": round(digital_nominal, 6),
        "three_digital_domains_plus_10pct_uf": round(digital_plus_10pct, 6),
        "r529_stored_capacitor_energy_only_uj": round(
            0.5 * digital_plus_10pct * 1e-6 * v3v3d_high**2 * 1e6, 3),
        "r529_initial_power_w_at_high_3v3d_and_minus_1pct_r": round(
            v3v3d_high**2 / r529_min, 3),
        "r527_initial_power_w_at_high_3v3a_and_minus_1pct_r": round(
            v3v3a_high**2 / r527_min, 3),
        "r530_initial_power_w_at_1v3_1p365v_and_minus_1pct_r": round(
            1.365**2 / r530_min, 3),
        "r529_part": {"mpn": parts["R529"].mpn, "package": parts["R529"].package,
                       "rating": parts["R529"].rating_tolerance},
        "r527_part": {"mpn": parts["R527"].mpn, "package": parts["R527"].package,
                       "rating": parts["R527"].rating_tolerance},
        "r530_part": {"mpn": parts["R530"].mpn, "package": parts["R530"].package,
                       "rating": parts["R530"].rating_tolerance},
        "illustrative_3v3d_no_load_rc_to_0p1v_ms": round(rc_ms, 3),
        "illustrative_rc_scope": "Assumes U504 already off, 89 us gate delay, 10% high capacitors, "
                                 "linear 10 ohm plus FET resistance; excludes U303 drive/backfeed, "
                                 "bead dynamics and regulator turn-off delay. Not a guaranteed bound.",
        "qualification_holds": [
            "Rebuild C06/C12 with U303 EN tied to 3V3D and the captured capacitance.",
            "Reconcile Spec 1V3 <=0.134 ms with Notes ~0.76 ms and verify DVDD/DVCC during fault and shutdown.",
            "Qualify R527/R529/R530 pulse and steady power, LDO overlap and JLC assembly footprints.",
        ] if mismatch else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(audit(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
