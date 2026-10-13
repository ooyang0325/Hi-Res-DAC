# Design documents vs. layout · 13 October 2026

This file compares the **controlled design documents** with the current layout:
- Design Spec v1.1, §7 rules R01–R17;
- Schematic Design Notes v1.0 (layout package);
- Parts List v0.9;
- Calculation Package v1.1.

The layout is [DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb)
after the independent layout review v1.0 fixes ([LAYOUT_REVIEW_RESPONSE_2026-10-13.md](LAYOUT_REVIEW_RESPONSE_2026-10-13.md)).
The documents were not revised during layout. Every row below is either an accepted deviation with
its reason, or an open item. The text that absorbs the accepted rows into the Spec, Notes and
Parts List is drafted in [DESIGN_DOCUMENT_UPDATES_2026-10-13.md](DESIGN_DOCUMENT_UPDATES_2026-10-13.md);
the owner issues the revisions.

**Approval key**
- **Owner:** decided by the owner.
- **Eng.:** engineering disposition in [CONSTRAINT_DISPOSITION_V2.md](CONSTRAINT_DISPOSITION_V2.md) or the
  review documents, open to owner review.
- **Open:** the layout does not yet meet the document, and no decision has been made.

## 1. Board and fabrication (Spec R06, R07, R13, R17)

| Item | Documents | Layout | Why | Approval |
| --- | --- | --- | --- | --- |
| Board size | 100 × 80 mm, two 5 mm V-cut rails, 100 × 90 mm panel (R06) | 120 × 100 mm; no rails drawn | For placement and routing room: the owner selected 100 × 100 mm, then allowed the 120 × 100 mm manual placement ([PRELAYOUT_GATES.md](PRELAYOUT_GATES.md)). Panelization is left to the order | Owner |
| Layer count and build | 4 layers, JLC04161H-7628 (R06) | **6 layers, JLC06161H-3313**, declared in the board: 1 oz / 0.5 oz, 3313 prepreg 0.0994 mm εr 4.1, cores 0.55 mm εr 4.6, 2116 prepreg 0.1088 mm εr 4.16, ENIG | On 4 layers the routing plateaued with 63–64 unroutable links. The owner chose 6 layers on 1 October ([LAYOUT_PROGRESS](LAYOUT_PROGRESS_2026-09-30.md)). The stackup was written into the board after the independent review found none declared | Owner |
| Layer use | L1 all parts and fast signals; L2 solid GND; L3 power pours and < 1 MHz signals; L4 GND pour plus slow analog and control, no clocks (R07) | L1 parts and fast signals (MCLK/BCLK/LRCLK/SDATA, USB on L1 with no vias). L2 solid GND, unchanged. L3 power traces and slow signals. L4 (SIG) slow signals and a GND pour. L5 solid GND. L6 slow signals, power trunks and a GND pour | The two extra layers add a second GND plane (L5) for the L4/L6 routes. The slow serial clocks (LINK SCK, JTAG, capture copies) use L3/L4 with vias. The audio-rate and master clocks stay on L1 | Owner (6-layer); Eng. |
| VPOS/VNEG distribution | L3 pours ≥ 3 mm, with a ≥ 0.4 mm branch pair to Z4 (R11) | Routed traces of 0.3–1.2 mm on L3; ≥ 0.5 mm on the main amplifier feeds | L3 also carries routing, so full-width pours would block it. The traces are checked against the solved current at the LM27762's 250 mA limit; the narrowest main-path margin is ≥ 2.1× ([signoff G10](signoff/out/SIGNOFF_REPORT.md)) | Eng. |
| Exposed-pad vias | U301: 5 × 0.30 mm thermal vias, unfilled and tented; epoxy fill dropped for cost (R06, R13) | U301 has 5 and U202 has 2 vias of 0.7/0.3 mm, **filled and capped**. 39 vias board-wide are filled and capped | JLC's via-covering guidance supports only filled and capped vias inside or within 0.35 mm of a pad; tented or plugged vias in a QFN pad risk voids and solder wicking ([DAC_CORE_ROUTE_STUDY.md](DAC_CORE_ROUTE_STUDY.md), [PCBA_PROCESS_REVIEW.md](PCBA_PROCESS_REVIEW.md)). **This reverses the R06 cost saving**; the price must be confirmed at order | Eng. (owner to accept cost) |
| Silkscreen designators | "Designators appear only in the assembly drawing" (R17) | 257 `${REFERENCE}` legends (1.0 × 0.15 mm) where they fit (D609, X201, TP747 and R202 lost theirs to the 13 October parts); F.Fab still carries every designator | Added on 7 October for the independent review's G05 finding, so the board can be inspected and reworked. **This contradicts R17 as written.** A single manifest field (`silk.refs`) removes them | **Owner decision needed** |
| Silkscreen marks | Pin-1 and polarity marks, OWNER marks at K601–K604, J701, D102 and R509, and the note "R509 owner-fitted — eFuse off without it" (R17) | Footprint pin-1 and polarity marks are present. **No OWNER marks and no R509 note** | Not yet drawn | **Open** |
| Silk line width | (not specified) | All footprint strokes ≥ 0.15 mm (909 were 0.10–0.13 mm) | JLC's minimum legible line | Eng. |

## 2. Schematic and functional changes (ECOs)

All are applied as checked overlays in [generate_schematic.py](generate_schematic.py). Parts List
v0.9 and the calculation package are not edited.

| ECO | Change | Why | Approval |
| --- | --- | --- | --- |
| I/V channel assignment | U403/U404: the DAC + legs go to op-amp B and the − legs to A (8 pin nets) | The two halves of the OPA2210 are identical. The rotated I/V macro gives straight ≤ 7 mm DAC-to-input routes ([FUNCTIONAL_ECO_2026-09-28.md](FUNCTIONAL_ECO_2026-09-28.md)) | Owner |
| F02 | U621 SN74AUP2G17 Schmitt buffer, R952/R953 10 k, R954/R955 100 k pull-ups, C667 100 nF on the 3V3A-good MCU readbacks | The 470 kΩ readback path had insufficient worst-case logic margin into the MCU | Owner |
| F04 | D707/D708 TVS on the J702 LP/RP contacts | The 3.5 mm jack had no local ESD clamp | Owner |
| F05 | J201/J202 fitted with XKB SMD pin headers (C2883805/C2883802); R15 specified bare debug pads | So the WCH-LinkE and the AGM programmer plug in directly. SMD parts drill nothing, so L2 stays whole | Owner |
| F06, F08, F09 | AGRV2K pin reassignments: LINK bus, CPLD_IRQ, OSC48/44_EN, the capture copies and MCLK_EN | Layout-driven: escape routes from the 0.4 mm QFN-32. **RTL pin constraints must follow** | Owner (pin swaps) |
| F07 | The CPLD drives dedicated BCLK/SDATA copies (pins 21/22) into R228/R230; WS is captured from LRCLK_FB | The DAC-bound I²S lines could not carry capture stubs as 3W F.Cu routes | Owner |
| F10 | R404/R408/R412/R416 reference returns via N4_GSENSE to the J702 sleeve; R448 0 Ω is the single GND join | The sign-off simulation found the 3.5 mm whine margin at 1 dB; after F10 it is ≥ 27 dB ([SIGNOFF_SIMULATION](SIGNOFF_SIMULATION_2026-10-07.md)) | Owner |
| F11 | R247/R248/R249, 33 Ω (C25105, as R224), in series at the U208 LINK_SCK/MOSI/FRAME outputs; U208 pins 7/5/2 move to N2_LINK_*_OUT | Layout review T2: the unterminated LVC edges put 14.3 mA into the AGRV2K clamp at the fast corner (10 mA assumed limit). With the resistors: 0 mA, ≤ 2 mV overshoot | **Owner approval requested** (layout review fix) |
| F12 | R203 33 Ω → 0 Ω (BOM only; footprint and nets kept) | Layout review T3: MCLK duty at the ES9018K2M die spans 47–63 % over the unknown XI threshold with 33 Ω, 48.9–54.8 % with 0 Ω. Qualify the X201 edges (≤ 1.5 ns) at bring-up | **Owner approval requested** |
| F13 | TP747 moves from N6_MCK_RC (1 MΩ hold node) to N6_MCK_CMP (behind R667) | Layout review T1: the hold node is now a 3.4 mm group at D609 with no vias; the probe and its exposed pad stay off it | **Owner approval requested** |
| D705/D706 pin map | Parts List v0.9 pad 1 = K = GND; schematic and board: pad 1 = anode (N7_LED*_A), pad 2 = GND | Owner override in [generate_schematic.py](generate_schematic.py) (26 Sep) following the maker and JLC symbols, so the LEDs are not reversed. Was missing from this table (layout review D1/D2) | Owner |
| J703 | Spec R15: I²S header not fitted. Layout: footprint removed | Owner-approved pad removal ([PLACEMENT_REPORT.md](PLACEMENT_REPORT.md)); the header was not fitted under R15 anyway | Owner |
| F01 | SPI2 all-rate capture | **Not implemented**; proposal only ([MCU_SPI2_CAPTURE_ECO.md](MCU_SPI2_CAPTURE_ECO.md)) | **Open** |

No MCU (CH32V307) pin swaps were taken.

## 3. Routing rules (Spec R08–R12, Notes v1.0)

| Rule | Documents | Layout | Why | Approval |
| --- | --- | --- | --- | --- |
| USB width | W 0.235 / S 0.15 mm = 90 Ω on the 4-layer 7628 stack (R08) | Coupled 0.17 mm / 0.215 mm gap and 0.18 / 0.32 mm; 0.20 mm split runs around U101; 0.16 mm J101 escapes | The R08 numbers belong to the 4-layer stack. On JLC06161H-3313 the routed pair was field-solved and widened to 88.7–90.0 Ω, 81–99 Ω at the build corners ([signoff_impedance.txt](sim/signoff/signoff_impedance.txt)) | Eng. (follows the owner's 6-layer decision) |
| USB length / vias | ≤ 30 mm, no vias, U101 inline | 25.9 mm, no vias, inline | — | Meets |
| USB skew | ≤ 0.15 mm (R08) | **2.15 mm** (12 ps) | D+/D− cross at the USB-C double-row pins, and the pair splits around the USBLC6 flow-through pins. 12 ps is well inside USB 2.0's ~100 ps, but R08 is tighter | **Open** (a 2 mm serpentine on D− would meet R08) |
| MCLK | ≤ 10 mm with a via fence; R665 at XI, R665 → U607 ≤ 3 mm (R09) | 8.38 mm, L1, no vias; R665 → U607 1.6 mm | — | Meets (the via fence is not verified by a check) |
| I²S | ≤ 25 mm, matched ±5 mm (R09) | 22.2–22.9 mm, 0.67 mm spread | — | Meets |
| DAC → OPA2210 −IN | ≤ 5 mm, no vias (R09) | ≤ 7 mm (DACR 6.84 mm), no vias | The rotated I/V macro could not get all four under 5 mm. The summing-node capacitance still has to be extracted against the model's 6 pF envelope | Owner (provisional ≤ 7 mm) |
| Rf/Cf loop | < 5 mm² (R09) | 4.875 mm² (plan view) | — | Meets |
| LEG → switch → JACK | ≤ 20 mm per net (R09) | Treated as a screen, not a limit. LEG_xx also carries the sense-divider taps (up to 265 mm of copper, with no load current) | Judged by resistance instead: the load path is 2–31 mΩ per net. The amplifier pads need 0.25 mm escapes of ≤ 1 mm (VSON 0.5 mm pitch) before the ≥ 0.5 mm trunks | Eng. |
| Jack ESD distance | ≤ 3 mm from the contacts (R09) | 3.26–4.03 mm (limit 4.2 mm, audited in CI) | Provisional routed limit set in the constraint disposition; the IEC system ESD test decides | Eng. (provisional ≤ 4.2 mm) |
| Headphone return | Dedicated ≥ 3 mm L1 strip to the output-stage star; ≥ 4 vias per sleeve pin (R10) | Continuous L2 and L5 planes. ECO F10 sense returns to the J702 sleeve. J702 sleeve: 6 GND vias. J701 pad 1: 5 GND vias within 2 mm (three added just outside the J701 courtyard, where B.Cu copper is forbidden) | A strip carved from L1 does not by itself isolate; the planes give lower shared impedance. The MATLAB ground solve, with F10, gives ≥ 27 dB whine margin | Eng. (strip); via count meets |
| Power widths | VBUS/5V_SYS ≥ 1.0 mm; 5V_ANA → FB501 → LM27762 ≥ 0.8 mm (R11) | Met, except pad launches: J101 VBUS 0.5 mm × ≤ 2 mm; U102 pins 1/6 0.36 mm and U504 pin 6 0.30 mm × ≤ 1.2 mm; three 0.20 mm 5V_ANA_F escapes at U501 | The pads are narrower than the trunk. Each neck is bounded and checked by [audit_power_pad_escapes.py](audit_power_pad_escapes.py) and the U501 rule | Eng. |
| Vias per 0.5 A | ≥ 2 per transition (R11) | U102 output: 2 × 0.8/0.4. U503 → 5V_ANA: 2 × 0.7/0.3. FB501 end: 1 × 0.8/0.4 at 0.49 A (rated 0.87 A) | The 0.49 A transitions are just under the rule's 0.5 A | Meets |
| Heat separation | Heat sources ≥ 15 mm from U301, U202, X201, the comparators and J701 (R11) | U611 is 5.5 mm from U501 (+10 K from the four sources); U603 14.6 mm (+6.9 K); all others meet | The independent thermal model puts the effect at a few kelvin; the board under U301 reaches 64.5 °C against its 70 °C rating, mostly global heating. An IR scan at bring-up confirms | **Owner waiver needed** (U611) |
| High-impedance nodes | Node copper ≤ 5 mm, no vias, ≥ 5 mm from clocks (R12); ≥ 0.5 mm to other copper (Notes §9.3.1) | **Not met** on most protection nodes: e.g. N6_CML 103 mm / 6 vias, N6_VT 83 mm / 9 vias. The MCLK-alive hold node N6_MCK_RC is now 3.4 mm with no vias (was 68 mm / 8 vias). Timer branches are held to ≤ 8 mm per named-pad branch. 29 pairs at 0.2–0.5 mm (under mask) | The protection block is spread across zones Z4–Z7 of the larger board, so its nodes must travel. The ≥ 5 mm clock and 10 mm reference keep-outs are kept as DRC rules. R05 cleaning (no-clean flux control) becomes essential | **Owner review** (listed in LAYOUT_PROGRESS); leakage and humidity test still required |
| Bypass placement | Notes: every capacitor within 1 mm | Replaced by a short supply-and-return loop rule. X201–X203 caps at their VCC pins (1–2 mm F.Cu); MCU caps at pins 64 and 32 (1.3 / ~5 mm); pins 1 and 19 keep the inner 3V3M feed (no legal 0402 site) | The 1 mm rule is not achievable on dense QFN/LQFP fan-outs. On the independent PDN model every pin is now inside its 99 mV droop budget (worst 74 mV, pin 19) | Eng. |
| Slow digital clearance | 0.2 mm default | 0.15 mm only between the listed slow MCU/CPLD control nets (enables, JTAG/SWD, I²C, LINK, ADC sense) | Needed to fan out the 0.5 mm LQFP-64 and 0.4 mm QFN-32. Inside JLC's 0.09 mm capability | Eng. (owner-reviewable) |
| Via floor | Ø0.60/0.20 mm (0.20 mm ring) | Ø0.50 mm / 0.15 mm ring allowed | Needed for escapes in the dense digital block. The ring is JLC's absolute minimum | Owner (ce339dc) |
| DC_SENSE_LP | Slow analog on L4 (R07) | ~100 mm on L3 along the west edge | Routed in the Freerouting gap-fill. It is a DC sense line, RC-filtered at the MCU, running between GND layers | Eng. (re-route when the protection block is re-placed) |
| GND stitching | L4 GND pour stitched to L2 on a ≤ 5 mm grid (R07) | 751 GND vias, including 34 added beside clock/audio layer changes | — | Meets |

## 4. Footprints and lands (Spec R13, G-3)

| Part | Documents | Layout | Why | Approval |
| --- | --- | --- | --- | --- |
| J101 | GCT USB4105 drawing: 0.6 × 1.15 mm VBUS/GND lands | `J101_…_NPTH030`: those four lands are 0.98 mm long, shortened on the locating-hole side | The locating holes were 0.13/0.17 mm from the lands (JLC NPTH minimum 0.20 mm; board rule 0.28 mm); now 0.30/0.33 mm | Eng.; **G-3 overlay must confirm the tails** |
| J701/J702 | Maker slot/pad sizes | Copper enlarged around the unchanged slots (≥ 0.31 mm ring at +0.13 mm slot tolerance) | JLC plated-slot tolerance | Owner |
| U621 | TI DCK land (2.2 mm span) | JLC C507231 land (1.68 mm span) | Exact JLC CAD for JLC assembly | Eng.; G-3 open |
| J201/J202 3D | — | KiCad stock SMD pin-header bodies | The F05 headers had no model, so they rendered as bare pads | Eng. |

## 5. Open items that bring the layout back to the documents

1. Draw the R17 silkscreen OWNER marks (K601–K604, J701, D102, R509) and the R509 note.
2. Decide R17 designators: keep the 257 legends (and revise R17), or remove them.
3. Meet the R08 skew (≤ 0.15 mm) with a short D− serpentine, or accept it (the independent TDR gives 1.9 ps A-row / 16.7 ps B-row, 0.8 % of the unit interval) and revise R08.
4. Approve ECOs F11–F13 (layout review T1–T3).
5. Waive Spec R11 for U611 (5.5 mm from U501).
6. Protection high-impedance nodes: owner acceptance plus the cleaning requirement (ρs ≥ 1e10 Ω/sq) and the 50 °C high-humidity test, or a re-placement that shortens them.
7. Issue Spec v1.2 / Notes / Parts List v1.0 from [DESIGN_DOCUMENT_UPDATES_2026-10-13.md](DESIGN_DOCUMENT_UPDATES_2026-10-13.md).
