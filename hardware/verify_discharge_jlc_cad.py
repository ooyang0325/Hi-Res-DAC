#!/usr/bin/env python3
"""Compare the two JLC resistor entries with the exact native R2512 import.

The shared JLC pad pattern is reproducible, but the FOJAN maker land drawing
does not match it. Report that conflict; do not approve an assembly footprint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "JLC_Source/JLC_Discharge_2512.elibz"
NATIVE = HERE / "JLC_Imported.pretty"
MODEL = HERE / "EASYEDA_MODELS/R2512_L6.3-W3.2-H0.6.step"
MODEL_MANIFEST = HERE / "EASYEDA_MODELS/MODEL_SOURCES.json"
FOOTPRINT = "R2512"
CODES = {
    "C2907584": "FRC2512J4R7 TS",
    "C5123624": "HoCR2512-2W-10R-1%",
}


def pad_map(fp: pcbnew.FOOTPRINT) -> dict[str, tuple[float, float, float, float, int]]:
    result = {}
    for pad in fp.Pads():
        pos = pad.GetPosition()
        size = pad.GetSize()
        result[pad.GetNumber()] = (
            round(pcbnew.ToMM(pos.x), 4), round(pcbnew.ToMM(pos.y), 4),
            round(pcbnew.ToMM(size.x), 4), round(pcbnew.ToMM(size.y), 4),
            int(pad.GetShape()),
        )
    return result


def audit() -> dict:
    with ZipFile(SOURCE) as archive:
        data = json.loads(archive.read("device.json"))
        devices = {item["product_code"]: item for item in data["devices"].values()}
        if set(devices) != set(CODES):
            raise AssertionError("Exact JLC discharge device set changed")
        footprint_uuids = {item["attributes"]["Footprint"] for item in devices.values()}
        model_uuids = {item["attributes"]["3D Model"] for item in devices.values()}
        if len(footprint_uuids) != 1 or len(model_uuids) != 1:
            raise AssertionError("The two JLC codes no longer share one R2512 land/model")
        footprint_uuid = next(iter(footprint_uuids))
        source_rows = [json.loads(line) for line in
                       archive.read(f"FOOTPRINT/{footprint_uuid}.efoo").decode().splitlines()
                       if line.strip()]
        source_pads = {}
        for row in source_rows:
            if not row or row[0] != "PAD":
                continue
            if row[10][0] != "RECT":
                raise AssertionError("JLC source pad is no longer rectangular")
            source_pads[str(row[5])] = tuple(float(value) * 0.0254 for value in
                                             (row[6], row[7], row[10][1], row[10][2]))
    for code, mpn in CODES.items():
        device = devices[code]
        if (device["attributes"].get("Manufacturer Part") != mpn
                or device.get("footprint", {}).get("display_title") != FOOTPRINT):
            raise AssertionError(f"{code} exact JLC identity changed")
    native = pcbnew.FootprintLoad(str(NATIVE), FOOTPRINT)
    if native is None:
        raise AssertionError("KiCad could not load the native JLC R2512")
    native_pads = pad_map(native)
    if set(source_pads) != set(native_pads) or set(source_pads) != {"1", "2"}:
        raise AssertionError(f"JLC source/native pad numbers differ: {source_pads} / {native_pads}")
    for number, row in native_pads.items():
        if row[4] != int(pcbnew.PAD_SHAPE_RECT) or any(
                abs(source - imported) > 0.001
                for source, imported in zip(source_pads[number], row[:4])):
            raise AssertionError(f"JLC source/native pad geometry differs: {source_pads} / {native_pads}")
    one, two = native_pads["1"], native_pads["2"]
    if (one[:4], two[:4]) != ((-3.0665, 0.0, 1.2825, 3.456),
                               (3.0665, 0.0, 1.2825, 3.456)):
        raise AssertionError("JLC R2512 pad geometry changed; re-review maker lands")
    model_paths = [model.m_Filename for model in native.Models()]
    expected_model = "${KIPRJMOD}/EASYEDA_MODELS/" + MODEL.name
    if model_paths != [expected_model] or not MODEL.is_file():
        raise AssertionError("Exact JLC R2512 model link or file is missing")
    digest = hashlib.sha256(MODEL.read_bytes()).hexdigest()
    entries = json.loads(MODEL_MANIFEST.read_text())
    matching = [item for item in entries if item["converted_file"] == MODEL.name]
    if len(matching) != 1 or matching[0]["converted_sha256"] != digest:
        raise AssertionError("Exact JLC R2512 model provenance/hash is missing")
    inner = round(two[0] - two[2] / 2 - (one[0] + one[2] / 2), 4)
    outer = round(two[0] + two[2] / 2 - (one[0] - one[2] / 2), 4)
    height = one[3]
    return {
        "source_library": SOURCE.name,
        "devices": {code: CODES[code] for code in sorted(CODES)},
        "shared_footprint_uuid": next(iter(footprint_uuids)),
        "shared_model_uuid": next(iter(model_uuids)),
        "native_footprint": "JLC_Imported:R2512",
        "pads_mm": {number: {"centre": list(row[:2]), "size": list(row[2:4]),
                             "shape_id": row[4]}
                    for number, row in sorted(native_pads.items())},
        "jlc_land_mm": {"inner_gap_A": inner, "outer_span_B": outer,
                        "pad_height_C": height},
        "fojan_maker_recommended_mm": {"inner_gap_A": [3.60, 4.20],
                                       "outer_span_B": [7.60, 8.60],
                                       "pad_height_C": [3.00, 3.50]},
        "fojan_maker_land_match": (3.60 <= inner <= 4.20
                                   and 7.60 <= outer <= 8.60
                                   and 3.00 <= height <= 3.50),
        "milliohm_maker_land_check": "open: manufacturer drawing not retrieved",
        "exact_jlc_model_sha256": digest,
        "release_status": "HOLD: JLC FOJAN pad pattern conflicts with maker A/B land range",
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
