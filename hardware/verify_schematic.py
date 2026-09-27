#!/usr/bin/env python3
"""Check the KiCad capture against Parts List v0.9 and run KiCad ERC."""

from __future__ import annotations

import os
import csv
import io
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from generate_schematic import HERE, PROJECT, apply_approved_overrides, datasheet_url, read_source, symbol_value, workbook_value


def cli() -> str:
    candidate = shutil.which("kicad-cli")
    if candidate:
        return candidate
    mac = Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
    if mac.exists():
        return str(mac)
    raise RuntimeError("kicad-cli is needed to verify the exported schematic")


def pcbnew_python() -> Path:
    candidates = [os.environ.get("KICAD_PYTHON", ""), sys.executable,
                  "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3",
                  "/usr/bin/python3"]
    for name in dict.fromkeys(candidates):
        if not name:
            continue
        executable = Path(name)
        if executable.exists() and subprocess.run(
            [str(executable), "-c", "import pcbnew"], capture_output=True, text=True,
        ).returncode == 0:
            return executable
    raise RuntimeError("A Python interpreter with KiCad's pcbnew module is required for footprint verification")


def footprint_root() -> Path:
    candidates = [os.environ.get("KICAD10_FOOTPRINT_DIR", ""),
                  "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
                  "/usr/share/kicad/footprints"]
    for name in candidates:
        if name and (Path(name) / "Resistor_SMD.pretty").is_dir():
            return Path(name)
    raise RuntimeError("Cannot locate KiCad's stock footprint libraries")


def run() -> None:
    parts, workbook_pins, _ = read_source()
    design_pins = apply_approved_overrides(workbook_pins)
    schematic = HERE / f"{PROJECT}.kicad_sch"
    environment = os.environ.copy()
    environment.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "hires-dac-fontcache"))

    with tempfile.TemporaryDirectory(prefix="dac-hpa-check-") as scratch:
        xml_path = Path(scratch) / "netlist.xml"
        erc_path = Path(scratch) / "erc.json"
        export = subprocess.run(
            [cli(), "sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml_path), str(schematic)],
            capture_output=True, text=True, env=environment,
        )
        if export.returncode:
            raise RuntimeError(f"KiCad netlist export failed: {export.stdout}\n{export.stderr[-1000:]}")

        root = ET.parse(xml_path).getroot()
        components = {comp.attrib["ref"]: comp for comp in root.find("components")}
        expected_refs = set(parts) | {f"MH{i}" for i in range(1, 5)} | {f"FID{i}" for i in range(1, 8)}
        if set(components) != expected_refs:
            raise AssertionError(f"Component set differs: missing={set(expected_refs)-set(components)}, extra={set(components)-expected_refs}")

        fields_checked = 0
        for ref, part in parts.items():
            component = components[ref]
            fields = {field.attrib["name"]: field.text or "" for field in component.find("fields")}
            expected_fields = {
                "MPN": part.mpn,
                "LCSC": part.lcsc,
                "LCSC Part #": part.lcsc,
                "Assembly": part.fit,
                "Package": part.package,
                "Rating/Tolerance": part.rating_tolerance,
                "Source": part.source,
                "Workbook Value": workbook_value(part, ref),
                "Datasheet": datasheet_url(part),
            }
            for name, expected in expected_fields.items():
                if fields.get(name) != expected:
                    raise AssertionError(f"{ref} {name}: {fields.get(name)!r} != {expected!r}")
                fields_checked += 1
            if component.findtext("value") != symbol_value(part):
                raise AssertionError(f"{ref}: displayed value differs from source")

        actual_nodes: dict[tuple[str, str], str] = {}
        for net in root.find("nets"):
            name = net.attrib["name"].removeprefix("/")
            for node in net:
                key = (node.attrib["ref"], node.attrib["pin"])
                if key in actual_nodes:
                    raise AssertionError(f"A schematic pin appears in two nets: {key}")
                actual_nodes[key] = name

        expected_nodes = {
            (ref, pin.number): pin.net
            for ref, pins in design_pins.items()
            for pin in pins
        }
        mismatches = []
        for key, expected in expected_nodes.items():
            actual = actual_nodes.get(key)
            if expected == "NC":
                if actual is not None and not actual.startswith("unconnected-"):
                    mismatches.append((key, expected, actual))
            elif actual != expected:
                mismatches.append((key, expected, actual))
        if mismatches:
            raise AssertionError(f"Approved-map/KiCad pin-net mismatches: {mismatches[:20]}")
        extras = {
            key: name for key, name in actual_nodes.items()
            if key not in expected_nodes and not (key[0].startswith("MH") and name == "GND")
        }
        if extras:
            raise AssertionError(f"Unexpected KiCad pin nodes: {list(extras.items())[:20]}")
        connected = sum(pin.net != "NC" for pins in design_pins.values() for pin in pins)
        nc_count = len(expected_nodes) - connected
        named_nets = {pin.net for group in workbook_pins.values() for pin in group if pin.net != "NC"}
        if (len(parts), len(expected_nodes), connected, nc_count, len(named_nets)) != (526, 1445, 1402, 43, 246):
            raise AssertionError("Unexpected v0.9 designator, pin or net counts")

        source_nodes = {(ref, pin.number): pin.net for ref, group in workbook_pins.items() for pin in group}
        actual_delta = {key: (source_nodes.get(key), expected_nodes.get(key))
                        for key in set(source_nodes) | set(expected_nodes)
                        if source_nodes.get(key) != expected_nodes.get(key)}
        approved_delta = {
            ("D705", "1"): ("GND", "N7_LEDG_A"), ("D705", "2"): ("N7_LEDG_A", "GND"),
            ("D706", "1"): ("GND", "N7_LEDR_A"), ("D706", "2"): ("N7_LEDR_A", "GND"),
        }
        if actual_delta != approved_delta:
            raise AssertionError(f"Unapproved workbook-to-schematic net overrides: {actual_delta}")

        package = HERE.parent / "doc" / "DAC_HPA_Calculation_Package_v1.1.zip"
        with zipfile.ZipFile(package) as archive:
            with archive.open("calc_package_v11/integration/netlist_merged.csv") as source:
                rows = list(csv.DictReader(io.TextIOWrapper(source, encoding="utf-8-sig")))
        package_nodes = {(row["refdes"], str(row["pin"])): row["net"] for row in rows}
        if len(rows) != len(package_nodes) or package_nodes != source_nodes:
            differing = [(key, source_nodes.get(key), package_nodes.get(key))
                         for key in set(source_nodes) | set(package_nodes)
                         if source_nodes.get(key) != package_nodes.get(key)]
            raise AssertionError(f"Workbook/calculation-package pin-net mismatch: {differing[:20]}")

        kicad_python = pcbnew_python()
        if kicad_python.exists():
            library_root = footprint_root()
            footprints = {}
            unassigned = sorted(ref for ref, component in components.items() if not component.findtext("footprint"))
            if unassigned:
                raise AssertionError(f"Unexpected unassigned footprints: {unassigned}")
            for component in components.values():
                identifier = component.findtext("footprint") or ""
                if not identifier:
                    continue
                nickname, name = identifier.split(":", 1)
                library_path = HERE / f"{nickname}.pretty" if nickname in {"DAC_HPA", "JLC_Imported"} else library_root / f"{nickname}.pretty"
                footprints[identifier] = {"library_path": str(library_path), "name": name}
            inspected = subprocess.run(
                [str(kicad_python), str(HERE / "footprint_pads_kicad.py")],
                input=json.dumps(footprints), capture_output=True, text=True,
            )
            if inspected.returncode:
                raise RuntimeError(f"Footprint inspection failed: {inspected.stderr[-1000:]}")
            pad_sets = json.loads(inspected.stdout)
            matched_footprints = 0
            for ref, component in components.items():
                identifier = component.findtext("footprint") or ""
                if not identifier:
                    continue
                expected = {pin.number for pin in design_pins[ref]} if ref in design_pins else ({"1"} if ref.startswith("MH") else set())
                actual = set(pad_sets[identifier]) - {""}  # unnumbered NPTH locating pegs
                if actual != expected:
                    raise AssertionError(f"{ref} footprint {identifier}: pads {sorted(actual)} != symbol pins {sorted(expected)}")
                matched_footprints += 1
        else:
            raise RuntimeError(f"KiCad Python interpreter disappeared: {kicad_python}")

        erc = subprocess.run(
            [cli(), "sch", "erc", "--format", "json", "--exit-code-violations", "-o", str(erc_path), str(schematic)],
            capture_output=True, text=True, env=environment,
        )
        if erc.returncode:
            raise RuntimeError(f"KiCad ERC failed: {erc.stdout}\n{erc.stderr[-1000:]}")
        if "Found 0 violations" not in erc.stdout:
            raise AssertionError(f"KiCad ERC was not clean: {erc.stdout}")

        print(f"PASS: {len(parts)} workbook components, 11 PCB items, {len(expected_nodes)} approved schematic pins")
        print(f"PASS: {connected} connected pins match the approved KiCad pin/net map exactly")
        print(f"PASS: {len(package_nodes)} workbook pins match the calculation package's merged netlist")
        print(f"PASS: 247 workbook nets (including NC); only {len(approved_delta)} owner-approved D705/D706 pin/net entries differ")
        print(f"PASS: {fields_checked} MPN/LCSC/fit/package/source/value fields match")
        if matched_footprints is not None:
            print(f"PASS: {matched_footprints} assigned footprints have matching symbol pin/pad number sets")
        print("PASS: KiCad ERC 0 violations (selected outputs are typed; remaining pins are mostly passive)")
        print("CORRECTED: D705/D706 physical pad polarity follows the manufacturer and JLC symbols")
        print("OPEN PHYSICAL GATES: G-1 through G-4; footprints with a provisional status still need review")


if __name__ == "__main__":
    run()
