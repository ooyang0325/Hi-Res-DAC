# Source-document reconciliation for schematic capture

The workbook is the pin-by-pin connection source. Design Spec v1.0 and the detailed block/placement text in Schematic Design Notes v0.9 provide independent checks. The notes' Section 6 checklist contains a few earlier values that conflict with those current sources:

| Notes v0.9 location | Conflict | Capture used | Why |
| --- | --- | --- | --- |
| Section 6, rule 4 | Calls C102 4.7 µF. | C102 2.2 µF, 25 V. | Spec v1.0 input/suspend text, Notes v0.9 Sections 3.1 and 3.5, Parts List v0.8, and the short-circuit/inrush calculations all use 2.2 µF. |
| Section 6, rule 16 | Places R227 on `MCLK`, after R203. | R227 connects `N2_X201_OUT` to GND, at X201 pin 3 before R203. | Notes v0.9 clock-block and placement text specify R227 at X201 pin 3; Parts List v0.8 matches. |
| Section 9, clock-routing table | One row calls the R665 MCLK-alive tap 1 kΩ. | R665 330 Ω. | The ninth-round change, Notes v0.9 Sections 3.2/3.6/9.2, Spec v1.0, and Parts List v0.8 consistently use 330 Ω. |
| Section 6, rule 44 | Traces the series permit only through Q616 and Q617. | Q622 follows Q617 in the permit path. | Notes v0.9 rule 58 and the detailed new re-arm-latch section, Spec v1.0, and Parts List v0.8 all include Q622. |
| Parts List v0.8, C442/C443 Datasheet field | Names Kyocera AVX TAJD227K010RNJ but links a Kemet T495 page. | The KiCad property links the [KYOCERA AVX TAJ datasheet](https://datasheets.kyocera-avx.com/TAJ.pdf). | The specified MPN is a TAJ-series capacitor; its manufacturer's sheet identifies the polarity band as the anode (+). The JLC C8024 footprint band is at pad 1, matching the workbook's pin-1-positive map. |

`verify_design_notes.py` checks 623 selected machine-checkable pin, value, net-membership, assembly-status and approved-correction assertions. It does not cover firmware, PCB placement/routing, thermal design, or the open physical gates. The approved J701/LED corrections and unresolved connector sample gates are recorded separately in `CONNECTOR_REVIEW.md` and `POLARITY_REVIEW.md`.
