# Placement, routability and PCBA peer-review guide

Review the [current 120 × 100 mm functional-ECO board](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb), its [whole-board preview](DAC_HPA_FUNCTIONAL_ECO_PLACEMENT_REVIEW.png) and [layout review](FUNCTIONAL_ECO_LAYOUT_REVIEW.md). The GitLab `deliver_review_package` artifact provides its zoomable SVG and GLB 3D view. Record board coordinates, layer and references for findings. The earlier primary and 100 × 80/100 × 100 mm boards are historical comparisons; they do not match the eight-part ECO schematic.

The [earlier macro-placement review](MACRO_PLACEMENT_REVIEW.md) explains the first subcircuit regrouping. The current ECO board keeps those manual groups, improves the DAC supply-capacitor row and hold-up-reservoir access, and adds the J702 local TVS/readback parts. Use the [constraint disposition](CONSTRAINT_DISPOSITION_V2.md) for this route study.

For scalable per-layer views, run the one-command [CLI visual inspection workflow](PCB_CLI_VISUAL_REVIEW.md). It exports the committed ECO board without modifying it.

**Current state:** 544 footprints, 250 named PCB nets, 28 F.Cu tracks, seven vias and one filled L2 GND zone. The partial copper includes J701/J702 TVS branches, one K603→J702 RP trial path, and the X201→R203→U301 MCLK trunk with R227/R665 branches. KiCad DRC reports zero error/warning violations; its JSON lists 499 missing links while the full ratsnest counts 1,144. All 478 component footprints resolve 3D bodies. [Layout summary](FUNCTIONAL_ECO_LAYOUT_SUMMARY.json) records exact counts and selected routed lengths. Placement and partial routing cannot certify simultaneous audio routes, EMI performance or JLCPCB assembly.

## Review order

| Priority | What to establish | Present evidence and open test |
| --- | --- | --- |
| 1. Connector and hand access | Physical jack/USB fit, board-edge mating, top-side soldering access and package-to-package space. | [G-3 1:1 overlays](G3_OVERLAY_INDEX.md) and [G-4 polarity](G4_POLARITY_CHECKLIST.md) are open. J101 and J702 need JLCPCB acceptance at finished edges and a confirmed soldering process for plated slots. J701's 1.5 mm top-side iron access is preserved in the manual primary. |
| 2. Critical simultaneous routes | Establish drawable paths with feedback and returns present. | See the route-risk table below. The board is mostly unrouted. Four-leg trial probes on the earlier placement exposed long output crossovers; these are route blockers to solve, not route approval. |
| 3. Audio and EMI topology | Preserve a single continuous L2 GND reference, quiet I/V/VREF, isolated high-impedance nodes, and a dedicated jack return. | The present L2 GND zone covers the board, but no complete output/clock/power return-current review is possible until routes, stitching and L4 pours exist. Use [Audio/EMI placement review](AUDIO_EMI_PLACEMENT_REVIEW.md), reading its old 100 × 100 mm examples as historical. |
| 4. Fabrication and assembly | Check actual JLCPCB policy, design rules, custom lands, pick-and-place access and BOM fit. | [JLC DFA/DFM rules](JLCPCB_DFA_DFM_RULES.md) and audits are screens only. The current conservative proxy classifies the new U621 and SOD-523 devices; 16 placed references remain outside its package table. Enlarged jack lands, panel rails and slot soldering need order-specific review. |

## Route-risk ledger for this placement

| Circuit | Current geometry | Reviewer decision or evidence needed |
| --- | --- | --- |
| X201 → R203 → U301 MCLK | The hand-drawn L1 route passes through TP711: X201→R203 **1.832 mm**, R203→U301 **6.479 mm**, combined **8.311 mm**. R227 has a local GND via and R665→U607 pin 2 is connected; DNF R703 has no copper. | Inspect clock edge quality, oscillator supply/return loop, probe loading, actual duty and U607 monitor behavior. The route meets the geometric 2/8/10 mm screens, but extracted parasitics and powered validation remain open. |
| Four protection timer branches | Worst C/R/Q Manhattan pad-distance lower bound is **7.91 mm** against an 8 mm route rule. | Draw all RC/bleed routes together and check *actual* copper length, reset level, leakage clearance and neighboring clock copper. A lower bound below 8 mm is not a pass. |
| I²S BCLK/LRCLK/SDATA | Current core pad-distance lower bounds 22.11 / 21.24 / 20.48 mm against 25 mm. | Route source → series resistor → DAC with branches, skew, spacing and uninterrupted L2 return. J703 has no PCB pads. |
| DAC → U403/U404 I/V | Four pad-distance lower bounds 3.83 / 6.65 / 6.23 / 3.81 mm against an owner-approved **provisional 7 mm** target. The five local HF bypasses are 1.86–2.30 mm from their DAC rail pins. | Draw all four inputs with GND guards and 2 mm no-digital-copper area, four-way VREF star, local rail returns and Rf/Cf loops. Check actual length, extracted summing-node capacitance and loop area <5 mm². |
| U401/U402 → K601–K604 output legs | The source/link/relay order creates LP/LN and RP/RN crossovers. Independent route probes were able to draw four output legs only with a long inner/back-layer crossover while feedback/T nodes remained incomplete. VSON 0.50 mm pitch also makes a 0.50 mm pad exit violate 0.20 mm clearance. | Manually reorganize complete amplifier/feedback/T/link and relay macros, then route all four legs concurrently. Use only short 0.25 mm VSON pad escapes before widening; a via crossover needs a measured return/impedance budget and an explicit rule change. No four-leg routability claim is made yet. |
| Relay → ESD → J701/J702 audio | D707/D708 now have 3.861/3.250 mm J702 signal branches and local GND vias; K603→J702 RP is a 9.785 mm trial route. The LP main trunk, the other relay/jack branches and all jack returns are undrawn. | Complete simultaneous routes to all jack contact pads, including J701 paired pads, and verify L/R separation, return current and solder access. The 20 mm blanket output limit is under electrical-budget review. |
| Jack GND and ESD return | J701 TVS signals measure 3.83–4.03 mm and J702 local branches 3.861/3.250 mm against the provisional ≤4.2 mm screen. Six short GND stubs/vias reach L2. | Complete robust sleeve connections, local stitching and return-current review; measure effective common impedance and loaded crosstalk. System IEC ESD testing remains open. |
| USB D+/D− at J101 | Fine-pitch escape has no credible rectangular-grid probe result. | Route the intended 90 Ω differential pair with nominal 0.235 mm width, permitted short 0.15 mm neck-downs and zero vias; check JLC stackup and field-solver impedance. Keep CC/VBUS/protection clear and inspect J101 shield return. |

The manual primary removed the historical 15 sensitive-to-clock *pad* gap findings, but routed copper must still satisfy the 5/10 mm high-impedance separation rules. The J701 footprint needs a narrow local exception to the general 2 mm L/R copper-separation rule; the custom KiCad rule restricts it to tracks within J701's courtyard against J701 pads, at ≥0.20 mm clearance. Inspect that fanout for crosstalk and manufacturability.

## DFA/DFM and physical checks

- Overlay actual J101/J701/J702, relay, oscillator, U621, ESD and polarized parts on the [30-pattern G-3 sheets](G3_OVERLAY_INDEX.md); verify terminal overlap, pin 1, body/peg/slot fit and the enlarged jack copper. J701/J702 worst calculated slot ring is ≥0.31 mm under JLC's published +0.13 mm slot-size tolerance; slot-to-copper registration and the 0.25 mm nearest J701 pad gap still require JLC DFM.
- Inspect J101 and J702 mating edges and panel rails with JLCPCB. The current proxy flags them as assembly exceptions to the general 2.5 mm body-to-finished-edge screen. J101's 3D shell was aligned to the existing maker PCB-edge datum; solder lands did not move.
- Confirm soldering of J101 S1–S4 and J702 1/2 plated slots. They currently have no F.Paste apertures. Check the proposed bottom-side J702 hand-solder fallback and access before changing fit class. [PCBA process review](PCBA_PROCESS_REVIEW.md) contains the exact JLC question.
- Check owner-fitted relay and film-capacitor iron access, 3D heights and thermal exposure. The C631–C634 body is a review envelope, and X201–X203 use a generic 2520 model; use physical parts and maker drawings at G-3.
- Review the current `FUNCTIONAL_ECO_DFA_AUDIT.json` in CI: zero classified spacing/edge findings and 16 unclassified placed references. Zero proxy findings do not guarantee machine access or final soldering. Confirm BOM/rotation in JLC's order preview after layout.

## Reproduce the read-only checks

Use KiCad 10's Python interpreter with `pcbnew` (`python3` in the GitLab KiCad image; on macOS the bundled interpreter path is shown in [README](README.md)). From the repository root:

```sh
python3 hardware/audit_placement.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb --height 100 > /tmp/placement.json
python3 hardware/audit_dfa_dfm.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb > /tmp/dfa_dfm.json
python3 hardware/audit_jlc_fab.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb > /tmp/jlc_fab.json
kicad-cli pcb drc --format json --severity-error --severity-warning -o /tmp/pcb_drc.json hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb
python3 hardware/check_functional_eco_layout.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb /tmp/placement.json /tmp/dfa_dfm.json /tmp/jlc_fab.json /tmp/pcb_drc.json
python3 hardware/audit_3d_models.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb --output /tmp/model_3d.json
```

Use [Review findings template](REVIEW_FINDINGS_TEMPLATE.md) to separate **observed board defects** from **route feasibility concerns** and **physical/JLC answers still needed**. A passing script is evidence for its stated screen only. Routing release remains on hold until G-3/G-4 and the listed geometric and audio/EMI checks are closed.
