# Manual 120 × 100 mm macro-placement candidate

The editable [candidate PCB](DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb) is a **review-only replacement placement**, generated from the current primary by [226 explicit hand-selected positions](manual_macro_relayout.py). The script performs no placement search or collision resolution. J101/J701/J702, mounting holes, the original four J701 TVS routes and L2 GND zone remain at their existing datums. The primary [DAC_HPA.kicad_pcb](DAC_HPA.kicad_pcb) remains available for comparison and retains its locally corrected top-right outline arc.

The candidate keeps 536 footprints, 246 named PCB nets, four layers and a 120 × 100 mm outline. Its most crowded groups were rebuilt in order: DAC supply pins and U403/U404 feedback/bypass, left/right output-amplifier networks, four U613–U620 low-level detector pairs, U611/U612 OR taps/references, CPLD I²S/clock bypasses and U501 flying/input/output capacitors. [Constraint disposition](CONSTRAINT_DISPOSITION_V2.md) describes the routing-policy changes.

## What changed by measurement

All values below are **pad-centre straight lower bounds**, except the package/DRC findings. They do not establish a drawable route or return path.

| Check | Prior primary | Candidate |
| --- | ---: | ---: |
| U208.8 → C224.1 | 31.68 mm | 5.13 mm |
| U605.8 → C628.1 | 46.23 mm | 2.96 mm |
| U608.8 → C630.1 | 20.13 mm | 2.75 mm |
| U501.11 → C510.1 / U501.6 → C511.1 | 13.27 / 13.95 mm | 3.99 / 2.87 mm |
| R926/R927/R928/R929 high-impedance tap → local filter | 65.13 / 93.33 / 53.78 / 69.81 mm | 1.51 / 2.34 / 2.57 / 2.69 mm |
| X201 → R203 → TP711 → U301 MCLK | 10.77 mm | 8.83 mm |
| I²S BCLK/LRCLK/SDATA core paths | 22.82 / 19.91 / 22.05 mm | 22.11 / 21.24 / 20.48 mm |
| DAC DACL/DACLB/DACR/DACRB → I/V input | 4.81 / 4.72 / 3.13 / 3.95 mm | 3.83 / 6.65 / 6.23 / 3.81 mm |

The two DAC/I/V paths at 6.65 and 6.23 mm are **less comfortable** than in the primary. Their feedback parts and bypasses now occupy a coherent east-side macro, but the routed ≤7 mm limit, input capacitance and <5 mm² feedback loops are still unproven. The longest independent U403/U404 feedback-part pad distances are C419 6.22 mm and C420 5.94 mm. Do not infer loop stability from those distances; the v1.1 calculation model's global gain-margin floor also needs its separate corner review.

## Independent geometry checks

The current [candidate summary](MACRO_STUDY_SUMMARY.json) records zero footprint bounding-box overlaps, zero 5/10 mm clock-to-sensitive-*pad* gap findings, zero KiCad DRC errors/warnings and 499 unconnected items. The JLC package-spacing and body-edge screens have zero classified findings; 20 JLC-placed packages remain outside that matrix, and J101/J702 still need edge/panel/process acceptance. The source netlist comparison passes for all 536 candidate footprints and 246 named nets. The board is still mostly unrouted.

The 28 G-3 overlays, G-4 polarity record, JLC plated-slot/edge decision, local return stitching, thermal and 3D body-height checks remain open. Existing J701 D701–D704 routes still meet the provisional 4.2 mm signal limit; the [J702 two-TVS option](J702_LOCAL_TVS_OPTION.md) is **not** in this 536-footprint candidate.

## Next route trial, before promoting the candidate

1. Draw USB D+/D− together from J101 to U201, with protection/CC/VBUS exits, no vias, quoted-stack-up impedance and continuous L2 return.
2. Draw the MCLK line through TP711 and the R665/U607 monitor connection; route all three I²S source resistors, DAC paths and branches simultaneously. Measure actual lengths/skew and check clock-to-protection copper gaps.
3. Draw all four DAC inputs **with** Rf/Cf, local supply returns, VREF star and GND guards. Extract summing-node capacitance and feedback-loop area rather than comparing only pad distances.
4. Draw U501 flying, VIN/CP/output loops and the regional power feeds. Keep switching return out of quiet analog references.
5. Draw 1.0–1.5 mm candidate headphone trunks and short neck-downs through all relay/jack branches; show the L2/sleeve return and J701/J702 TVS discharge paths. Recalculate output impedance and crosstalk from the routed geometry.
6. Refill L2, inspect top mask/paste and 3D access, then repeat DRC, JLC screens and physical overlays. Keep fabrication/PCBA outputs on hold.

From the repository root, reproduce the placement screens with the KiCad Python that includes `pcbnew`:

```sh
python3 hardware/audit_placement.py hardware/DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb --height 100 --check-invariants > /tmp/macro_placement.json
python3 hardware/audit_dfa_dfm.py hardware/DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb > /tmp/macro_dfa.json
kicad-cli pcb drc --format json --severity-error --severity-warning -o /tmp/macro_drc.json hardware/DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb
python3 hardware/check_macro_study.py hardware/DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb /tmp/macro_placement.json /tmp/macro_dfa.json /tmp/macro_drc.json
```

For zoomable layer and 3D exports, use the candidate command in [CLI visual review](PCB_CLI_VISUAL_REVIEW.md). Keep the commit SHA with any review findings. This candidate is an exploratory placement, **not** a route-ready or PCBA-ready PCB.
