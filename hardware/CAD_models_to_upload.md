# CAD files and measurements still useful

The command-line JLCPCB KiCad loader supplied 41 LCSC CAD entries, including the new TI TLV3402IDGKR and onsemi MMBT3904LT1G. Manufacturer drawings supplied the 2D land dimensions for D102, X201–X203, C631–C634, K601–K604 and the connector slot corrections. All assigned footprints pass the symbol-pin/pad-number check. **No CAD upload is needed to continue schematic capture.**

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

- **J101:** The GCT USB4105 drawing has 12 PCB solder lands, four shell stakes, and two locating holes. JLCPCB C3020560 CAD splits four paired solder lands into separate pad IDs. The project footprint follows GCT's composite 12-land map. The owner reports both G-1 samples match but waived the raw log; G-3 physical overlay remains open.
- **J701:** Parts List v0.9 carries the approved 12-pad G-Switch map. The custom footprint keeps the maker slots and pad centres, enlarges copper for ≥0.31 mm worst ring under JLC's +0.13 mm slot tolerance, and adds two NPTH peg holes. Pads 11/12 are soldered mounting tabs with no-connect flags. The owner reports two-sample G-2 continuity (tabs common with bushing and isolated from sleeve); G-3 still checks the physical overlay and enlarged copper.
- **J702:** Parts List v0.9 carries the HRO maker map: pins 1/2 GND, 3 `JACK_RP`, 4 `JACK_LP`, and 5/6 break contacts with no-connect flags. The custom footprint keeps the slots and pad centres, enlarges copper for a 0.30 mm ring, and adds two NPTH peg holes. The owner reports both samples match the TRS contact and break behavior and waived the G-2 raw log; G-3 overlay and G-6 slot soldering remain open.

Do not release PCB manufacturing or PCBA data from the provisional connector mapping.
