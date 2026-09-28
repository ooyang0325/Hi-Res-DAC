#!/usr/bin/env python3
"""Export review-only assembly lists from the actual KiCad schematic.

JLCPCB placement data depends on a routed PCB, so these lists are deliberately
named REVIEW_ONLY. Owner-fitted and DNF parts are excluded from the JLC list.
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

from generate_schematic import HERE, PROJECT, natural


def kicad_cli() -> str:
    return shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    environment = os.environ.copy()
    environment.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "hires-dac-fontcache"))
    with tempfile.TemporaryDirectory(prefix="dac-hpa-bom-") as scratch:
        xml_path = Path(scratch) / "schematic.xml"
        result = subprocess.run(
            [kicad_cli(), "sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml_path), str(HERE / f"{PROJECT}.kicad_sch")],
            capture_output=True, text=True, env=environment,
        )
        if result.returncode:
            raise RuntimeError(f"KiCad netlist export failed: {result.stdout}\n{result.stderr[-1000:]}")
        root = ET.parse(xml_path).getroot()

    groups: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    owner: list[list[str]] = []
    dnf: list[list[str]] = []
    kinds: Counter[str] = Counter()
    for component in root.find("components"):
        ref = component.attrib["ref"]
        fields = {field.attrib["name"]: field.text or "" for field in component.find("fields")}
        kind = fields["Assembly"]
        kinds[kind] += 1
        value = component.findtext("value") or ""
        footprint = component.findtext("footprint") or ""
        lcsc = fields["LCSC Part #"]
        mpn = fields["MPN"]
        if kind == "Yes":
            if not footprint:
                raise AssertionError(f"JLCPCB-placed {ref} has no footprint")
            groups[(value, footprint, lcsc, mpn)].append(ref)
        elif kind in {"Owner", "No"}:
            item = [ref, value, footprint, lcsc, mpn]
            (owner if kind == "Owner" else dnf).append(item)
        elif kind not in {"Pads", "No part"}:
            raise AssertionError(f"Unexpected assembly category {kind!r} on {ref}")
    expected = {"Yes": 463, "Owner": 7, "No": 9, "Pads": 3, "No part": 63}  # v0.9 + 8 ECO, 52 test pads + 11 mechanical items
    if dict(kinds) != expected:
        raise AssertionError(f"Schematic assembly count changed: {dict(kinds)} != {expected}")

    placed = []
    for (value, footprint, lcsc, mpn), refs in sorted(groups.items(), key=lambda item: natural(min(item[1], key=natural))):
        placed.append([value, ",".join(sorted(refs, key=natural)), footprint, "" if lcsc == "—" else lcsc, mpn])
    write_csv(HERE / "JLCPCB_BOM_REVIEW_ONLY.csv", ["Comment", "Designator", "Footprint", "LCSC Part #", "MPN"], placed)
    header = ["Designator", "Comment", "Footprint", "LCSC Part #", "MPN"]
    write_csv(HERE / "OWNER_FITTED_REVIEW_ONLY.csv", header, sorted(owner, key=lambda row: natural(row[0])))
    write_csv(HERE / "DNF_REVIEW_ONLY.csv", header, sorted(dnf, key=lambda row: natural(row[0])))
    missing_code = sum(len(refs) for (value, footprint, lcsc, mpn), refs in groups.items() if not lcsc or lcsc == "—")
    print(f"Exported {kinds['Yes']} JLCPCB-placed items on {len(placed)} rows; {kinds['Owner']} owner-fitted; {kinds['No']} DNF")
    print(f"OPEN: {missing_code} placed items have no LCSC code; global sourcing must be arranged before ordering")
    print("REVIEW ONLY: a routed PCB and CPL are required before PCBA upload")


if __name__ == "__main__":
    main()
