#!/usr/bin/env python3
"""Create an explicit 120 x 100 mm hand-placement comparison.

The right edge and the specified connector/output components move 20 mm to
the right. Their coordinates are written out below; no placement optimizer,
packing search, or collision resolution is run. This keeps both audio jacks
at their required panel edge and leaves a wider analog-to-output passage.
"""

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_100x100_TIMER_STUDY_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_120x100_MANUAL_STUDY_ONLY.kicad_pcb"

# (x, y, rotation) in millimetres from the unchanged lower-left corner.
MOVES: dict[str, tuple[float, float, int]] = {
    "J701": (106.5, 64.0, 180),
    "J702": (110.84, 30.5, 180),
    "K601": (100.0, 48.5, 180),
    "K602": (97.0, 79.6, 180),
    "K603": (112.2, 48.7, 180),
    "K604": (110.3, 79.6, 180),
    "D701": (100.35, 57.8, 0),
    "D702": (109.5, 58.0, 0),
    "D703": (107.9, 70.2, 0),
    "D704": (113.7, 70.2, 0),
    "R926": (97.5, 36.5, 0),
    "R928": (100.1, 36.5, 0),
    "R929": (102.5, 36.5, 0),
    "FID3": (107.0, 5.5, 0),
    "FID4": (105.0, 92.0, 0),
    "MH3": (116.5, 3.5, 0),
    "MH4": (116.5, 96.5, 0),
}


def main() -> None:
    board = pcbnew.LoadBoard(str(SOURCE))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    if len(footprints) != 536:
        raise SystemExit(f"Unexpected source footprint count: {len(footprints)}")
    for drawing in board.GetDrawings():
        if drawing.GetLayer() != pcbnew.Edge_Cuts:
            continue
        start = drawing.GetStart()
        end = drawing.GetEnd()
        for point in (start, end):
            old_x = pcbnew.ToMM(point.x)
            if old_x in (139.0, 140.0):
                point.x = pcbnew.FromMM(old_x + 20.0)
        drawing.SetStart(start)
        drawing.SetEnd(end)
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
