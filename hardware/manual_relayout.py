#!/usr/bin/env python3
"""Apply engineer-selected footprint coordinates to the current review board.

This file deliberately contains no placement search, packing, scoring, or
collision resolution. Every coordinate below is chosen during a visual review
of the KiCad copper, fab, and courtyard layers. Run the independent audits
after each manual iteration; a successful save does not imply routability.
"""

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_100x100_BASELINE_REVIEW_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_MANUAL_REVIEW_ONLY.kicad_pcb"
BOARD_X = 40.0
BOARD_Y = 40.0
BOARD_HEIGHT = 100.0

# Position is (x, y) in millimetres from the board's lower-left corner.
# Slow relay-control devices move away from the J701/J702 L1 output corridors.
MOVES: dict[str, tuple[float, float, int]] = {
    # K603 can move towards J701 without narrowing K601's separate L-channel
    # courtyard or approaching J702; this gives the RP ESD route margin.
    "K603": (92.2, 48.7, 180),
    "Q612": (78.0, 18.0, 0),
    "Q614": (83.0, 18.0, 0),
    "Q616": (88.0, 18.0, 0),
    "Q617": (93.0, 18.0, 0),
    "Q622": (93.0, 12.0, 0),
    "D705": (78.0, 12.0, 0),
    "D706": (83.0, 12.0, 0),
    "R692": (88.0, 13.0, 0),
    "R696": (88.0, 11.0, 0),
    "R937": (77.0, 22.5, 0),
    "R950": (80.0, 22.5, 0),
    # Pull-ups leave J701's 0.5 mm signal exits. The first four form one
    # quiet control row; each timing resistor sits beside its film capacitor.
    "R916": (66.0, 18.0, 0),
    "R917": (68.8, 18.0, 0),
    "R918": (71.6, 18.0, 0),
    "R919": (74.4, 18.0, 0),
    "R920": (64.0, 15.0, 0),
    "R921": (65.9, 6.0, 0),
    "R922": (60.0, 32.3, 0),
    "R923": (39.0, 3.2, 0),
    # The two positive-channel ESD paths approach the lower J701 contacts.
    # This is a routing study; the J701 hand-solder access conflict remains.
    "D701": (80.35, 57.8, 0),
    "D702": (89.5, 58.0, 0),
    # Bring the four far-flung persistence dividers back near the lower
    # protection comparators in a regular two-by-two row.
    "R902": (69.0, 10.0, 0),
    "R903": (73.2, 10.0, 0),
    "R906": (69.0, 13.0, 0),
    "R907": (73.2, 13.0, 0),
    "R701": (74.5, 16.0, 0),
    "R908": (69.5, 6.0, 0),
    "R909": (73.5, 6.0, 0),
    "R912": (69.5, 3.5, 0),
    "R913": (73.5, 3.5, 0),
    "R924": (64.5, 31.5, 0),
    "R925": (67.0, 31.5, 0),
    "R928": (85.5, 22.5, 0),
    "R936": (79.0, 25.0, 0),
    "R929": (83.0, 22.5, 0),
    "R910": (78.0, 5.5, 0),
    "R911": (82.0, 5.5, 0),
    "R914": (78.0, 8.5, 0),
    "R915": (82.0, 8.5, 0),
    # Film-capacitor solder access is checked against the existing nearby
    # comparators and small parts. These moves preserve the maker land.
    "C631": (58.4, 14.4, 90),
    "C632": (58.3, 5.4, 0),
    "C633": (60.0, 36.7, 0),
    "C634": (46.6, 7.0, 0),
    "C641": (53.8, 10.5, 90),
    # Bring the LPW input capacitor and local supply bypass inside JLC's
    # component-body edge envelope while preserving their U613/U614 cluster.
    "C643": (52.0, 96.6, 90),
    "C659": (51.5, 94.0, 90),
    "R930": (52.0, 91.5, 90),
    # Small body-gap corrections visible in the 1:1 JLC package screening.
    "R109": (13.5, 51.8, 90),
    "Q504": (12.0, 10.7, 0),
    "C506": (18.9, 13.5, 90),
    # Keep the shell-to-GND link close to J101 while clearing the PCB edge.
    "R107": (3.0, 59.0, 90),
    "R104": (4.3, 59.0, 90),
    # Keep the 80 MHz clock-monitor rectifier away from the protection
    # high-impedance pads and closer to U607's buffered output.
    "D609": (46.0, 41.5, 0),
    "C624": (46.5, 43.9, 0),
    "TP708": (50.0, 43.0, 0),
    # The VLLP shunt belongs beside the upper low-power comparators, not the
    # BCLK test pad in the digital/analog boundary.
    "R939": (44.0, 90.0, 90),
    "R684": (39.6, 46.0, 0),
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
            pcbnew.FromMM(BOARD_X + x),
            pcbnew.FromMM(BOARD_Y + BOARD_HEIGHT - y),
        ))
    pcbnew.SaveBoard(str(OUTPUT), board)
    print(f"Saved {OUTPUT.name} with {len(MOVES)} explicit footprint moves")


if __name__ == "__main__":
    main()
