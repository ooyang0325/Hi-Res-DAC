# Placement, routability and PCBA peer-review guide

Review the editable [120 × 100 mm primary board](DAC_HPA.kicad_pcb), [2D placement](DAC_HPA_120x100_manual_preview.png), [J701/output zoom](DAC_HPA_120x100_output_zoom.png), [clock/analog zoom](DAC_HPA_120x100_clock_zoom.png), [timer zoom](DAC_HPA_120x100_timer_zoom.png), and [3D board](DAC_HPA_3D_review.png). Record board coordinates, layer and references for findings. The 100 × 80 mm and 100 × 100 mm boards are historical comparisons; do not use them as the current routing baseline.

For scalable per-layer views, run the one-command [CLI visual inspection workflow](PCB_CLI_VISUAL_REVIEW.md). It exports the same committed primary board without modifying it.

**Current state:** 536 footprints, 246 named PCB nets, eight F.Cu tracks, four vias, one filled L2 GND zone, and 499 unconnected items. The eight tracks are only four J701 TVS signal escapes and four GND stubs. KiCad DRC reports zero error/warning violations on this *partial* copper. All 470 component footprints resolve 3D bodies; [3D model review](3D_MODEL_REVIEW.md) labels the package approximations. Placement and distance proxies cannot certify simultaneous routes, audio performance, EMI or JLCPCB assembly.

## Review order

| Priority | What to establish | Present evidence and open test |
| --- | --- | --- |
| 1. Connector and hand access | Physical jack/USB fit, board-edge mating, top-side soldering access and package-to-package space. | [G-3 1:1 overlays](G3_OVERLAY_INDEX.md) and [G-4 polarity](G4_POLARITY_CHECKLIST.md) are open. J101 and J702 need JLCPCB acceptance at finished edges and a confirmed soldering process for plated slots. J701's 1.5 mm top-side iron access is preserved in the manual primary. |
| 2. Critical simultaneous routes | Establish *drawable* paths, not just independent lower bounds. | See the route-risk table below. The board is mostly unrouted; request sketches or actual KiCad route trials that include return paths, clearance, vias and all branches. |
| 3. Audio and EMI topology | Preserve a single continuous L2 GND reference, quiet I/V/VREF, isolated high-impedance nodes, and a dedicated jack return. | The present L2 GND zone covers the board, but no complete output/clock/power return-current review is possible until routes, stitching and L4 pours exist. Use [Audio/EMI placement review](AUDIO_EMI_PLACEMENT_REVIEW.md), reading its old 100 × 100 mm examples as historical. |
| 4. Fabrication and assembly | Check the actual JLCPCB policy, design rules, custom lands, pick-and-place access and BOM fit. | [JLC DFA/DFM rules](JLCPCB_DFA_DFM_RULES.md) and audits are screens only. The 20 JLC-placed references outside the package-pair table, enlarged jack lands, panel rails and slot soldering need individual/order review. |

## Route-risk ledger for this placement

| Circuit | Current geometry | Reviewer decision or evidence needed |
| --- | --- | --- |
| X201 → R203 → U301 MCLK | Direct no-stub probe: 9.60 mm; path forced through TP711 has a **10.77 mm straight lower bound** against the 10 mm absolute rule. | Decide how TP711 is accessed without forcing a long MCLK path. Show final routed length, loading and continuous L2 return. |
| Four protection timer branches | Worst C/R/Q Manhattan pad-distance lower bound is **7.91 mm** against an 8 mm route rule. | Draw all RC/bleed routes together and check *actual* copper length, reset level, leakage clearance and neighboring clock copper. A lower bound below 8 mm is not a pass. |
| I²S BCLK/LRCLK/SDATA | Core straight lower bounds 22.82 / 19.91 / 22.05 mm against 25 mm. | Route source → series resistor → DAC with branches, skew, spacing and uninterrupted L2 return; measure every path after routing. J703 has no PCB pads in this primary. |
| DAC → U403/U404 I/V | Four independent grid probes 6.37 / 5.73 / 4.01 / 4.81 mm against an owner-approved **provisional 7 mm** target. | Draw all four with GND guards and 2 mm no-digital-copper area, four-way VREF star and local decoupling. Measure actual length, extracted input capacitance within the 6 pF recheck envelope, feedback-loop copper area <5 mm² and bring-up ringing. [I/V recheck](IV_7MM_RECHECK.md) explains the model limit. |
| Relay → ESD → J701/J702 audio | Only four J701 TVS escapes are routed. Existing independent probes showed K601→J701 at 20.48 mm, K603→J701 at 27.69 mm and K603→J702 blocked in a conservative model, against a 20 mm requirement. | Demonstrate simultaneous 0.5 mm L1 routes to *all* jack contact pads, including J701 paired pads, with ≥2 mm L/R separation outside the jack courtyard, grounded copper between, and no relay-LED current coupling. Measure actual routes. |
| Jack GND and ESD return | Four TVS signals measure 3.83–4.03 mm against a provisional ≤4.2 mm limit; each has a short stub/via to L2. | Provide a ≥3 mm dedicated L1 headphone return strip, at least four L2 vias at each jack ground pin, and a route/plane inspection showing USB surge, LED and jack ESD currents away from quiet analog returns. System IEC ESD testing remains open. |
| USB D+/D− at J101 | Fine-pitch escape has no credible rectangular-grid probe result. | Route the intended 90 Ω differential pair with nominal 0.235 mm width, permitted short 0.15 mm neck-downs and zero vias; check JLC stackup and field-solver impedance. Keep CC/VBUS/protection clear and inspect J101 shield return. |

The manual primary removed the historical 15 sensitive-to-clock *pad* gap findings, but routed copper must still satisfy the 5/10 mm high-impedance separation rules. The J701 footprint needs a narrow local exception to the general 2 mm L/R copper-separation rule; the custom KiCad rule restricts it to tracks within J701's courtyard against J701 pads, at ≥0.20 mm clearance. Inspect that fanout for crosstalk and manufacturability.

## DFA/DFM and physical checks

- Overlay actual J101/J701/J702, relay, oscillator, protection and polarized parts on the [28-pattern G-3 sheets](G3_OVERLAY_INDEX.md); verify terminal overlap, pin 1, body/peg/slot fit and the enlarged jack copper. J701/J702 worst calculated slot ring is ≥0.31 mm under JLC's published +0.13 mm slot-size tolerance; slot-to-copper registration and the 0.25 mm nearest J701 pad gap still require JLC DFM.
- Inspect J101 and J702 mating edges and panel rails with JLCPCB. The current proxy flags them as assembly exceptions to the general 2.5 mm body-to-finished-edge screen. J101's 3D shell was aligned to the existing maker PCB-edge datum; solder lands did not move.
- Confirm soldering of J101 S1–S4 and J702 1/2 plated slots. They currently have no F.Paste apertures. Check the proposed bottom-side J702 hand-solder fallback and access before changing fit class. [PCBA process review](PCBA_PROCESS_REVIEW.md) contains the exact JLC question.
- Check owner-fitted relay and film-capacitor iron access, 3D heights and thermal exposure. The C631–C634 body is a review envelope, and X201–X203 use a generic 2520 model; use physical parts and maker drawings at G-3.
- Review the 435 classified JLC-placed package pairs and 20 unclassified references in `MANUAL_120x100_PRIMARY_DFA_DFM_AUDIT.json`. Zero proxy findings do not guarantee machine access or final soldering. Confirm BOM/rotation in JLC's order preview after layout.

## Reproduce the read-only checks

Use KiCad 10's Python interpreter with `pcbnew` (`python3` in the GitLab KiCad image; on macOS the bundled interpreter path is shown in [README](README.md)). From the repository root:

```sh
python3 hardware/audit_placement.py hardware/DAC_HPA.kicad_pcb --height 100 --check-invariants > /tmp/placement.json
python3 hardware/audit_dfa_dfm.py hardware/DAC_HPA.kicad_pcb > /tmp/dfa_dfm.json
python3 hardware/audit_jlc_fab.py hardware/DAC_HPA.kicad_pcb > /tmp/jlc_fab.json
python3 hardware/audit_esd_routes.py hardware/DAC_HPA.kicad_pcb > /tmp/esd.json
python3 hardware/audit_3d_models.py --output /tmp/model_3d.json
kicad-cli pcb drc --format json --severity-error --severity-warning -o /tmp/pcb_drc.json hardware/DAC_HPA.kicad_pcb
```

Use [Review findings template](REVIEW_FINDINGS_TEMPLATE.md) to separate **observed board defects** from **route feasibility concerns** and **physical/JLC answers still needed**. A passing script is evidence for its stated screen only. Routing release remains on hold until G-3/G-4 and the listed geometric and audio/EMI checks are closed.
