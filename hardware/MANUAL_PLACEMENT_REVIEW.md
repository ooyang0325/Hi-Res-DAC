# DAC-HPA manual 120 × 100 mm layout review — 27 September 2026

**Routing release: HOLD.** The editable primary board is [`DAC_HPA.kicad_pcb`](DAC_HPA.kicad_pcb), now 120 × 100 mm. Every footprint movement in this iteration uses explicit, engineer-selected coordinates in `manual_relayout.py`, `manual_100mm_timer_study.py`, `manual_120x100_study.py`, `manual_120x100_top_access_study.py`, and `manual_clock_escape_study.py`. No placement search or packing was run. `manual_esd_route_probe.py` draws only four manually selected J701 TVS escapes, four short GND stubs and vias, and a continuous L2 GND zone. `place_board.py` now regenerates the separate 100 × 100 mm baseline comparison, not the primary board.

See the [whole board](DAC_HPA_120x100_manual_preview.png), [J701 output detail](DAC_HPA_120x100_output_zoom.png), [timer detail](DAC_HPA_120x100_timer_zoom.png), [clock/analog boundary detail](DAC_HPA_120x100_clock_zoom.png), and [100 × 100 mm timer comparison](DAC_HPA_100x100_timer_preview.png). These images show F.Cu, F.Fab, F.CrtYd and Edge.Cuts from the KiCad PCB, not a conceptual floorplan.

| Read-only check | 100 × 100 mm comparison | 120 × 100 mm primary |
| --- | ---: | ---: |
| Footprints / named nets | 536 / 246 | 536 / 246 |
| Footprint bounding-box overlaps | 0 | 0 |
| JLC classified package-body spacing proxy findings | 0 | 0 |
| JLC classified body-to-edge proxy findings | 0 | 0 |
| Obstructions in the two reserved L1 output corridors | 0 | 0 |
| Worst timer C/R/Q Manhattan pad-distance lower bound | 7.91 mm | 7.91 mm |
| Sensitive-to-clock pad-gap findings | 15 | 0 |
| KiCad DRC errors / warnings | 9 / 0 | 0 / 0 |
| Tracks / vias / filled zones | 0 / 0 / 0 | 8 / 4 / 1 |
| Other unconnected items reported by KiCad | 499 | 499 |

The 100 × 100 mm comparison still has nine J701 top-side solder-access errors. The owner kept 1.5 mm top-side iron clearance and allowed the wider 120 × 100 mm outline. The larger board moves the four TVS diodes outside J701's hand-access courtyard, makes room for the two relay rows, and leaves the L1 output corridors clear. It also removes the previous sensitive-pad proximity to MCLK/I²S/clock-monitor pads without requiring a split ground plane. The L2 zone in the primary is one filled GND polygon; L1 output, digital and analog return paths still require review after all routes are drawn.

## Provisional J701 ESD escape

The owner approved a **provisional ≤4.2 mm signal path** in place of the old 3 mm target, with short TVS ground returns and a system IEC ESD test. This is a design decision for the primary review board, not a JLCPCB assembly limit. The four hand-drawn 0.5 mm F.Cu tracks are D701→J701.7 = 3.83 mm, D702→J701.5 = 4.03 mm, D703→J701.6 = 4.03 mm, and D704→J701.2 = 4.03 mm. Each D701–D704 GND pad has a 1.02 mm 0.5 mm-wide stub to a Ø0.60/0.20 mm via into the filled L2 GND plane. `audit_esd_routes.py` checks the committed copper, and KiCad DRC reports zero errors and warnings. ESD testing, return-current measurement and protection validation are still required.

J701's fixed plated contact pitch cannot meet the project's general 2 mm L/R output-copper separation at its pads. The KiCad custom-rule exception is limited to a track within J701's courtyard against a J701 pad, with 0.20 mm minimum copper clearance. The 2 mm L/R rule remains outside that fanout. A routed crosstalk and return-path review must verify the short exception does not harm audio performance.

## JLCPCB DFA/DFM screen

The KiCad project minima and read-only package/fabrication screens are described in [`JLCPCB_DFA_DFM_RULES.md`](JLCPCB_DFA_DFM_RULES.md). The JLC package-pair screen covers 435 classified parts of 455 listed JLC-placed parts and reports zero body-spacing findings; 20 unclassified parts need individual review. The J101 body crosses the left board edge by 0.05 mm and J702 is 0.33 mm from the right edge, both outside JLC's general 2.5 mm body-to-finished-edge term. The connector/panel arrangement requires JLC acceptance. Enlarged slot lands have a ≥0.31 mm worst ring under JLC's +0.13 mm plated-slot tolerance; physical G-3 overlays, mask geometry and JLC DFM acceptance remain open. After trimming the J702 legend and adjusting D102/X201 polarity marks, KiCad's silkscreen warning pass is clear.

## Work still needed before routing release

1. **Complete actual routing.** The primary has only the four TVS signal and GND returns. KiCad still reports 499 unconnected items. The 0.5 mm L1 headphone outputs, ≥3 mm dedicated headphone GND return, relay contacts, L/R grounded separation, power feeds, USB pair, I²S and MCLK routes are not complete. Check clearances and return continuity after each routed group.
2. **Close length and signal-integrity checks.** The four timer branches have only a ≤7.91 mm Manhattan pad-distance lower bound against the 8 mm route rule. The I²S source→series resistor→DAC straight lower bounds are 22.82/19.91/22.05 mm against 25 mm; routed lengths and skew are unknown. The MCLK path through TP711 has a 10.77 mm straight lower bound against the 10 mm limit, so that branch needs a disposition. DAC-to-I/V, feedback-loop area, USB impedance and high-impedance-versus-clock copper clearance still require routes and extraction.
3. **Close audio and assembly gates.** Relay-to-jack routes and the meaning of the 20 mm requirement for J701 paired contacts need a routed review. G-3 sample overlays and G-4 polarity checks remain open. Obtain JLC's treatment of J101/J702 edge placement, plated-slot soldering, J701 mask openings, unclassified package gaps and panel rails before ordering. The source DOCX/XLSX design set still states the older outline and ESD target and needs a controlled revision before manufacturing freeze.

A passing placement, JLC proxy, or KiCad DRC check does not demonstrate completed routing, USB impedance, THD+N, crosstalk, EMI immunity, output impedance or a buildable PCBA package. Do not submit this partial board for production.
