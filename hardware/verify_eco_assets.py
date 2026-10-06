#!/usr/bin/env python3
"""Verify the exact JLC C507231 land and 3D body used by the F02 ECO.

Run with KiCad's Python interpreter. This checks the source-to-native footprint
conversion and pad spacing; it does not replace a placed-board DRC or G-3
physical overlay.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "JLC_Source" / "JLC_DAC_HPA.elibz"
NATIVE = HERE / "JLC_Imported.pretty"
MODEL_RECORDS = HERE / "EASYEDA_MODELS" / "MODEL_SOURCES.json"
CODE = "C507231"
MPN = "SN74AUP2G17DCKR"
FOOTPRINT = "SC-70-6_L2.2-W1.3-P0.65-LS2.1-BL"
MODEL = "SC-70-6_L2.0-W1.3-H1.0-P0.65.step"


def pad_map(footprint: pcbnew.FOOTPRINT) -> dict[str, tuple[int, int, int, int, int, int]]:
    result = {}
    for pad in footprint.Pads():
        number = pad.GetNumber()
        if number in result:
            raise AssertionError(f"Repeated {FOOTPRINT} pad {number}")
        pos, size = pad.GetPosition(), pad.GetSize()
        result[number] = (pos.x, pos.y, size.x, size.y,
                          int(pad.GetShape()), round(pad.GetOrientationDegrees()))
    return result


def run() -> None:
    with ZipFile(SOURCE) as archive:
        devices = json.loads(archive.read("device.json"))["devices"]
        matches = [item for item in devices.values() if item.get("product_code") == CODE]
    if len(matches) != 1:
        raise AssertionError(f"Expected one JLC source device {CODE}, found {len(matches)}")
    device = matches[0]
    if (device["attributes"].get("Manufacturer Part"),
        device.get("footprint", {}).get("display_title")) != (MPN, FOOTPRINT):
        raise AssertionError("C507231 MPN/footprint identity changed")

    source = pcbnew.FootprintLoad(str(SOURCE), FOOTPRINT)
    native = pcbnew.FootprintLoad(str(NATIVE), FOOTPRINT)
    if source is None or native is None:
        raise AssertionError("KiCad cannot load the source or native C507231 footprint")
    source_pads, native_pads = pad_map(source), pad_map(native)
    if source_pads != native_pads or set(native_pads) != {str(n) for n in range(1, 7)}:
        raise AssertionError(f"C507231 source/native pad geometry differs: {source_pads} / {native_pads}")
    if any(item[-2] != int(pcbnew.PAD_SHAPE_RECT) or item[-1] != 0
           for item in native_pads.values()):
        raise AssertionError("C507231 pad-copper gap check requires unrotated rectangular pads")
    coords = {number: tuple(v / 1e6 for v in values[:4])
              for number, values in native_pads.items()}
    expected = {
        "1": (-0.65, 0.84, 0.35, 0.78),
        "2": (0.00, 0.84, 0.35, 0.78),
        "3": (0.65, 0.84, 0.35, 0.78),
        "4": (0.65, -0.84, 0.35, 0.78),
        "5": (0.00, -0.84, 0.35, 0.78),
        "6": (-0.65, -0.84, 0.35, 0.78),
    }
    if coords != expected:
        raise AssertionError(f"C507231 imported pad dimensions moved: {coords}")
    min_clearance = math.inf
    for i, first in enumerate(sorted(coords)):
        x1, y1, w1, h1 = coords[first]
        for second in sorted(coords)[i + 1:]:
            x2, y2, w2, h2 = coords[second]
            dx = max(0.0, abs(x1 - x2) - (w1 + w2) / 2)
            dy = max(0.0, abs(y1 - y2) - (h1 + h2) / 2)
            min_clearance = min(min_clearance, math.hypot(dx, dy))
    if min_clearance < 0.15 - 1e-9:
        raise AssertionError(f"C507231 pad copper gap {min_clearance:.3f} mm < 0.15 mm")

    models = list(native.Models())
    expected_link = "${KIPRJMOD}/EASYEDA_MODELS/" + MODEL
    if len(models) != 1 or models[0].m_Filename != expected_link:
        raise AssertionError("C507231 exact JLC STEP link is missing from footprint")
    records = json.loads(MODEL_RECORDS.read_text(encoding="utf-8"))
    record = [item for item in records if item.get("lcsc_code") == CODE]
    if len(record) != 1 or record[0].get("converted_file") != MODEL:
        raise AssertionError("C507231 model provenance entry is missing")
    model_path = HERE / "EASYEDA_MODELS" / MODEL
    if not model_path.is_file() or model_path.stat().st_size < 1000:
        raise AssertionError("C507231 exact STEP file is missing")
    if hashlib.sha256(model_path.read_bytes()).hexdigest() != record[0]["converted_sha256"]:
        raise AssertionError("C507231 exact STEP hash differs from provenance")
    print(f"PASS: JLC {CODE} source/native six-pad geometry identical; minimum pad gap {min_clearance:.2f} mm")
    print(f"PASS: exact {MPN} STEP body and SHA-256 provenance match")


if __name__ == "__main__":
    run()
