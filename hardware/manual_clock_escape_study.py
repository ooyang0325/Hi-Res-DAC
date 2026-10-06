#!/usr/bin/env python3
"""Hand-place the I2S series parts in the freed J703 area for EMI review."""

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_120x100_TOP_ACCESS_STUDY_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_120x100_CLOCK_ESCAPE_STUDY_ONLY.kicad_pcb"

# These are manually selected board-local millimetres. No search is run.
MOVES: dict[str, tuple[float, float, int]] = {
    "R204": (39.3, 67.5, -90),
    "R205": (41.5, 72.0, -90),
    "R206": (38.5, 73.2, -90),
    "TP712": (39.5, 70.8, 0),
    "TP716": (36.5, 70.5, 0),
    "R215": (38.5, 75.3, 90),
    "U615": (49.0, 87.0, 0),
    "C649": (44.5, 88.0, 0),
    "C647": (44.0, 91.0, 0),
    "C648": (61.5, 94.0, 0),
    "C661": (51.5, 87.0, 90),
    "R938": (52.5, 89.0, 0),
    "R939": (54.5, 89.0, 90),
    "R446": (37.0, 88.0, 90),
    "R447": (39.0, 88.0, 90),
    "FID5": (37.0, 92.5, 0),
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
