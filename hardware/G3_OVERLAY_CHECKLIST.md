# G-3 overlay checklist — design set v1.1

Print both review-only SVGs at 100% / Actual Size. First measure each 10 mm bar. Place a real part on each 1:1 footprint and check that every terminal overlaps its pad by at least 0.1 mm on each side, that pin-1/polarity marks and body orientation agree, and that slots/peg holes clear the part. Record deviations before routing. Use the generated `G3_OVERLAY_INDEX.md` to identify each cell. This checklist is editable; the generated index and SVGs are review aids, not fabrication outputs.

For 0.4/0.5 mm pitch and the 0.1 mm overlap limit, use manufacturer dimensions or a calibrated optical/CAD overlay; an ordinary paper print alone cannot certify that margin.

| Cell | Physical sample ID(s) | Overlap, pin-1, hole and body observations | Pass/fail or measured mismatch |
| --- | --- | --- | --- |
| 01 |  |  |  |
| 02 |  |  |  |
| 03 |  |  |  |
| 04 |  |  |  |
| 05 |  |  |  |
| 06 |  |  |  |
| 07 |  |  |  |
| 08 |  |  |  |
| 09 |  |  |  |
| 10 |  |  |  |
| 11 |  |  |  |
| 12 |  |  |  |
| 13 |  |  |  |
| 14 |  |  |  |
| 15 |  |  |  |
| 16 |  |  |  |
| 17 |  |  |  |
| 18 |  |  |  |
| 19 |  |  |  |
| 20 |  |  |  |
| 21 |  |  |  |
| 22 |  |  |  |
| 23 |  |  |  |
| 24 |  |  |  |
| 25 |  |  |  |
| 26 |  |  |  |
| 27 |  |  |  |
| 28 |  |  |  |

Cells 01–03 are on `G3_CONNECTOR_OVERLAY_REVIEW_ONLY.svg`; cells 04–28 are on `G3_PART_OVERLAY_REVIEW_ONLY.svg`. For X201, also overlay the specified NDK second source. For U613–U620, the TI DGK drawing and JLCPCB 3D preview can replace physical samples per Notes §9.6. Record the U202 exposed-pad size and net; X-ray is an assembly review, not a paper-overlay result.

Printed 10 mm bar: ______ mm. Review date: __________. Reviewer/signature: ____________________.

JLCPCB DFM response for enlarged J701/J702 copper, ≥0.31 mm worst ring under +0.13 mm slot tolerance, and the 0.25 mm J701 pad-to-pad gap: ______________________________________________________________.
