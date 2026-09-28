# Placement, routability and PCBA peer-review guide

Start with the newest [120 × 100 mm integrated-audio study](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb) and its [electrical-margin review](INTEGRATED_AUDIO_ROUTE_STUDY.md). Compare it with the [functional-ECO capture baseline](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb), its [whole-board preview](DAC_HPA_FUNCTIONAL_ECO_PLACEMENT_REVIEW.png) and [layout review](FUNCTIONAL_ECO_LAYOUT_REVIEW.md). The GitLab `deliver_review_package` artifact provides zoomable SVG and GLB 3D views for both. Record board coordinates, layer and references for findings. The earlier 536-footprint primary and 100 × 80/100 × 100 mm boards do not match the eight-part ECO schematic.

The [earlier macro-placement review](MACRO_PLACEMENT_REVIEW.md) explains the first subcircuit regrouping. The functional-ECO baseline improves the DAC supply-capacitor row and hold-up-reservoir access, and adds the J702 local TVS/readback parts. The [intermediate 270° output study](OUTPUT_MACRO_ROUTE_STUDY.md) proves four amplifier-to-relay inputs and feedback loops. The integrated study continues those paths to the physical jack contacts. Use the [constraint disposition](CONSTRAINT_DISPOSITION_V2.md) for each board.

For scalable per-layer views, run the one-command [CLI visual inspection workflow](PCB_CLI_VISUAL_REVIEW.md). It exports the committed ECO board without modifying it.

**Capture baseline:** 544 footprints, 250 named PCB nets, 28 F.Cu tracks, seven vias and one filled L2 GND zone. Its partial copper contains J701/J702 TVS branches and the X201→R203→U301 MCLK trunk. The [integrated study summary](INTEGRATED_AUDIO_SUMMARY.json) reports zero custom-rule DRC violations, zero classified JLC spacing findings, four connected amplifier-to-jack signal paths and 1,089 full ratsnest gaps. All 478 populated component footprints resolve 3D bodies. A placement or partial-route result cannot certify EMI performance or JLCPCB assembly.

## Review order

| Priority | What to establish | Present evidence and open test |
| --- | --- | --- |
| 1. Connector and hand access | Physical jack/USB fit, board-edge mating, top-side soldering access and package-to-package space. | [G-3 1:1 overlays](G3_OVERLAY_INDEX.md) and [G-4 polarity](G4_POLARITY_CHECKLIST.md) are open. J101 and J702 need JLCPCB acceptance at finished edges and a confirmed soldering process for plated slots. J701's 1.5 mm top-side iron access is preserved in the manual primary. |
| 2. Critical simultaneous routes | Establish drawable paths with feedback and returns present. | See the route-risk table below. The board is mostly unrouted. Four-leg trial probes on the earlier placement exposed long output crossovers; these are route blockers to solve, not route approval. |
| 3. Audio and EMI topology | Preserve a single continuous L2 GND reference, quiet I/V/VREF, isolated high-impedance nodes, and a dedicated jack return. | The present L2 GND zone covers the board, but no complete output/clock/power return-current review is possible until routes, stitching and L4 pours exist. Use [Audio/EMI placement review](AUDIO_EMI_PLACEMENT_REVIEW.md), reading its old 100 × 100 mm examples as historical. |
| 4. Fabrication and assembly | Check actual JLCPCB policy, design rules, custom lands, pick-and-place access and BOM fit. | [JLC DFA/DFM rules](JLCPCB_DFA_DFM_RULES.md) and audits are screens only. The current conservative proxy classifies the new U621 and SOD-523 devices; 16 placed references remain outside its package table. Enlarged jack lands, panel rails and slot soldering need order-specific review. |

## Route-risk ledger for the capture baseline and integrated study

| Circuit | Current geometry | Reviewer decision or evidence needed |
| --- | --- | --- |
| X201 → R203 → U301 MCLK | The hand-drawn L1 route passes through TP711: X201→R203 **1.832 mm**, R203→U301 **6.479 mm**, combined **8.311 mm**. R227 has a local GND via and R665→U607 pin 2 is connected; DNF R703 has no copper. | Inspect clock edge quality, oscillator supply/return loop, probe loading, actual duty and U607 monitor behavior. The route meets the geometric 2/8/10 mm screens, but extracted parasitics and powered validation remain open. |
| Four protection timer branches | Worst C/R/Q Manhattan pad-distance lower bound is **7.91 mm** against an 8 mm route rule. | Draw all RC/bleed routes together and check *actual* copper length, reset level, leakage clearance and neighboring clock copper. A lower bound below 8 mm is not a pass. |
| I²S BCLK/LRCLK/SDATA | Current core pad-distance lower bounds 22.11 / 21.24 / 20.48 mm against 25 mm. | Route source → series resistor → DAC with branches, skew, spacing and uninterrupted L2 return. J703 has no PCB pads. |
| DAC → U403/U404 I/V | Four pad-distance lower bounds 3.83 / 6.65 / 6.23 / 3.81 mm against an owner-approved **provisional 7 mm** target. The five local HF bypasses are 1.86–2.30 mm from their DAC rail pins. | Draw all four inputs with GND guards and 2 mm no-digital-copper area, four-way VREF star, local rail returns and Rf/Cf loops. Check actual length, extracted summing-node capacitance and loop area <5 mm². |
| U401/U402 → K601–K604 output legs | The integrated study keeps the original A/B pins, hand-places both amplifiers and their Rf/Cf, and physically connects all four outputs through R417–R420 to relay pad 4. It uses 0.932 mm local VSON escapes, four L4 low-impedance output trunks and L1-only `LEG_*`; all four feedback centreline areas are 4.833 mm². V+ pin 2, both pin-8 EN inputs and C409/C411 now share local VPOS copper. V− pin 4/exposed pad reaches its local 100 nF cap; the cap GND pads return to L2. | Finish the input/T, main VPOS/VNEG source feeds and exposed-pad thermal network; reserve L3/L4 return, extract parasitics and test stability/THD+crosstalk. A local EN tie does not power the amplifier. These are partial-copper connections, not amplifier sign-off. |
| Relay → ESD → J701/J702 audio | The integrated study connects each relay output to its intended J701 pads and LP/RP to J702; paired J701 contacts avoid switch pads and mounting pegs. All six local TVS signal paths measure 3.255–4.03 mm. | Check 1:1 fit and solder access, complete return/power copper and system ESD, then measure R-15. With the [review-only 1 mΩ-max output links](OUTPUT_LINK_BOM_ECO.md), conditional 4.4 mm worst-pad estimates are 0.3864/0.3748 Ω (L/R) at 1 kHz and 0.3992/0.3876 Ω in the 20 kHz model sensitivity. The 3.5 mm signal-only lower bounds are 0.2272/0.2194 Ω; the sleeve return is unextracted. Jack-contact maxima, return paths and loaded measurements remain open. |
| Jack GND and ESD return | The integrated board's jack sleeve pads and both amplifier GND pins physically reach one continuous L2 GND polygon. | Design the L3/L4 reference and all HF bypass/ESD discharge returns; extract shared impedance, then measure loaded crosstalk and perform system IEC ESD. A single filled L2 polygon does not prove the return-current path. |
| USB D+/D− at J101 | Fine-pitch escape has no credible rectangular-grid probe result. | Route the intended 90 Ω differential pair with nominal 0.235 mm width, permitted short 0.15 mm neck-downs and zero vias; check JLC stackup and field-solver impedance. Keep CC/VBUS/protection clear and inspect J101 shield return. |

The manual primary removed the historical 15 sensitive-to-clock *pad* gap findings, but routed copper must still satisfy the 5/10 mm high-impedance separation rules. The integrated board's custom DRC also applies **2 mm F.Cu left/right clearance before the 0 Ω links**: `N4_*_OUT` tracks are checked against the opposite channel's pre-link and `LEG_*`/`JACK_*` copper. The existing 2 mm post-link rule remains. J701's fixed contact pitch needs a narrow local exception for tracks crossing its courtyard against J701 pads, at ≥0.20 mm clearance. Inspect that fanout and the L4 output trunks for crosstalk and manufacturability.

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
python3 hardware/audit_local_tvs_paths.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb --output /tmp/local_tvs.json
python3 hardware/check_functional_eco_layout.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb /tmp/placement.json /tmp/dfa_dfm.json /tmp/jlc_fab.json /tmp/pcb_drc.json
python3 hardware/audit_3d_models.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb --output /tmp/model_3d.json
```

Use [Review findings template](REVIEW_FINDINGS_TEMPLATE.md) to separate **observed board defects** from **route feasibility concerns** and **physical/JLC answers still needed**. A passing script is evidence for its stated screen only. Routing release remains on hold until G-3/G-4 and the listed geometric and audio/EMI checks are closed.
