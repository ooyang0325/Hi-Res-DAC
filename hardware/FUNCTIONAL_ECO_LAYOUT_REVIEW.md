# Functional-ECO board: manual placement and route review

**Current board:** [DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb), 120 × 100 mm, four layers. It is a hand-placed, partially routed review candidate aligned with the [v1.1-ECO1 schematic](FUNCTIONAL_ECO_2026-09-28.md). The older `DAC_HPA.kicad_pcb`, macro study and separate J702 TVS option are historical comparisons; none includes the complete current footprint population.

The [machine-checked summary](FUNCTIONAL_ECO_LAYOUT_SUMMARY.json) records **544 footprints, 250 named nets, zero footprint bounding-box overlaps, zero KiCad error/warning DRC findings and 499 unconnected items**. All populated pad nets match the ECO schematic. The conservative JLC package-pair/body-edge screens report zero classified findings, but exact machine access and JLC order DFM remain open. All 478 component bodies resolve to STEP/VRML models; 66 copper-only items intentionally have none.

## Hand changes in this iteration

| Group | Exact change | Measured effect and limit |
| --- | --- | --- |
| U605 MCU readback | U621 and C667 were placed by U605. R688/R689 stayed at 470 kΩ and were moved beside U621; R952/R953 isolate its strong outputs and R954/R955 provide MCU-side fail-high pulls. | The two high-impedance R688/R689→U621 input pad distances are **1.687/1.856 mm**. C667 supply/return pad distances are **2.229/2.229 mm**. Actual traces, ground vias, rail corners and fault timing remain unverified. |
| U301 supply row | C305/C306/C307/C308/C309 were placed in a pin-ordered HF bypass row; C303/C304 sit behind it. | DAC pin-to-100 nF pad distances are **2.236/1.863/1.888/2.296/2.236 mm** for AVCC_L/AVCC_R/VCCA/DVCC/1V3. Supply-and-return loop inductance needs routed copper and L2 via inspection. |
| I/V hold-up | C442/C443 and D411/D412 moved south-east by explicit coordinates in `manual_functional_eco_layout.py`. | Opens the strip below K601 for audio routing while preserving zero courtyard/spacing findings. Diode-reservoir rail routing, access and voltage hold-up still require verification. |
| J702 ESD | D707/D708 are now captured on JACK_RP/JACK_LP. One RP relay→TVS→J702 trial and both local signal/GND-via branches are drawn. | D707→J702 is **3.861 mm**, D708→J702 **3.250 mm**, under the provisional 4.2 mm screen. Full LP output, jack sleeves, return-current geometry and IEC system ESD remain open. |

The board has 16 F.Cu track segments, six through vias and one filled L2 GND zone. These are local TVS branches and returns; there is no USB pair, MCLK/I²S, complete DAC/I/V, output, power or protection routing. A clean DRC on these few segments is only a clearance result.

## Output-stage route blocker found by hand probes

U401/U402 output links and relay contacts are vertically opposed: LP/RP links leave above their lower relays K601/K603, while LN/RN links leave below their upper relays K602/K604. Four independent straight-line length checks therefore hid a topological crossing. The VSON-10 output pad pitch is 0.50 mm with 0.30 mm pads, so a 0.50 mm trace directly at a pad leaves only 0.10 mm to its neighbour, below the 0.20 mm rule. A **0.25 mm local escape** leaves 0.225 mm by ideal geometry; it must widen promptly to ≥0.50 mm. The current board's custom rule permits that local width, with final length/DFM inspection still required.

Temporary hand-drawn route studies under `/private/tmp` are **not** part of the current KiCad board:

| Probe | Result | Disposition |
| --- | --- | --- |
| Original 0° amplifiers, all four LEG links | DRC-clean only after a roughly 31 mm L3 crossover for LP; the shorter LP crossing obstructed RN. | Does not establish a compact complete output layout. |
| 270° amplifiers with A/B unit swaps | Four LEG links and Rf/Cf pairs could be drawn, but RN needed a 23.26 mm B.Cu crossover and T-node/bypass nets were still undrawn. | Rejected as a current candidate; it would also require a schematic pin-net ECO. |
| 180° amplifiers, corrected link ordering | A DRC-clean four-LEG trial exists. An all-L1 RP detour forced JACK_LP through a 0.24 mm LP/RP pinch near K603, incompatible with the intended 2 mm channel separation and wider trunks. A separate trial used a **14.79 mm, 1.0 mm L3 RP bridge** with two Ø0.8/0.4 mm vias and kept the K601→J701/J702 JACK_LP branches about 18–19 mm. | Promising geometry only. At 50 °C, the L3 copper is about **8.15 mΩ** before vias/pad necks. Local feedback/T networks, L3 rail exclusion, L2 return continuity, crosstalk, total output impedance and the complete jack branches have not passed together. |

No 180° or 270° trial was promoted to the captured board. Moving only the amplifier package without its complete Rf/Cf, T network, supply bypass and audio exits would make a misleading placement. The next accepted output iteration must draw those networks **together**, preserve the continuous L2 reference, measure actual widths/lengths and recalculate the ≤0.5 Ω jack output-impedance and amplifier-stability budgets. The source 20 mm blanket audio rule is an engineering screen; [constraint disposition](CONSTRAINT_DISPOSITION_V2.md) explains the resistance and return-current criteria. Manual coordinate decisions are required; no placement search was used here.

## Remaining release holds

- [F01 all-rate SPI2 capture](MCU_SPI2_CAPTURE_ECO.md) is a feasible clock-rate *proposal*, with no firmware/RTL or proven DAC-side WS fault coverage. The R-28 high-rate frozen-word energy credit remains open.
- [F02/F04 schematic ECO](FUNCTIONAL_ECO_2026-09-28.md) passes netlist/ERC but needs rail/fault tests, JLC U621 G-3 land resolution, nonlinear TVS loading/THD and IEC system ESD.
- [3V3M charge](ATTACH_CHARGE_RECONCILIATION.json) is 6.5 µF nominal and 43.695 µC in the stated no-load-credit planning bound; measure C(V,T), U502 effective output capacitance and USB attach current/region overlap.
- G-3/G-4 sample overlays and polarity, connector soldering process, all critical concurrent routes, extracted clock/audio returns and JLC order DFM are open. **This is not Gerber/CPL/PCBA release data.**

For visual review, run [the command-line export](PCB_CLI_VISUAL_REVIEW.md) on this board. The GitLab `deliver_review_package` artifact includes a current zoomable SVG, GLB 3D assembly, schematic PDF and the audit JSON files for the same commit.
