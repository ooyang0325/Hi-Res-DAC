# DAC-HPA placement and routability review — 27 September 2026

**Routing status: HOLD.** The owner selected 100 × 100 mm as the primary outline and approved OPA2210IDGKR VSSOP-8 plus a provisional reassessment of the DAC-to-I/V limit to 7 mm. The editable `DAC_HPA.kicad_pcb` reflects those choices. `DAC_HPA_100x80_REVIEW_ONLY.kicad_pcb` retains the original 100 × 80 mm outline for comparison. Neither has tracks or copper zones; neither is a fabrication or PCBA package.

`audit_placement.py` reads actual KiCad pad and courtyard geometry. A separate exploratory L1 grid probe uses 0.1 mm cells and rectangular pad obstacles; it routes each net independently. Those checks cannot prove simultaneous routing, real return paths, fabrication clearance, impedance or full DRC.

## Effect of the iteration

| Measurement | First 100 × 80 SOIC pass | 100 × 80 VSSOP comparison | 100 × 100 VSSOP primary |
| --- | ---: | ---: | ---: |
| Schematic-linked footprints / named nets | 537 / 246 | 537 / 246 | 537 / 246 |
| Footprint bounding-box overlaps | 0 | 0 | 0 |
| Preferred-region spills | not audited | 24 | 2 |
| DACL / DACLB / DACR / DACRB straight pad distances | 8.05 / 12.36 / 9.66 / 8.31 mm | 4.81 / 4.72 / 3.13 / 3.95 mm | same |
| HSE IN / OUT pad distances | 9.64 / 7.31 mm | 7.36 / 6.30 mm | 4.97 / 3.22 mm |
| Longest LPW timer-cap centre to comparator centre | not audited | 22.51 mm | 5.02 mm |
| Z4S / Z4L / Z5 bounding-box fill | 66.90 / 56.89 / 68.88 % | 74.27 / 65.23 / 62.98 % | 71.80 / 65.46 / 50.44 % |
| High-impedance nets with clock-pad gaps below their 5/10 mm target | not audited | 19 | 15 |

The fill values clip component bounding rectangles to approximate, overlapping functional zones. They are density proxies, not copper-fill percentages. Z4S and Z4L still exceed the Notes' 60% target even on the larger outline. The comparison shows why the 100 × 80 mm variant was not carried forward, but the new outline still needs analog-core and protection repacking.

## Critical signal paths

- **DAC to I/V:** Individual 0.20 mm grid estimates are 6.37/5.73/4.01/4.81 mm. All are below the provisional 7 mm target, but the four paths, GND guards, VREF star, decoupling and feedback loops have not been routed together. The former 5 mm rule and SOIC MPN remain in the source Office documents. `IV_7MM_RECHECK.md` records the model sensitivity and package evidence.
- **MCLK:** Moving X201, R203 and C217 north by 1 mm shortens the individual X201→R203 and R203→DAC route probes to 1.64 + 7.96 = **9.60 mm**. R665→U607 remains 1.75 mm straight; R665 pad 1 is 1.68 mm from DAC XI versus the 1.5 mm placement target. The present TP711 is off the direct trace; including it has a **10.77 mm straight-line lower bound** against the absolute 10 mm rule. Its test-access arrangement needs a design decision.
- **I²S and USB:** Independent BCLK/LRCLK/SDATA probes give 19.60/18.57/21.10 mm before branches, against 25 mm; spacing, skew and return continuity remain open. The USB input pad distances have improved: D102 VBUS→J101 4.89 mm, U101 D+/D−→J101 3.85/4.92 mm, U103 CC1/CC2→J101 2.30/2.95 mm. The fine-pitch USB escape defeated the rectangular grid probe, so the required 90 Ω pair still needs a true route and impedance check.
- **Headphone outputs:** J701/J702 moved 1.5 mm toward each other, and the two upper relays moved closer to J701 on the 100 × 100 mm board while K601–K604 retain ≥1.5 mm owner-fitted iron clearance. At the required 0.5 mm width, independent probes now estimate `JACK_LN` K602→J701 at 12.74 mm and `JACK_RN` K604→J701 at 7.94 mm; `JACK_LP` K601→J702 is 19.50 mm. The K601→J701 path is still 20.48 mm, K603→J701 is 27.69 mm, and K603→J702 was blocked by the conservative pad model. The 20 mm rule is not yet met. J701's paired contact pads require local branches, and the dedicated ≥3 mm headphone ground strip has not been laid out.
- **Jack ESD and assembly:** D701–D704 are 2.76–2.98 mm straight from the nearest J701 audio pads, meeting the ≤3 mm signal-pad target. Their footprints intrude on the Notes' ≥3 mm hand-solder access region around J701; the assembly and ESD placement instructions conflict and need a reviewed solution.

`AUDIO_EMI_PLACEMENT_REVIEW.md` lists the 15 pad-level clock/high-impedance conflicts and the required continuous L2 return and headphone-ground topology. The current board contains **zero tracks and zero copper zones**, so audio quality, EMI behaviour, USB impedance and crosstalk are not yet verified. The larger outline does not confer electrical isolation by itself.

## Remaining decisions and release work

The service-header J703 pads create several high-speed I²S proximity conflicts in the analog protection area; its purpose and PCB footprint need a decision. TP711 forces the MCLK path beyond the absolute limit if it stays on the trace. Those decisions, the U607 clock-monitor repack, Z4S/Z4L density, 0.5 mm headphone routes and jack ESD/iron clearance remain before a route-ready placement can be claimed.

After the decisions, draw the actual copper, ground and power pours, then measure routed lengths, feedback-loop area, differential impedance, L/R spacing, return paths and thermal clearance. Run complete KiCad DRC and JLC DFM, and retain G-3/G-4 physical gates. [JLCPCB lists OPA2210IDGKR/C2876414](https://jlcpcb.com/partdetail/TexasInstruments-OPA2210IDGKR/C2876414) for Extended SMT assembly with pre-order instructions; five-board quantity and reserved stock are unconfirmed. The source DOCX/XLSX set still needs the owner-approved MPN, 7 mm candidate rule and 100 × 100 mm outline recorded before manufacturing freeze.
