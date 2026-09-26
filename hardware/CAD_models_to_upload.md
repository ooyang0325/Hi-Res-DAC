# CAD files and measurements still useful

The command-line JLCPCB KiCad loader supplied 39 LCSC models. Manufacturer drawings supplied the remaining 2D land dimensions for D102, X201–X203, C631–C634, and K601–K604. Those custom KiCad footprints are assigned and pass the symbol-pin/pad-number check. **No CAD upload is needed to continue schematic capture.**

If you have them, the following files would help with the later G-3 physical overlay and 3D review. STEP is optional for the schematic; a model does not replace the sample checks.

| Designators | Exact MPN | Optional upload |
| --- | --- | --- |
| D102 | Littelfuse SMDJ12A | Manufacturer STEP or exact package model |
| X201 | Kyocera KC2520K80.0000C1GE00 | Manufacturer STEP |
| X202 | NDK NZ2520SDA-49.152MHZ-NSC5083D | Manufacturer STEP |
| X203 | NDK NZ2520SDA-45.1584MHZ-NSC5083D | Manufacturer STEP; X202 geometry may be reused after checking |
| C631–C634 | Panasonic ECH-U1H224GX9 | Manufacturer STEP |
| K601–K604 | Toshiba TLP3545A(TP1,F) | Manufacturer STEP for the **LF1** lead form |

## Physical and electrical decisions still required

- **J101:** The GCT USB4105 drawing has 12 PCB solder lands, four shell stakes, and two locating holes. JLCPCB C3020560 CAD splits four paired solder lands into separate pad IDs. The project footprint follows GCT's composite 12-land map and remains provisional until G-1/G-3 sample checks.
- **J701:** The owner approved the 12-pad G-Switch/JLC map, and the JLCPCB C2762984 footprint is now assigned in KiCad. The drawing names electrical contacts 1–10; JLC names 11/12 `ep`, whose physical role remains unverified. The two-sample G-2 continuity and G-3 hole/peg overlay gates remain open; a CAD upload alone will not settle them.
- **J702:** JLCPCB C2848643 CAD has six pads, but the HRO drawing does not support the workbook's assumption that pins 5 and 6 are GND-only mounting pads. G-2 continuity on two physical samples is needed.

Do not release PCB manufacturing or PCBA data from the provisional connector mapping.
