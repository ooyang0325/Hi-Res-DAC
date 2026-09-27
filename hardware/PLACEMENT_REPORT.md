# DAC-HPA provisional placement

This editable four-layer KiCad board places all schematic footprint items on a 100 × 80 mm R1 outline. The board has pad nets and schematic paths but no tracks or copper pours. The owner directed placement without the pre-layout physical checks; this board is not a manufacturing release.

- Schematic footprint items: **537** (including 7 fiducials)
- Electrical nets: **246**
- Anchored connectors, mounting holes, relays and principal ICs: **64**
- Coordinate origin: lower-left of the 100 × 80 mm board, as in Notes v1.0 §9.1.
- The two 5 mm V-cut panel rails are not part of this main-board outline; JLCPCB adds them at panelization.
- Placement script: `place_board.py`; it refuses to replace an existing board without `--force`.

## Principal positions (mm from lower-left)

| Ref | x | y | Rotation |
| --- | ---: | ---: | ---: |
| J101 | 5.00 | 50.00 | 270° |
| U201 | 25.00 | 67.00 | 0° |
| U202 | 42.00 | 66.00 | 0° |
| U301 | 50.00 | 49.00 | 0° |
| X201 | 50.00 | 38.50 | 0° |
| U403 | 60.00 | 57.00 | 0° |
| U404 | 60.00 | 44.00 | 0° |
| U401 | 70.00 | 57.00 | 0° |
| U402 | 70.00 | 44.00 | 0° |
| J701 | 86.50 | 58.50 | 180° |
| J702 | 90.84 | 16.50 | 180° |
| K601 | 80.00 | 29.50 | 0° |
| K602 | 80.00 | 45.00 | 0° |
| K603 | 93.00 | 29.50 | 0° |
| K604 | 93.00 | 45.00 | 0° |
| U503 | 14.00 | 18.00 | 0° |
| U603 | 42.00 | 27.00 | 0° |
| U606 | 49.00 | 27.00 | 0° |
| U609 | 57.00 | 25.00 | 0° |
| U610 | 65.00 | 25.00 | 0° |
| U611 | 42.00 | 15.00 | 0° |
| U612 | 50.00 | 15.00 | 0° |

## Fiducials

| Ref | x | y |
| --- | ---: | ---: |
| FID1 | 5.00 | 20.00 |
| FID2 | 8.00 | 70.00 |
| FID3 | 88.00 | 7.50 |
| FID4 | 36.00 | 72.00 |
| FID5 | 44.50 | 73.00 |
| FID6 | 15.50 | 61.00 |
| FID7 | 34.50 | 67.00 |

## Region spills

All non-test-pad footprint centers remained in their preferred region; some courtyards cross approximate region boundaries.

The board remains provisional; routing, copper pours, silkscreen, impedance and assembly outputs are outside this placement artifact.
