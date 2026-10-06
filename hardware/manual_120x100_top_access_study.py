#!/usr/bin/env python3
"""Test top-side J701 iron access on the 120 x 100 mm hand placement.

The four TVS diodes move outside J701's 1.5 mm courtyard access region;
the nearby owner-fitted relays move to retain their own 1.5 mm access. This
is a geometry study of the conflict with the current 3 mm TVS rule, not an
approved change to that electrical requirement or a routed PCB.
"""

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_120x100_MANUAL_STUDY_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_120x100_TOP_ACCESS_STUDY_ONLY.kicad_pcb"

MOVES: dict[str, tuple[float, float, int]] = {
    "D701": (100.35, 56.72, 0),
    "D702": (108.85, 56.72, 0),
    "D703": (108.3, 71.28, 0),
    "D704": (113.7, 71.28, 0),
    "K601": (100.0, 47.3, 180),
    "K603": (112.2, 47.3, 180),
    "K604": (110.3, 80.6, 180),
}


def main() -> None:
    board = pcbnew.LoadBoard(str(SOURCE))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    if len(footprints) != 536:
        raise SystemExit(f"Unexpected source footprint count: {len(footprints)}")
    for ref, (x, y, angle) in MOVES.items():
        footprint = footprints[ref]
        footprint.SetOrientationDegrees(angle)
        footprint.SetPosition(pcbnew.VECTOR2I(
            pcbnew.FromMM(40.0 + x),
            pcbnew.FromMM(140.0 - y),
        ))
    pcbnew.SaveBoard(str(OUTPUT), board)
    print(f"Saved {OUTPUT.name} with {len(MOVES)} explicit footprint coordinates")


if __name__ == "__main__":
    main()
