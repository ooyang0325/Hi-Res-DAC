# DAC-HPA historical 100 × 80 comparison placement

This generated report predates the owner-approved J703 PCB-pad removal. Its 537-item count below is historical. Use `PLACEMENT_100x80_AUDIT.json` for the current 536-footprint comparison.

- Schematic footprint items: **537** (including 7 fiducials)
- Electrical nets: **246**
- Explicitly positioned items: **95**
- Coordinate origin: lower-left of the 100 × 80 mm board. This smaller outline is retained for comparison.
- The two 5 mm V-cut panel rails are not part of this main-board outline; JLCPCB adds them at panelization.
- Placement script: `place_board.py`; it refuses to replace an existing board without `--force`.

## Principal positions (mm from lower-left)

| Ref | x | y | Rotation |
| --- | ---: | ---: | ---: |
| J101 | 5.00 | 50.00 | 270° |
| U201 | 25.00 | 67.00 | 0° |
| U202 | 42.00 | 66.00 | 0° |
| U301 | 50.00 | 49.00 | 0° |
| X201 | 50.00 | 39.50 | 0° |
| U403 | 52.75 | 54.50 | 90° |
| U404 | 55.50 | 48.50 | 0° |
| U401 | 72.20 | 57.00 | 0° |
| U402 | 71.20 | 44.00 | 0° |
| J701 | 86.50 | 54.00 | 180° |
| J702 | 90.84 | 20.50 | 180° |
| K601 | 80.00 | 38.50 | 180° |
| K602 | 72.00 | 72.00 | 180° |
| K603 | 93.30 | 38.50 | 180° |
| K604 | 85.30 | 72.00 | 180° |
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
| FID4 | 36.00 | 73.00 |
| FID5 | 58.50 | 69.00 |
| FID6 | 15.50 | 63.00 |
| FID7 | 13.00 | 68.00 |

## Region spills

Some footprint centers moved beyond their preferred functional region to avoid occupied courtyards:

| Ref | Preferred | Placed in |
| --- | --- | --- |
| C305 | Z4L | Z4U |
| C306 | Z4L | Z4U |
| C307 | Z4L | Z4U |
| C308 | Z4L | Z4U |
| C309 | Z4L | Z4U |
| C649 | Z4U | Z4L |
| C650 | Z4U | Z4L |
| FB301 | Z4L | Z4U |
| FB302 | Z4L | Z4S |
| R446 | Z4U | Z4S |
| R447 | Z4U | Z4S |
| R676 | Z4S | Z4L |
| R679 | Z4S | Z4L |
| R680 | Z4S | Z4L |
| R681 | Z4S | Z4L |
| R682 | Z4S | Z4L |
| R683 | Z4S | Z7A |
| R685 | Z4S | Z7A |
| R686 | Z4S | Z7A |
| R687 | Z4S | Z7A |
| R688 | Z4S | Z7A |
| R689 | Z4S | Z7A |
| R938 | Z4L | Z4U |
| R939 | Z4L | Z4U |

The board remains provisional; routing, copper pours, silkscreen, impedance and assembly outputs are outside this placement artifact.
