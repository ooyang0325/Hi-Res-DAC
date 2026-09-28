#!/usr/bin/env python3
"""Check the primary KiCad netclasses and via dimensions used for routing."""

from __future__ import annotations

import json
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
PROJECT = HERE / "DAC_HPA.kicad_pro"
BOARD = HERE / "DAC_HPA.kicad_pcb"


def close(actual: float, target: float) -> bool:
    return abs(actual - target) < 1e-6


def main() -> None:
    project = json.loads(PROJECT.read_text())
    rules = project["board"]["design_settings"]["rules"]
    assert close(rules["min_track_width"], 0.15)
    assert close(rules["min_via_annular_width"], 0.20)
    dimensions = project["board"]["design_settings"]["via_dimensions"]
    assert {(row["diameter"], row["drill"]) for row in dimensions} >= {
        (0.6, 0.2), (0.8, 0.4),
    }
    classes = {row["name"]: row for row in project["net_settings"]["classes"]}
    for name, diameter, drill in (("Default", 0.6, 0.2),
                                  ("USB_DIFF", 0.6, 0.2),
                                  ("FINE_ESCAPE", 0.6, 0.2),
                                  ("POWER", 0.8, 0.4)):
        klass = classes[name]
        assert close(klass["via_diameter"], diameter)
        assert close(klass["via_drill"], drill)
        assert (diameter - drill) / 2 + 1e-6 >= 0.20
    usb = classes["USB_DIFF"]
    assert close(usb["clearance"], 0.15)
    assert close(usb["track_width"], 0.235)
    assert close(usb["diff_pair_width"], 0.235)
    assert close(usb["diff_pair_gap"], 0.15)
    assert close(classes["FINE_ESCAPE"]["track_width"], 0.15)
    board = pcbnew.LoadBoard(str(BOARD))
    expected = {
        "USB_DP": "USB_DIFF", "USB_DN": "USB_DIFF",
        "VBUS": "POWER", "5V_SYS": "POWER", "5V_ANA": "POWER",
        "JACK_LP": "AUDIO_OUTPUT", "JACK_RP": "AUDIO_OUTPUT",
        "LEG_LP": "AUDIO_OUTPUT", "GND": "Default",
    }
    for net_name, class_name in expected.items():
        actual = board.FindNet(net_name).GetNetClassName()
        assert actual == class_name, (net_name, actual, class_name)
    print("PASS: USB, fine-escape, audio and power routing classes; 0.20 mm via rings")


if __name__ == "__main__":
    main()
