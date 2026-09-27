#!/usr/bin/env python3
"""Derive review-only jack footprints from the JLC CAD and maker dimensions.

The JLC import draws the locating holes as graphics rather than drill objects.
J701 also uses larger copper and slots than the maker dimensions recorded in
Design Spec v1.1. The owner subsequently chose a copper-only enlargement to
meet the design's 0.30 mm ring rule at the stated slot tolerance. This script
preserves the imported pad centres and slot drills, replaces hole graphics
with Ø1.20 mm NPTH pads, and applies the approved copper sizes. G-3 overlays
and JLCPCB DFM confirmation remain required.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "JLC_Imported.pretty"
TARGET = HERE / "DAC_HPA.pretty"


def block_end(source: str, start: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("Unclosed KiCad footprint block")


def transform_blocks(source: str, kind: str, transform) -> tuple[str, int]:
    starts = [match.start() + 2 for match in re.finditer(rf"\n\t\({kind}(?=\s)", source)]
    changed = 0
    for start in reversed(starts):
        end = block_end(source, start)
        before = source[start:end]
        after = transform(before)
        if before != after:
            source = source[:start] + after + source[end:]
            changed += 1
    return source, changed


def hole(x: float, y: float, ref: str, index: int) -> str:
    identity = uuid.uuid5(uuid.NAMESPACE_URL, f"hi-res-dac/{ref}/locating-hole/{index}")
    return (
        f'\n\t(pad "" np_thru_hole circle\n'
        f'\t\t(at {x:g} {y:g})\n'
        '\t\t(size 1.2 1.2)\n'
        '\t\t(drill 1.2)\n'
        '\t\t(layers "*.Cu" "*.Mask")\n'
        f'\t\t(uuid "{identity}")\n'
        '\t)'
    )


def drop_hole_graphic(block: str) -> str:
    if '(layer "Edge.Cuts")' in block and block.startswith('(fp_poly'):
        return ""
    if '(layer "Dwgs.User")' in block and block.startswith('(fp_circle'):
        return ""
    return block


def convert(source_name: str, target_name: str, holes: list[tuple[float, float]], j701: bool) -> None:
    original = (SOURCE / f"{source_name}.kicad_mod").read_text(encoding="utf-8")
    assert original.startswith(f'(footprint "{source_name}"'), source_name
    result = original.replace(f'(footprint "{source_name}"', f'(footprint "{target_name}"', 1)
    result, removed_polys = transform_blocks(result, "fp_poly", drop_hole_graphic)
    assert removed_polys == 2, (source_name, removed_polys)
    if not j701:
        result, removed_circles = transform_blocks(result, "fp_circle", drop_hole_graphic)
        assert removed_circles == 2, (source_name, removed_circles)
        # The import also draws a partial board-edge guide. Keep it visible to
        # the layout engineer without turning it into fabrication Edge.Cuts.
        def drawing_guide(block: str) -> str:
            return block.replace('(layer "Edge.Cuts")', '(layer "Dwgs.User")')

        result, moved_guides = transform_blocks(result, "fp_line", drawing_guide)
        assert moved_guides == 3, (source_name, moved_guides)

    if j701:
        def approved_slot(block: str) -> str:
            if not re.match(r'\(pad "(?:[1-9]|1[0-2])" thru_hole oval', block):
                return block
            updated, size_count = re.subn(r'\(size 2 (?:1\.4|1\.3)\)', '(size 2 1.2)', block, count=1)
            updated, drill_count = re.subn(r'\(drill oval 1\.4 0\.6\)', '(drill oval 1.4 0.5)', updated, count=1)
            assert (size_count, drill_count) == (1, 1), block[:80]
            return updated

        result, changed = transform_blocks(result, "pad", approved_slot)
        assert changed == 12, changed
    else:
        def approved_slot(block: str) -> str:
            if not re.match(r'\(pad "[12]" thru_hole oval', block):
                return block
            updated, size_count = re.subn(r'\(size 1 1\.9\)', '(size 1.2 2.1)', block, count=1)
            assert size_count == 1, block[:80]
            return updated

        result, changed = transform_blocks(result, "pad", approved_slot)
        assert changed == 2, changed

    additions = "".join(hole(x, y, target_name, index) for index, (x, y) in enumerate(holes, 1))
    assert result.count("\n\t(embedded_fonts no)") == 1
    result = result.replace("\n\t(embedded_fonts no)", additions + "\n\t(embedded_fonts no)", 1)
    result = re.sub(r"(?m)^[\t ]+$", "", result)
    (TARGET / f"{target_name}.kicad_mod").write_text(result, encoding="utf-8")
    print(f"Derived {target_name}: {2 if j701 else 4} hole graphics removed, {len(holes)} NPTH holes added")


if __name__ == "__main__":
    convert("AUDIO-TH_GT-3321667P-01", "J701_GT-3321667P-01_maker_slots", [(-3.55, 0), (3.95, -1.55)], True)
    convert("AUDIO-SMD_PJ-332A-6A", "J702_PJ-332A-6A_peg_holes", [(-4.275, -0.05), (2.725, -0.05)], False)
