# Response to the independent layout review v1.0 · 13 October 2026

Review: `doc/DAC_HPA_Independent_Layout_Review_v1.0.docx` with its evidence package (7 October 2026,
verdict "not sign-off ready": 8 technical fixes T1–T8, 3 document fixes D1–D3, 8 record items R1–R8).

Board: [DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb).
After the changes below:
- KiCad DRC **with schematic parity**: 0 violations, 0 unconnected, 0 parity issues ([INTEGRATED_AUDIO_DRC_PARITY.json](INTEGRATED_AUDIO_DRC_PARITY.json)); now a CI step ([check_integrated_parity.py](check_integrated_parity.py)).
- The 7 October sign-off suite ([signoff/](signoff/README.md)) re-run on this board: 0 FAIL / 10 WARN / 9 PASS, as before; G13 bypass-distance warnings 40 → 38 ([SIGNOFF_REPORT.md](signoff/out/SIGNOFF_REPORT.md)).
- Every CI job replayed locally: all pass. (validate_macro_study could not run here: the macOS KiCad Python has no numpy. That job's board is untouched.)

**Re-verification on the reviewer's own solvers.** The fixes were re-checked with the evidence-package
code itself, run on the revised board: the MNA detector model, the transmission-line transient
engine, the 2.5-D thermal model and the PDN droop model. The copper model was rebuilt from the new
board file with the reviewer's own parser (`geometry/sexp.py`, `geometry/model.py`). The wrappers and
results are in [sim/layout_review_v1/](sim/layout_review_v1/README.md).

**Corrections from the reviewer's re-verification (layout review v1.1, 14 Oct; follow-up in
[LAYOUT_REVIEW_V1_1_RESPONSE_2026-10-14.md](LAYOUT_REVIEW_V1_1_RESPONSE_2026-10-14.md)).** The numbers
below stand, with these corrections:
- T1: the hold-node capacitance is 1.57 pF, not 1.74 pF; the wrapper counted the shared 1.27 mm of track twice (conservative).
- R1: the leakage exposure rose (49.9 → 56.1 V·sq), it did not fall: TP747, a 1 mm exposed pad, now sits on N6_MCK_CMP. The minimum surface resistivity for ≤ 0.5 ms is still about 1.0 × 10⁹ Ω/sq.
- T2: the LINK_SCK stub to R247 is 2.32 mm, not ≤ 1.6 mm; LINK_FRAME is 16.46 mm with 3 vias. The 0 mA result is from these lengths.
- Moves this response did not list: C224 (it lost its GND via; fixed 14 Oct), C625, R666, R667, R218, TP708, TP734 and TP747, and N6_MCK_RC's old trunk renamed N6_MCK_CMP.

## 1. Fix-before-order items

| ID | Change | Reviewer's number (as routed → compact ref.) | Revised board, same solver |
| --- | --- | --- | --- |
| **T1** MCLK-alive detector | C625, R666 and R667 now stand in a row beside D609, all on one 3.4 mm F.Cu hold node with no vias. The 80 MHz loop C624 → D609 → C625 → GND via is 4.8 mm, no vias. The old 68 mm hold-node trunk keeps its copper as the DC side N6_MCK_CMP (R667 → U606), as the review recommends. TP747 moved behind R667 (**ECO F13**). N6_PMP is shortened from 5.9 mm to 3.5 mm. | Hold-node parasitic C: 15.3 pF → 1.65 pF. Dead detection, worst corner: 0.481 ms → 0.446 ms (window 0.5 ms). Ripple at D609.2: 461/1052 mV | Hold-node C **1.74 pF**. Dead detection **0.458 ms** worst (0.413 ms typ; low stop 0.216 ms). Ripple **189/195 mV**. Alive detection ≤ 285 ns (limit 2 ms); running level ≥ 2.48 V vs ≤ 0.384 V threshold |
| **T2** LINK_SCK/MOSI/FRAME | **ECO F11**: R247/R248/R249, 33 Ω (same part as R224), at the U208 outputs, ≤ 1.6 mm of copper from each pin. R248 sits above U208 and R247 below it. R249 takes C224's place, and its line returns on In3 to the existing FRAME via. C224 moves above U208. | LINK_SCK fast corner: 0.93 V over VCC, 14.3 mA clamp current; MOSI/FRAME 2.9/6.8 mA | LINK_SCK, full 27-corner factorial (36 runs): overshoot **≤ 1.5 mV**, clamp current **0 mA**, one threshold crossing, ringback margin ≥ 0.78 V. MOSI/FRAME: ≤ 1.7 mV, 0 mA |
| **T3** MCLK duty | **ECO F12**: R203 33 Ω → 0 Ω. BOM only; the footprint and nets stay, so 33 Ω can be re-fitted | 47.0–63.1 % across the XI threshold range; 48.9–54.8 % with 0 Ω | Same copper; the reviewer's 0 Ω result applies. **Bring-up**: qualify the X201 edges at ≤ 1.5 ns and measure the duty at XI |
| **T4** U503 PowerPAD | Six filled and capped Ø0.70/0.30 mm vias in the pad. Four crossings re-routed around the via field: 3V3M and ANA_EN (In2), AUD_EN (In3) and N5_ILIM (B.Cu) | F1 dead-short state, 50 °C ambient: 131.3 °C as built; 117.3 °C with 6 vias | **117.9 °C** (limit 125 °C). Normal state unchanged at 67.7 °C |
| **T5** Oscillator bypass | X201: C217 moves to the pin-4 corner, with ~2 mm of F.Cu to pin 4 and its own GND via. X202: C218 sits on the pin-4 via (1.1 mm F.Cu); R218 moves to C218's old site to make room. X203: the package shifts 1.0 mm east, and C219 takes the freed 1.6 mm slot, ~1 mm from pin 4. | Supply spike per 1 ns edge: X201 174.8 mV, X202 188.7 mV, X203 189.2 mV; compact 56–58 mV | X201 **60.0 mV**, X202 **68.7 mV**, X203 **64.8 mV** |
| **T6** MCU bypass | C206 moves to pin 64 (1.3 mm F.Cu) and C207 to the pin-32 via. Both came from the north bulk cluster. Pins 1 and 19 have no legal 0402 site within 4.5 mm and keep the inner 3V3M feed | Droop for a 65 mA, 1 ns step: pin 32 101.9 mV, pin 64 103.0 mV (budget 99 mV) | Pin 32 **41.1 mV**, pin 64 **30.1 mV**, pin 19 74.3 mV, pin 48 52.6 mV. **All within 99 mV** |
| **T7** DNF attributes | The board generator copies the schematic DNP flag onto the footprints. That covers the 8 board DNF parts; J703 is not on the board. DNP parts are also excluded from the position file, so no board export can place them. They stay on the BOM as DNP lines, like their symbols, which is what keeps schematic parity clean. The generator also carries every symbol field and the schematic's NC-pin net names, as Update-PCB-from-Schematic would | — | Parity 0. Each DNF footprint: `dnp`, excluded from position files |
| **T8** J201/J202 pin 1 | No layout change. The 3D models were re-checked on 7 October (pin-1 dot on the edge row) | Pin-1 stagger side not readable from the XKB drawing text | **Owner action**: 1:1 print ([DAC_HPA_1to1_F_REVIEW_ONLY.pdf](DAC_HPA_1to1_F_REVIEW_ONLY.pdf)) against the drawing or a sample header |

## 2. Document items

| ID | Action |
| --- | --- |
| D1 Parts List | The complete v0.9 → v1.0 change list is in [DESIGN_DOCUMENT_UPDATES_2026-10-13.md](DESIGN_DOCUMENT_UPDATES_2026-10-13.md) §1: added rows, changed rows (incl. OPA2210 DGK) and netlist changes (incl. D705/D706). It was computed from the generator overlay, so it is complete by construction. The owner issues v1.0; the repository does not edit the workbook |
| D2 Spec/Notes | Revision text drafted in the same file §2. It covers the accepted deviations, the R11 waiver for U611, the D705/D706 override, the detector and LINK notes, and the cleaning requirement. The D705/D706 override is now also in the ECO table of [DESIGN_TO_LAYOUT_DIFFERENCES.md](DESIGN_TO_LAYOUT_DIFFERENCES.md) |
| D3 DRC file | DRC with schematic parity on the current board: 0/0/0, now enforced in CI. The suite's `signoff/out/kicad_drc.json` was regenerated from the current board |

## 3. Record items

| ID | Disposition |
| --- | --- |
| R1 Leakage | Holds only on a cleaned board. Required assembly condition: **ρs ≥ 1e10 Ω/sq (2e10 with margin)**, plus a cleaning remark on the order; confirm with the 50 °C high-humidity test. Drafted for the evidence register (updates §2.3). The hold node is now 3.4 mm, so it has less exposed copper |
| R2 LINK_MISO / LRCLK_FB | CPLD RTL: ≤ 8 mA drive or slow slew on pins 28 and 13. Open with the CPLD constraint work |
| R3 EP vias, R11, U301 | Added where legal: U504 0 → 2, U401 2 → 5, U402 3 → 7. Thermal result: U504 98.7 → 89.9 °C, U401 85.5 → 83.4 °C, U402 81.1 → 79.5 °C. U501 has no legal site (B.Cu under the pad); it stays at 92.2 °C. U611 needs the R11 waiver. IR scan at bring-up |
| R4 Pour coverage, N6_ORTEST | Recorded. N6_ORTEST re-route deferred to the next revision, as recommended |
| R5 Load capacitance | Recorded. The HSE crystal's rated CL is to be checked against 21.6 pF |
| R6 USB skew | 1.9/16.7 ps (0.8 % of the UI). Accept, or add a D− serpentine (owner decision; differences doc item 3) |
| R7 Back-feed in S5 | Recorded. Measure VPOS on the bench in S5 |
| R8 | TP747 fixed (F13). J701 sleeve: 2 → **5** GND vias within 2 mm (Spec R10 ≥ 4); the new ones sit just outside the J701 courtyard, where B.Cu copper is forbidden. C507 neck: the 0.8 mm rule cannot apply at a 0.28 mm WSON pin, and the input-cap site at pin 3 is enclosed by the N5_FBP/N5_CP routing; recorded with the reviewer's ≤ 0.18 mV coupling result. 5V_SYS 22 mV drop and OPA1622 cable ringing: recorded |

## 4. Geometry notes from the evidence package

- Bottom-right board corner: was a non-tangent R0.79 arc bulging 0.042 mm outside the edges; the generator now makes it R1, like the other three corners.
- `JLCPCB_DFA_DFM_RULES.md` via counts corrected: 1575 vias, 55 filled, 477 near-pad sites.
- MH1–MH4 on GND without netlist rows; courtyards within 2.5 mm of the edge: recorded (unchanged).
- New parts' copies of footprints now get fresh UUIDs: `FOOTPRINT(copy)` had kept the source's item UUIDs, so DRC named R247–R249 items after R224.

## 5. Still open before the order (process, not layout)

G-3 physical overlays, G-4, G-5 netlist freeze, G-6 JLC answers; CPLD pin constraints and fitter run
(F06–F09, R2, LINK_SCK global clock); cost re-quote (120 × 100 mm, 6 layers, 55 filled vias); owner
approval of ECOs F11–F13 and the R11 waiver; Parts List v1.0 and Spec/Notes revision issue.
