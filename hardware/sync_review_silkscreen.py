#!/usr/bin/env python3
"""Copy three checked silkscreen clearances into embedded board footprints.

KiCad stores footprint graphics inside each PCB. This script changes only the
specified local silk primitives; it never moves a footprint or a pad.
"""

from __future__ import annotations

import re
from pathlib import Path

from derive_connector_footprints import block_end, clear_j702_slot_silk, transform_blocks


HERE = Path(__file__).resolve().parent
BOARDS = [
    "DAC_HPA.kicad_pcb",
    "DAC_HPA_100x80_REVIEW_ONLY.kicad_pcb",
    "DAC_HPA_MANUAL_REVIEW_ONLY.kicad_pcb",
    "DAC_HPA_100x100_TIMER_STUDY_ONLY.kicad_pcb",
    "DAC_HPA_120x100_MANUAL_STUDY_ONLY.kicad_pcb",
    "DAC_HPA_120x100_TOP_ACCESS_STUDY_ONLY.kicad_pcb",
    "DAC_HPA_120x100_CLOCK_ESCAPE_STUDY_ONLY.kicad_pcb",
]


def edit_footprint(source: str, name: str, editor) -> tuple[str, int]:
    token = f'(footprint "DAC_HPA:{name}"'
    start = source.find(token)
    if start < 0:
        raise ValueError(f"Missing embedded {name}")
    end = block_end(source, start)
    before = source[start:end]
    after, count = editor(before)
    return source[:start] + after + source[end:], count


def edit_d102(block: str) -> tuple[str, int]:
    pattern = r'(\(start )-4\.91( 3\.25\)\s*\(end )-4\.91( -3\.25\))'
    return re.subn(pattern, r'\g<1>-5.19\g<2>-5.19\g<3>', block, count=1)


def edit_x201(block: str) -> tuple[str, int]:
    pattern = r'(\(center -1\.4 )1\.3(\)\s*\(end -1\.3 )1\.3(\))'
    return re.subn(pattern, r'\g<1>1.65\g<2>1.65\g<3>', block, count=1)


def edit_j702(block: str) -> tuple[str, int]:
    return transform_blocks(block, "fp_line", clear_j702_slot_silk)


def main() -> None:
    for name in BOARDS:
        path = HERE / name
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        counts = []
        for footprint, editor in (
            ("D102_SMDJ12A_HandSolder", edit_d102),
            ("X201_KC2520K80_Kyocera", edit_x201),
            ("J702_PJ-332A-6A_peg_holes", edit_j702),
        ):
            source, count = edit_footprint(source, footprint, editor)
            if count not in ((0, 1) if footprint != "J702_PJ-332A-6A_peg_holes" else (0, 6)):
                raise ValueError(f"Unexpected {footprint} silk edit count {count} in {name}")
            counts.append(count)
        path.write_text(re.sub(r"(?m)^[\t ]+$", "", source), encoding="utf-8")
        print(name, counts)


if __name__ == "__main__":
    main()
