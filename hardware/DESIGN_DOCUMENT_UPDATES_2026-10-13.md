# Design document updates · 13 October 2026

The independent layout review v1.0 (findings D1 and D2) found that Parts List v0.9 and the Spec/Notes
no longer describe the board. This file is the exact change list for the owner to issue as
**Parts List v1.0**, **Design Spec v1.2** and the next **Schematic Design Notes** revision. The
repository never edits those controlled documents: the schematic generator applies every change
below as a checked overlay ([generate_schematic.py](generate_schematic.py)), and
[verify_schematic.py](verify_schematic.py) fails if the board, schematic and this overlay disagree.
The JLC BOM ([JLCPCB_BOM_REVIEW_ONLY.csv](JLCPCB_BOM_REVIEW_ONLY.csv)) already reflects all of it.

## 1. Parts List v0.9 → v1.0 (finding D1)

### 1.1 Added rows

| Ref | Value | MPN | Package | LCSC | ECO |
| --- | --- | --- | --- | --- | --- |
| U621 | SN74AUP2G17DCKR | TI SN74AUP2G17DCKR | SC70-6 (DCK) | C507231 | F02 MCU readback buffer |
| R952, R953 | 10 kΩ | UNI-ROYAL 0402WGF1002TCE | 0402 | C25744 | F02 MCU-side series resistors |
| R954, R955 | 100 kΩ | UNI-ROYAL 0402WGF1003TCE | 0402 | C25741 | F02 fault-high pull-ups |
| C667 | 100 nF | Samsung CL05B104KO5NNNC | 0402 | C1525 | F02 U621 bypass |
| D707, D708 | 5 V | GOODWORK LESD5D5.0CT1G | SOD-523 | C41399463 | F04 J702 LP/RP TVS |
| R448 | 0 Ω | UNI-ROYAL 0402WGF0000TCE | 0402 | C17168 | F10 ground-sense join at the J702 sleeve |
| R247, R248, R249 | 33 Ω | UNI-ROYAL 0402WGF330JTCE | 0402 | C25105 | **F11** U208 LINK output source resistors |

### 1.2 Changed rows

| Ref | v0.9 | v1.0 | ECO |
| --- | --- | --- | --- |
| U403, U404 | OPA2210 SOIC-8 | **TI OPA2210IDGKR, VSSOP-8 (DGK)**, C2876414 | Owner override (DGK) |
| J201 | 8 SMD pads, no component | **XKB X6511WVS-08H-C60D48R1**, C2883805, fitted | F05 |
| J202 | 5 SMD pads, no component | **XKB X6511WVS-05H-C60D48R1**, C2883802, fitted | F05 |
| R203 | 33 Ω, C25105 | **0 Ω, UNI-ROYAL 0402WGF0000TCE, C17168** (footprint kept for re-fit) | **F12** |
| J101 | GCT USB4105 land | Land pattern `J101_USB4105-GF-A_12lands_4stakes_NPTH030` (VBUS/GND lands 0.98 mm) | Sign-off review, 7 Oct |
| J703 | I²S header (not fitted) | Not on the PCB (`on_board no`) | Owner |

### 1.3 Netlist sheet (pin → net)

| Pins | v0.9 | v1.0 | ECO |
| --- | --- | --- | --- |
| D705.1 / D705.2 | GND / N7_LEDG_A | **N7_LEDG_A / GND** (pad 1 = anode, per the maker and JLC symbols) | Owner override, 26 Sep |
| D706.1 / D706.2 | GND / N7_LEDR_A | **N7_LEDR_A / GND** | Owner override, 26 Sep |
| U403.1/2/6/7, U404.1/2/6/7 | A/B channel order | Channels swapped (DAC + legs on B, − legs on A) | I/V channel ECO |
| R688.2 / R689.2 | N6_V3AG_A/B_MCU | N6_V3AG_A/B_BUF_IN | F02 |
| U202 pins 2, 3, 8, 10, 11, 12, 14, 21, 22, 23, 26, 27, 28, 31 | v0.9 CPLD map | LINK bus to 26/27/28, CPLD_IRQ to 3, OSC48_EN to 31, OSC44_EN to 8, N2_CPY_CK/SD to 21/22, MCLK_EN to 23 | F06–F09 (**RTL pin constraints must follow**) |
| R228.1 / R229.1 / R230.1 | N2_BCLK/LRCLK/SDATA_SRC | N2_CPY_CK / LRCLK_FB / N2_CPY_SD | F07 |
| R404.2, R408.2, R412.2, R416.2 | GND | N4_GSENSE | F10 |
| U208.7 / U208.5 / U208.2 | LINK_SCK / LINK_MOSI / LINK_FRAME | N2_LINK_SCK_OUT / N2_LINK_MOSI_OUT / N2_LINK_FRAME_OUT | **F11** |
| TP747.1 | N6_MCK_RC | **N6_MCK_CMP** | **F13** |

Inventory after the ECOs: 538 netlisted parts (469 JLC-placed, 7 owner-fitted, 9 DNF, 52 test pads,
1 pad set), 1473 pins, 256 named nets.

## 2. Spec v1.1 / Notes → next revision (finding D2)

Each item is an accepted deviation or a decision the documents must record. Status and reasons are in
[DESIGN_TO_LAYOUT_DIFFERENCES.md](DESIGN_TO_LAYOUT_DIFFERENCES.md).

### 2.1 Board and fabrication
- Board 120 × 100 mm, 6 layers, JLC06161H-3313 (1 oz outer, 0.5 oz inner), ENIG; L1 signal, L2 GND, L3 PWR/routing, L4 signal, L5 GND, L6 signal.
- Via set: Ø0.60/0.20 mm default; Ø0.50/0.20 mm (0.15 mm ring) on the listed slow digital nets (owner, ce339dc); Ø0.70/0.30 and Ø0.80/0.40 mm power/thermal. All via-in-pad sites filled and capped (55 vias).
- Exposed-pad vias as built: U503 6 (Notes: ≥ 5), U504 2 (Notes: 4 + 200 mm² pour; the 1.0 × 1.6 mm pad fits two), U401 5, U402 7 (Notes: 5), U501 about 2 (one filled via in the pad, one at its edge; Notes: 6; no further legal site, B.Cu runs under the pad). Record the U504/U501 shortfall with the independent thermal result (≤ 92.2 °C at 50 °C ambient).
- Silkscreen: R17 says designators only on the assembly drawing; the board carries 257 legends. Revise R17 or remove them (owner decision).

### 2.2 Routing rules
- R08 USB: widths re-solved for JLC06161H-3313 (0.17/0.18/0.20 mm); skew 2.15 mm vs ≤ 0.15 mm (decide: serpentine or accept 16.7 ps).
- R09 DAC → OPA2210 −IN ≤ 7 mm (owner-provisional, 6.84 mm worst).
- R09 jack ESD distance ≤ 4.2 mm (routed 3.26–4.03 mm).
- R10 headphone return: continuous L2/L5 planes plus the F10 sense return instead of a dedicated L1 strip; ≥ 4 sleeve vias met at J701 (5) and J702 (6).
- R11 heat separation: **waiver for U611** (5.5 mm from U501, +10 K).
- R12 high-impedance nodes: accepted as routed for the protection block, with the cleaning requirement below. The MCLK-alive hold node now meets R12 (3.4 mm, no vias).
- Notes, bypass placement: replace "within 1 mm" with the supply-and-return loop rule; record pins 1 and 19 of U201.
- Notes, MCLK-alive detector: dead detection ≤ 0.46 ms at the dead-worst corner as routed (was "≤ 0.452 ms" / BOM "≤ 0.42 ms"); TP747 is behind R667 (≤ 100 kΩ rule no longer applies to it).
- Notes, LINK bus: U208 → CPLD is 28 mm, not ≤ 5 mm; the F11 source resistors replace the distance rule.

### 2.3 Assembly and test
- Leakage: add **ρs ≥ 1e10 Ω/sq (≥ 2e10 with margin) after cleaning** as a required assembly condition in the evidence register, and the cleaning remark on the order; confirm with the planned 50 °C high-humidity test on U605, the LPW taps and the OR taps (layout review R1).
- Bring-up: qualify the X201 edge time ≤ 1.5 ns and measure MCLK duty at XI (F12); measure VPOS in supply state S5 (R7); IR scan of the U301 area (R3).
- CPLD RTL: pin constraints for F06–F09, ≤ 8 mA drive (or slow slew) on pins 28 (LINK_MISO) and 13 (LRCLK_FB) (R2), and confirm in the fitter report that LINK_SCK (pin 9) reaches the global clock network.
