# DAC-HPA historical 100 × 100 placement snapshot

This generated report predates the owner-approved J703 PCB-pad removal and 120 × 100 mm manual primary. Its 537-item and primary-outline labels below are historical. Use `PLACEMENT_100x100_BASELINE_AUDIT.json` for the current 536-footprint baseline comparison and `MANUAL_PLACEMENT_REVIEW.md` for the current primary.

- Schematic footprint items: **537** (including 7 fiducials)
- Electrical nets: **246**
- Explicitly positioned items: **96**
- Coordinate origin: lower-left of the 100 × 100 mm board. This is the owner-selected primary outline.
- The two 5 mm V-cut panel rails are not part of this main-board outline; JLCPCB adds them at panelization.
- Placement script: `place_board.py`; it refuses to replace an existing board without `--force`.

## Principal positions (mm from lower-left)

| Ref | x | y | Rotation |
| --- | ---: | ---: | ---: |
| J101 | 5.00 | 65.00 | 270° |
| U201 | 25.00 | 77.00 | 0° |
| U202 | 42.00 | 76.00 | 0° |
| U301 | 50.00 | 59.00 | 0° |
| X201 | 50.00 | 49.50 | 0° |
| U403 | 52.75 | 64.50 | 90° |
| U404 | 55.50 | 58.50 | 0° |
| U401 | 72.20 | 67.00 | 0° |
| U402 | 71.20 | 54.00 | 0° |
| J701 | 86.50 | 64.00 | 180° |
| J702 | 90.84 | 30.50 | 180° |
| K601 | 80.00 | 48.50 | 180° |
| K602 | 77.00 | 79.60 | 180° |
| K603 | 93.30 | 48.50 | 180° |
| K604 | 90.30 | 79.60 | 180° |
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
| FID2 | 8.00 | 90.00 |
| FID3 | 88.00 | 7.50 |
| FID4 | 36.00 | 92.00 |
| FID5 | 44.00 | 93.00 |
| FID6 | 15.50 | 78.00 |
| FID7 | 13.00 | 83.00 |

## Region spills

Some footprint centers moved beyond their preferred functional region to avoid occupied courtyards:

| Ref | Preferred | Placed in |
| --- | --- | --- |
| C308 | Z4L | Z4U |
| C309 | Z4L | Z4U |

The board remains provisional; routing, copper pours, silkscreen, impedance and assembly outputs are outside this placement artifact.
