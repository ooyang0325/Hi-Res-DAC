#!/usr/bin/env python3
"""Export an actual-size overlay and checklist for the G-3 sample set.

The source is the current assembly-review CSVs, so a changed footprint ID
cannot silently leave an outdated overlay. This is a review aid, not Gerber.
"""

from __future__ import annotations

import csv
import os
from html import escape
from pathlib import Path

import pcbnew

from export_g3_connector_overlay import HERE, fab_svg, n, pad_svg


FOOTPRINT_REFS = """
J101 J701 J702 K601 K602 K603 K604 X201 X202 X203 U503 U103 U206
D705 D706 D102 D104 D105 D411 D412 C442 C443 U208 U605 U606 U607
D609 D610 Q207 Q619 Q620 U502 U608 U609 U610 Q507 Q621 Q622
Q623 Q624 Q625 Q626 C631 C632 C633 C634 U611 U612 Q627
C647 C648 C649 C650 C651 C652 C653 C654
U613 U614 U615 U616 U617 U618 U619 U620 U202 D405 D406 D407 D408
""".split()
CONNECTORS = {"J101", "J701", "J702"}
CSV_SOURCES = (
    "JLCPCB_BOM_REVIEW_ONLY.csv",
    "OWNER_FITTED_REVIEW_ONLY.csv",
    "DNF_REVIEW_ONLY.csv",
)
SVG = HERE / "G3_PART_OVERLAY_REVIEW_ONLY.svg"
INDEX = HERE / "G3_OVERLAY_INDEX.md"


def footprint_roots() -> list[Path]:
    candidates = [
        os.environ.get("KICAD10_FOOTPRINT_DIR"),
        os.environ.get("KICAD9_FOOTPRINT_DIR"),
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
        "/usr/share/kicad/footprints",
    ]
    return [Path(p) for p in candidates if p and Path(p).is_dir()]


def library_path(lib: str) -> Path:
    if lib in {"DAC_HPA", "JLC_Imported"}:
        return HERE / f"{lib}.pretty"
    for root in footprint_roots():
        path = root / f"{lib}.pretty"
        if path.is_dir():
            return path
    raise FileNotFoundError(f"KiCad footprint library not found: {lib}")


def assembly_footprints() -> dict[str, str]:
    result = {}
    for filename in CSV_SOURCES:
        with (HERE / filename).open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                for ref in row["Designator"].split(","):
                    ref = ref.strip()
                    if ref:
                        assert ref not in result, f"duplicate assembly ref: {ref}"
                        result[ref] = row["Footprint"].strip()
    missing = set(FOOTPRINT_REFS) - result.keys()
    assert not missing, f"missing G-3 references from assembly CSVs: {sorted(missing)}"
    return result


def group_footprints(ref_to_fp: dict[str, str]) -> list[tuple[str, list[str]]]:
    groups: dict[str, list[str]] = {}
    for ref in FOOTPRINT_REFS:
        groups.setdefault(ref_to_fp[ref], []).append(ref)
    assert len(groups) == 28, f"G-3 footprint count changed: {len(groups)}"
    return list(groups.items())


def part_svg(fp_id: str, refs: list[str], index: int, x: float, y: float) -> str:
    lib, name = fp_id.split(":", 1)
    footprint = pcbnew.FootprintLoad(str(library_path(lib)), name)
    assert footprint is not None, fp_id
    graphics = "\n".join(filter(None, (fab_svg(item) for item in footprint.GraphicalItems())))
    pads = "\n".join(
        pad_svg(pad)
        for pad in sorted(footprint.Pads(), key=lambda p: (p.GetNumber() == "", p.GetNumber()))
    )
    label = escape(refs[0] + (f" +{len(refs)-1}" if len(refs) > 1 else ""))
    return f'''<g>
<title>{escape(', '.join(refs))}: {escape(fp_id)}</title>
<text x="{n(x)}" y="{n(y-13)}" class="ref">{index:02d} · {label}</text>
<g transform="translate({n(x)} {n(y)})">
{graphics}
{pads}
</g>
</g>'''


def main() -> None:
    grouped = group_footprints(assembly_footprints())
    connectors = [(fp, refs) for fp, refs in grouped if refs[0] in CONNECTORS]
    others = [(fp, refs) for fp, refs in grouped if refs[0] not in CONNECTORS]
    assert len(connectors) == 3 and len(others) == 25
    drawings = []
    for offset, (fp, refs) in enumerate(others):
        row, column = divmod(offset, 5)
        drawings.append(part_svg(fp, refs, offset + 4, 25 + column * 39, 56 + row * 41))
    SVG.write_text(
        '''<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">
<style>
  .body { fill: none; stroke: #666; stroke-width: 0.13; }
  .ref { font: 2.5px sans-serif; fill: #111; }
  .note { font: 2.7px sans-serif; fill: #111; }
</style>
<rect x="0" y="0" width="210" height="297" fill="white"/>
<text x="15" y="17" style="font: 5px sans-serif">G-3 part overlay — REVIEW ONLY — actual size</text>
<text x="15" y="25" class="note">Print at 100% / Actual Size. Measure the 10 mm bar before overlaying samples.</text>
<line x1="165" y1="33" x2="175" y2="33" stroke="#111" stroke-width="0.4"/>
<line x1="165" y1="31" x2="165" y2="35" stroke="#111" stroke-width="0.2"/>
<line x1="175" y1="31" x2="175" y2="35" stroke="#111" stroke-width="0.2"/>
<text x="165" y="39" class="note">10 mm reference</text>
'''
        + "\n".join(drawings)
        + '''
<text x="15" y="267" class="note">Match each cell number to the checklist. Check pad overlap, pin 1, holes and body clearance.</text>
<text x="15" y="275" class="note">Sample IDs / date / reviewer: __________________________________________________________</text>
</svg>
''',
        encoding="utf-8",
    )
    lines = [
        "# G-3 overlay index — design set v1.1",
        "",
        "Print both review-only SVGs at 100% / Actual Size. First measure each 10 mm bar. "
        "Place a real part on each 1:1 footprint and check that every terminal overlaps "
        "its pad by at least 0.1 mm on each side, that pin-1/polarity marks and body "
        "orientation agree, and that slots/peg holes clear the part. Record deviations "
        "in `G3_OVERLAY_CHECKLIST.md` before routing. The printed sheets are review "
        "aids, not fabrication outputs.",
        "",
        "Use manufacturer dimensions or a calibrated optical/CAD overlay for 0.4/0.5 mm "
        "pitch and the 0.1 mm overlap limit; a normal paper print cannot certify that "
        "margin on its own.",
        "",
        "| Cell | References represented by one land pattern | KiCad footprint |",
        "| --- | --- | --- |",
    ]
    for index, (fp, refs) in enumerate(grouped, 1):
        lines.append(f"| {index:02d} | {', '.join(refs)} | `{fp}` |")
    lines += [
        "",
        "Cells 01–03 are on `G3_CONNECTOR_OVERLAY_REVIEW_ONLY.svg`; cells 04–28 "
        "are on `G3_PART_OVERLAY_REVIEW_ONLY.svg`. For X201, also overlay the "
        "specified NDK second source. For U613–U620, the TI DGK drawing and JLCPCB "
        "3D preview can replace physical samples per Notes §9.6. Record the U202 "
        "exposed-pad size and net; X-ray is an assembly review, not a paper-overlay result.",
        "",
    ]
    INDEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {SVG.name} and {INDEX.name} for {len(grouped)} unique footprints")


if __name__ == "__main__":
    main()
