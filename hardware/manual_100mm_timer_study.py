#!/usr/bin/env python3
"""Test an explicit, hand-arranged 100 x 100 mm timer floorplan.

Every coordinate is chosen from a close-up of the current KiCad board. This
script does not search, pack, score, or automatically move other footprints.
"""

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_MANUAL_REVIEW_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_100x100_TIMER_STUDY_ONLY.kicad_pcb"

# Board-local millimetres from lower left. U609's timing pair sits above it;
# U610 is rotated so its pair fits below. All four branches remain separate.
MOVES: dict[str, tuple[float, float, int]] = {
    "U609": (59.0, 23.95, 0),
    "U610": (78.8, 25.0, 180),
    "C631": (63.7, 34.45, 90),
    "C632": (57.2, 34.45, 90),
    "C633": (74.6, 14.2, 270),
    "C634": (80.8, 14.2, 270),
    "Q623": (66.8, 25.0, 0),
    "Q624": (54.0, 25.0, 180),
    "Q625": (68.65, 21.25, 180),
    "Q626": (86.9, 22.5, 0),
    "R920": (64.0, 27.3, 0),
    "R921": (54.0, 27.3, 0),
    "R922": (74.8, 21.3, 0),
    "R923": (83.2, 21.3, 0),
    "R916": (62.2, 18.0, 0),
    "R917": (64.7, 18.0, 0),
    "R918": (67.2, 18.0, 0),
    "R919": (69.7, 18.0, 0),
    "R924": (68.5, 38.0, 0),
    "R925": (71.0, 38.0, 0),
    # Slow control and LED devices give up the timer keepout and form rows
    # below the jack. None enter the manually reserved headphone passages.
    "U608": (55.0, 6.0, 0),
    "Q612": (91.5, 11.0, 0),
    "Q614": (87.0, 13.0, 0),
    "Q616": (91.5, 16.0, 0),
    "Q617": (87.0, 18.0, 0),
    "Q622": (91.5, 21.0, 0),
    "D705": (60.0, 4.0, 0),
    "D706": (66.0, 4.0, 0),
    "R701": (51.0, 4.0, 0),
    "FID3": (87.0, 5.5, 0),
    "R702": (64.0, 7.0, 90),
    "R691": (58.0, 8.0, 90),
    "TP718": (48.0, 5.0, 0),
    "TP743": (79.0, 34.0, 0),
    "TP744": (77.0, 34.0, 0),
    "TP745": (69.2, 40.0, 0),
    "R692": (95.0, 11.0, 0),
    "R696": (95.0, 14.0, 0),
    "R928": (80.1, 36.5, 0),
    "R929": (82.5, 36.5, 0),
    "R936": (79.0, 39.4, 0),
    "R937": (81.5, 39.4, 0),
    "R950": (84.0, 39.4, 0),
    "R926": (77.5, 36.5, 0),
    "R904": (71.8, 36.0, 0),
    "R905": (71.8, 33.0, 0),
    "R934": (82.0, 33.5, 0),
    "R935": (82.0, 31.0, 0),
    "R951": (79.0, 31.0, 0),
    "R662": (51.5, 20.0, 0),
    "R663": (55.5, 18.5, 90),
    "R903": (65.0, 10.0, 0),
    "R907": (65.0, 13.0, 0),
    "R910": (78.0, 3.5, 0),
    "R911": (82.0, 3.5, 0),
    "R914": (78.0, 6.7, 0),
    "R915": (82.0, 6.7, 0),
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
