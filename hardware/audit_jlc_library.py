#!/usr/bin/env python3
"""Audit the JLCPCB loader's CAD data against the approved schematic pins."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from generate_schematic import HERE, read_design


SOURCE = HERE / "JLC_Source" / "JLC_DAC_HPA.elibz"
OUTPUT = HERE / "jlc_footprints.json"


def records(archive: ZipFile, path: str) -> list[list]:
    return [json.loads(line) for line in archive.read(path).decode("utf-8").splitlines()]


def symbol_numbers(archive: ZipFile, symbol_uuid: str) -> set[str]:
    content = records(archive, f"SYMBOL/{symbol_uuid}.esym")
    pin_ids = {row[1] for row in content if row and row[0] == "PIN"}
    return {
        str(row[4]) for row in content
        if row and row[0] == "ATTR" and len(row) > 4
        and row[2] in pin_ids and row[3] == "NUMBER"
    }


def footprint_numbers(archive: ZipFile, footprint_uuid: str) -> set[str]:
    content = records(archive, f"FOOTPRINT/{footprint_uuid}.efoo")
    return {
        str(row[5]) for row in content
        if row and row[0] == "PAD" and len(row) > 5 and str(row[5])
    }


def audit() -> None:
    _, pins, parts = read_design()
    by_code = defaultdict(list)
    for part in parts.values():
        if part.lcsc.startswith("C"):
            by_code[part.lcsc].append(part)

    output = {}
    with ZipFile(SOURCE) as archive:
        data = json.loads(archive.read("device.json"))
        devices = {device["product_code"]: device for device in data["devices"].values()}
        for code, device in sorted(devices.items()):
            source_parts = by_code.get(code, [])
            if not source_parts:
                continue
            attributes = device["attributes"]
            symbol_uuid = attributes.get("Symbol")
            footprint_uuid = attributes.get("Footprint")
            candidate_symbol_pins = symbol_numbers(archive, symbol_uuid) if symbol_uuid else set()
            candidate_pad_numbers = footprint_numbers(archive, footprint_uuid) if footprint_uuid else set()
            design_numbers = {
                pin.number for part in source_parts for ref in part.refs for pin in pins[ref]
            }
            symbol_match = candidate_symbol_pins == design_numbers
            footprint_match = candidate_pad_numbers == design_numbers
            output[code] = {
                "manufacturer_part": attributes.get("Manufacturer Part", ""),
                "refs": sorted({ref for part in source_parts for ref in part.refs}),
                "footprint": device.get("footprint", {}).get("display_title", ""),
                "symbol_pin_numbers": sorted(candidate_symbol_pins),
                "footprint_pad_numbers": sorted(candidate_pad_numbers),
                "approved_design_pin_numbers": sorted(design_numbers),
                "symbol_numbers_match": symbol_match,
                "footprint_numbers_match": footprint_match,
                "status": "candidate_exact_numbers" if symbol_match and footprint_match else "review_required",
            }
        # U403/U404 use a later owner-approved MPN than Parts List v0.9.
        # Reuse the loader's existing TI DGK0008A land from C140314; the
        # OPA2210 pin map was checked against TI's Figure 5-3/Table 5-2.
        if "C2876414" in by_code:
            donor = devices["C140314"]
            donor_footprint_uuid = donor["attributes"]["Footprint"]
            donor_numbers = footprint_numbers(archive, donor_footprint_uuid)
            expected_numbers = {str(i) for i in range(1, 9)}
            if donor_numbers != expected_numbers:
                raise ValueError("TI DGK donor footprint pad numbers changed")
            footprint_name = donor.get("footprint", {}).get("display_title", "")
            if footprint_name != "VSSOP-8_L3.0-W3.0-P0.65-LS5.0-BL":
                raise ValueError("TI DGK donor footprint geometry changed")
            output["C2876414"] = {
                "manufacturer_part": "OPA2210IDGKR",
                "refs": ["U403", "U404"],
                "footprint": footprint_name,
                "symbol_pin_numbers": sorted(expected_numbers),
                "footprint_pad_numbers": sorted(donor_numbers),
                "approved_design_pin_numbers": sorted(expected_numbers),
                "symbol_numbers_match": True,
                "footprint_numbers_match": True,
                "symbol_source": "TI OPA2210 datasheet Figure 5-3/Table 5-2",
                "footprint_source_code": "C140314, TI DGK0008A package",
                "status": "review_required",
            }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    exact = sum(item["status"] == "candidate_exact_numbers" for item in output.values())
    print(f"Audited {len(output)} JLCPCB codes: {exact} exact pin/pad sets, {len(output)-exact} requiring review")
    for code, item in output.items():
        if item["status"] != "candidate_exact_numbers":
            print(code, ",".join(item["refs"]), "design", item["approved_design_pin_numbers"],
                  "library", item["footprint_pad_numbers"])


if __name__ == "__main__":
    audit()
