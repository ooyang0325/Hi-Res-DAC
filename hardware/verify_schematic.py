#!/usr/bin/env python3
"""Check the KiCad capture against v0.9 plus its asserted ECO and run ERC."""

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

from generate_schematic import (
    HERE, PROJECT, apply_approved_overrides, apply_functional_eco,
    datasheet_url, read_source, symbol_value, workbook_value,
)


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
    base_parts, workbook_pins, base_libparts = read_source()
    parts, design_pins, _ = apply_functional_eco(
        base_parts, apply_approved_overrides(workbook_pins), base_libparts,
    )
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
        excluded_from_board = {
            ref for ref, component in components.items()
            if component.find("property[@name='exclude_from_board']") is not None
        }
        if excluded_from_board != {"J703"}:
            raise AssertionError(f"Unexpected PCB-excluded symbols: {excluded_from_board}")

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
        named_nets = {pin.net for group in design_pins.values() for pin in group if pin.net != "NC"}
        if (len(parts), len(expected_nodes), connected, nc_count, len(named_nets)) != (534, 1465, 1424, 41, 252):  # F07: +2 CPLD copy nets
            raise AssertionError("Unexpected post-ECO designator, pin or net counts")

        source_nodes = {(ref, pin.number): pin.net for ref, group in workbook_pins.items() for pin in group}
        actual_delta = {key: (source_nodes.get(key), expected_nodes.get(key))
                        for key in set(source_nodes) | set(expected_nodes)
                        if source_nodes.get(key) != expected_nodes.get(key)}
        approved_delta = {
            ("D705", "1"): ("GND", "N7_LEDG_A"), ("D705", "2"): ("N7_LEDG_A", "GND"),
            ("D706", "1"): ("GND", "N7_LEDR_A"), ("D706", "2"): ("N7_LEDR_A", "GND"),
            ("R688", "2"): ("N6_V3AG_A_MCU", "N6_V3AG_A_BUF_IN"),
            ("R689", "2"): ("N6_V3AG_B_MCU", "N6_V3AG_B_BUF_IN"),
            ("U403", "1"): ("N4_IVL_P", "N4_IVL_N"),
            ("U403", "2"): ("DACL", "DACLB"),
            ("U403", "6"): ("DACLB", "DACL"),
            ("U403", "7"): ("N4_IVL_N", "N4_IVL_P"),
            ("U404", "1"): ("N4_IVR_P", "N4_IVR_N"),
            ("U404", "2"): ("DACR", "DACRB"),
            ("U404", "6"): ("DACRB", "DACR"),
            ("U404", "7"): ("N4_IVR_N", "N4_IVR_P"),
            # ECO F06 v2: layout-driven AGRV2K I/O reassignment (RTL constraints follow)
            ("U202", "10"): ("LINK_MOSI", "NC"), ("U202", "27"): ("NC", "LINK_MOSI"),
            ("U202", "11"): ("LINK_FRAME", "NC"), ("U202", "26"): ("NC", "LINK_FRAME"),
            ("U202", "12"): ("LINK_MISO", "NC"), ("U202", "28"): ("NC", "LINK_MISO"),
            ("U202", "14"): ("CPLD_IRQ", "NC"), ("U202", "29"): ("NC", "CPLD_IRQ"),
            ("U202", "2"): ("OSC48_EN", "NC"), ("U202", "31"): ("NC", "OSC48_EN"),
            ("U202", "3"): ("OSC44_EN", "NC"), ("U202", "8"): ("NC", "OSC44_EN"),
            # ECO F07: CPLD-driven BCLK/SDATA capture copies into R228/R230; R229 taps LRCLK_FB (WS)
            ("U202", "21"): ("MCLK_EN", "N2_CPY_CK"),  # ECO F08 pin rotation (F07 copies)
            ("U202", "22"): ("NC", "N2_CPY_SD"),
            ("U202", "23"): ("NC", "MCLK_EN"),
            ("R228", "1"): ("N2_BCLK_SRC", "N2_CPY_CK"), ("R229", "1"): ("N2_LRCLK_SRC", "LRCLK_FB"),
            ("R230", "1"): ("N2_SDATA_SRC", "N2_CPY_SD"),
        }
        approved_added = {
            ("U621", "1"): "N6_V3AG_A_BUF_IN", ("U621", "2"): "GND",
            ("U621", "3"): "N6_V3AG_B_BUF_IN", ("U621", "4"): "N6_V3AG_B_BUF_OUT",
            ("U621", "5"): "3V3M", ("U621", "6"): "N6_V3AG_A_BUF_OUT",
            ("R952", "1"): "N6_V3AG_A_BUF_OUT", ("R952", "2"): "N6_V3AG_A_MCU",
            ("R953", "1"): "N6_V3AG_B_BUF_OUT", ("R953", "2"): "N6_V3AG_B_MCU",
            ("R954", "1"): "3V3M", ("R954", "2"): "N6_V3AG_A_MCU",
            ("R955", "1"): "3V3M", ("R955", "2"): "N6_V3AG_B_MCU",
            ("C667", "1"): "3V3M", ("C667", "2"): "GND",
            ("D707", "1"): "JACK_RP", ("D707", "2"): "GND",
            ("D708", "1"): "JACK_LP", ("D708", "2"): "GND",
        }
        approved_delta.update({key: (None, net) for key, net in approved_added.items()})
        if actual_delta != approved_delta:
            raise AssertionError(f"Unapproved workbook-to-schematic ECO delta: {actual_delta}")

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
            eco_assets = subprocess.run(
                [str(kicad_python), str(HERE / "verify_eco_assets.py")],
                capture_output=True, text=True,
            )
            if eco_assets.returncode:
                raise RuntimeError(f"Functional-ECO CAD asset check failed: {eco_assets.stdout}\n{eco_assets.stderr[-1000:]}")
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

        print(f"PASS: 526 workbook components + 8 ECO components, 11 PCB items, {len(expected_nodes)} schematic pins")
        print(f"PASS: {connected} connected pins match the approved KiCad pin/net map exactly")
        print(f"PASS: {len(package_nodes)} workbook pins match the calculation package's merged netlist")
        print(f"PASS: 247 source net labels including NC, {len(named_nets)} post-ECO named nets")
        print(f"PASS: exactly {len(approved_delta)} documented workbook-to-schematic pin/net deltas")
        print(f"PASS: {fields_checked} MPN/LCSC/fit/package/source/value fields match")
        if matched_footprints is not None:
            print(f"PASS: {matched_footprints} assigned footprints have matching symbol pin/pad number sets")
            print(eco_assets.stdout.strip())
        print("PASS: KiCad ERC 0 violations (selected outputs are typed; remaining pins are mostly passive)")
        print("CORRECTED: D705/D706 physical pad polarity follows the manufacturer and JLC symbols")
        print("PCB OPTION: J703 remains in the schematic but is excluded from the PCB")
        print("OPEN PHYSICAL GATES: G-1 through G-4; footprints with a provisional status still need review")


if __name__ == "__main__":
    run()
