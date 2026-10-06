# G-3 overlay index — design set v1.1-ECO1

Print both review-only SVGs at 100% / Actual Size. First measure each 10 mm bar. Place a real part on each 1:1 footprint and check that every terminal overlaps its pad by at least 0.1 mm on each side, that pin-1/polarity marks and body orientation agree, and that slots/peg holes clear the part. Record deviations in `G3_OVERLAY_CHECKLIST.md` before routing. The printed sheets are review aids, not fabrication outputs.

Use manufacturer dimensions or a calibrated optical/CAD overlay for 0.4/0.5 mm pitch and the 0.1 mm overlap limit; a normal paper print cannot certify that margin on its own.

| Cell | References represented by one land pattern | KiCad footprint |
| --- | --- | --- |
| 01 | J101 | `DAC_HPA:J101_USB4105-GF-A_12lands_4stakes` |
| 02 | J701 | `DAC_HPA:J701_GT-3321667P-01_maker_slots` |
| 03 | J702 | `DAC_HPA:J702_PJ-332A-6A_peg_holes` |
| 04 | K601, K602, K603, K604 | `DAC_HPA:K601_TLP3545A_LF1_HandSolder` |
| 05 | X201 | `DAC_HPA:X201_KC2520K80_Kyocera` |
| 06 | X202, X203 | `DAC_HPA:X202_X203_NDK_NZ2520SDA` |
| 07 | U503 | `DAC_HPA:ESOP-8_L4.9-W3.9-P1.27-LS6.0-BL-EP_PAD` |
| 08 | U103 | `JLC_Imported:SOT-553-5_L1.6-W1.2-P0.50-LS1.6-TL-1` |
| 09 | U206 | `JLC_Imported:SC-88-6_L2.0-W1.3-P0.65-LS2.1-BL` |
| 10 | D705 | `JLC_Imported:LED0805-R-RD` |
| 11 | D706 | `JLC_Imported:LED-SMD_L1.6-W0.8-R-RD` |
| 12 | D102 | `DAC_HPA:D102_SMDJ12A_HandSolder` |
| 13 | D104, D105 | `JLC_Imported:SOT-23_L2.9-W1.3-P1.90-LS2.4-BR` |
| 14 | D411, D412 | `JLC_Imported:SOD-123F_L2.8-W1.8-LS3.7-RD` |
| 15 | C442, C443 | `JLC_Imported:CASE-D_7343` |
| 16 | U208 | `JLC_Imported:VSSOP-8_L2.1-W2.4-P0.50-LS3.2-BR` |
| 17 | U605 | `JLC_Imported:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL` |
| 18 | U606, U609, U610, U611, U612 | `JLC_Imported:TSSOP-14_L5.0-W4.4-P0.65-LS6.4-BL` |
| 19 | U607 | `JLC_Imported:TSSOP-5_L2.1-W1.3-P0.65-LS2.2-BR` |
| 20 | D609, D610, Q207, Q619, Q620, Q507, Q621, Q622 | `JLC_Imported:SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR` |
| 21 | U502 | `JLC_Imported:SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR` |
| 22 | U608 | `JLC_Imported:VSSOP-8_L2.3-W2.0-P0.50-LS3.1-BR` |
| 23 | Q623, Q624, Q625, Q626, Q627 | `JLC_Imported:SOT-23-3_L2.9-W1.6-P1.90-LS2.8-BR` |
| 24 | C631, C632, C633, C634 | `DAC_HPA:C631_ECHU1H224GX9_D4` |
| 25 | C647, C648, C649, C650, C651, C652, C653, C654 | `Capacitor_SMD:C_1206_3216Metric` |
| 26 | U613, U614, U615, U616, U617, U618, U619, U620 | `JLC_Imported:VSSOP-8_L3.0-W3.0-P0.65-LS5.0-BL` |
| 27 | U202 | `DAC_HPA:QFN-32_L4.0-W4.0-P0.40-BL-EP2.7_EP` |
| 28 | D405, D406, D407, D408 | `JLC_Imported:SOT-23-3_L3.0-W1.7-P0.95-LS2.9-BR` |
| 29 | U621 | `JLC_Imported:SC-70-6_L2.2-W1.3-P0.65-LS2.1-BL` |
| 30 | D701, D707, D708 | `JLC_Imported:SOD-523_L1.2-W0.8-LS1.6-BI` |

Cells 01–03 are on `G3_CONNECTOR_OVERLAY_REVIEW_ONLY.svg`; cells 04–30 are on `G3_PART_OVERLAY_REVIEW_ONLY.svg`. For X201, also overlay the specified NDK second source. For U613–U620, the TI DGK drawing and JLCPCB 3D preview can replace physical samples per Notes §9.6. Record the U202 exposed-pad size and net. For U621, compare the TI DCK example land to the exact JLC C507231 land before order. X-ray is an assembly review, not a paper-overlay result.
