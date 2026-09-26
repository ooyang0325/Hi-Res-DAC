#!/usr/bin/env python3
"""Audit the JLCPCB loader's CAD data against the workbook pin numbers."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from generate_schematic import HERE, read_source


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
    _, pins, parts = read_source()
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
            workbook_numbers = {
                pin.number for part in source_parts for ref in part.refs for pin in pins[ref]
            }
            symbol_match = candidate_symbol_pins == workbook_numbers
            footprint_match = candidate_pad_numbers == workbook_numbers
            output[code] = {
                "manufacturer_part": attributes.get("Manufacturer Part", ""),
                "refs": sorted({ref for part in source_parts for ref in part.refs}),
                "footprint": device.get("footprint", {}).get("display_title", ""),
                "symbol_pin_numbers": sorted(candidate_symbol_pins),
                "footprint_pad_numbers": sorted(candidate_pad_numbers),
                "workbook_pin_numbers": sorted(workbook_numbers),
                "symbol_numbers_match": symbol_match,
                "footprint_numbers_match": footprint_match,
                "status": "candidate_exact_numbers" if symbol_match and footprint_match else "review_required",
            }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    exact = sum(item["status"] == "candidate_exact_numbers" for item in output.values())
    print(f"Audited {len(output)} JLCPCB codes: {exact} exact pin/pad sets, {len(output)-exact} requiring review")
    for code, item in output.items():
        if item["status"] != "candidate_exact_numbers":
            print(code, ",".join(item["refs"]), "workbook", item["workbook_pin_numbers"],
                  "library", item["footprint_pad_numbers"])


if __name__ == "__main__":
    audit()
