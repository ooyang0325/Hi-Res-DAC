#!/usr/bin/env python3
"""Reconcile the captured 3V3M capacitor inventory with the attach-charge budget.

This is a conservative planning screen, not a USB-IF attach-current test. The
upper charge estimate assumes that the fitted X5R/X7R capacitance does not
exceed its zero-bias tolerance/temperature bound during the voltage ramp.
The D102 capacitance and separation of the two attach regions are assumptions
that still need measurement.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from generate_schematic import read_design


HERE = Path(__file__).resolve().parent
EXPECTED_3V3M_CAPS = {
    *(f"C{number}" for number in range(203, 211)),
    "C211", "C221", "C502", "C515", "C628", "C667",
}
CAPACITOR_TOLERANCE = {"C211": 0.20}  # Samsung CL05A225MQ5NSNC: M = +/-20%.
DEFAULT_TOLERANCE = 0.10  # K-coded fitted capacitors.
TEMPERATURE_FACTOR = 1.15  # Planning allowance for X5R/X7R temperature rise.
VBUS_MAX_V = 5.50
V3V3M_MAX_V = 3.343
D102_ASSUMED_CAP_F = 10e-9
REGION_A_LIMIT_C = 50e-6


def farads(value: str) -> float:
    match = re.fullmatch(r"([0-9.]+)\s*([pnu\u00b5])F", value)
    if not match:
        raise ValueError(f"Cannot parse capacitor value {value!r}")
    multiplier = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "\u00b5": 1e-6}[match.group(2)]
    return float(match.group(1)) * multiplier


def check() -> dict:
    parts, pins, _ = read_design()
    rail_caps = {
        ref: part for ref, part in parts.items()
        if ref.startswith("C") and any(pin.net == "3V3M" for pin in pins[ref])
    }
    if set(rail_caps) != EXPECTED_3V3M_CAPS:
        raise AssertionError(
            f"3V3M capacitor inventory changed: "
            f"missing={sorted(EXPECTED_3V3M_CAPS - set(rail_caps))}, "
            f"extra={sorted(set(rail_caps) - EXPECTED_3V3M_CAPS)}"
        )
    inventory = []
    for ref in sorted(rail_caps, key=lambda item: int(item[1:])):
        part = rail_caps[ref]
        nominal = farads(part.value)
        tolerance = CAPACITOR_TOLERANCE.get(ref, DEFAULT_TOLERANCE)
        inventory.append({
            "ref": ref,
            "value": part.value,
            "nominal_uF": round(nominal * 1e6, 4),
            "upper_zero_bias_uF": round(nominal * (1 + tolerance) * TEMPERATURE_FACTOR * 1e6, 5),
            "tolerance_plus_fraction": tolerance,
        })
    nominal_f = sum(farads(part.value) for part in rail_caps.values())
    upper_f = sum(
        farads(part.value)
        * (1 + CAPACITOR_TOLERANCE.get(ref, DEFAULT_TOLERANCE))
        * TEMPERATURE_FACTOR
        for ref, part in rail_caps.items()
    )
    c102_nominal_f = farads(parts["C102"].value)
    if parts["C102"].value != "2.2 \u00b5F":
        raise AssertionError("C102 attach-region value changed")
    c102_upper_f = c102_nominal_f * (1 + DEFAULT_TOLERANCE) * TEMPERATURE_FACTOR
    charge_c = (
        upper_f * V3V3M_MAX_V
        + c102_upper_f * VBUS_MAX_V
        + D102_ASSUMED_CAP_F * VBUS_MAX_V
    )
    result = {
        "source": "captured schematic: Parts List v0.9 plus asserted functional ECO",
        "3v3m_capacitors": inventory,
        "3v3m_nominal_uF": round(nominal_f * 1e6, 4),
        "3v3m_upper_zero_bias_uF": round(upper_f * 1e6, 5),
        "c102_upper_zero_bias_uF": round(c102_upper_f * 1e6, 5),
        "region_a_charge_no_load_credit_uC": round(charge_c * 1e6, 4),
        "region_a_limit_uC": REGION_A_LIMIT_C * 1e6,
        "nominal_margin_uC": round((REGION_A_LIMIT_C - charge_c) * 1e6, 4),
        "qualification": "HOLD: verify C(V,T), U502 output-cap stability, D102 C, and measured region separation/inrush",
    }
    if charge_c >= REGION_A_LIMIT_C:
        raise AssertionError(f"Region A planning bound exceeds 50 uC: {charge_c * 1e6:.3f} uC")
    return result


if __name__ == "__main__":
    result = check()
    (HERE / "ATTACH_CHARGE_RECONCILIATION.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
