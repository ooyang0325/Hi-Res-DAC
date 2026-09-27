# Audio integrity and EMI placement review — 27 September 2026

For the current hand-placed 120 × 100 mm primary and its routed J701 TVS escapes, see `MANUAL_PLACEMENT_REVIEW.md`. The pad-gap findings below describe the earlier 100 × 100 mm automatic baseline unless that review reports a correction.

**Historical baseline status: HOLD.** The earlier 100 × 100 mm board had no tracks, ground plane, power pours or stitching vias. Its analog/digital isolation, impedance, channel separation, noise and crosstalk could not be certified from placement. `PLACEMENT_100x100_BASELINE_AUDIT.json` is its reproducible pad-level screen. The new primary has an L2 GND zone and four TVS routes but remains mostly unrouted and unqualified for audio or EMI performance.

## Ground and return architecture to implement

The v1.1 Spec R07/R10 and Notes §9.3.2 specify **one GND net and an unbroken L2 ground plane**. Digital devices stay west, analog signal paths east, and power conversion south-west. Separation comes from component placement and controlled signal/return paths; no ground-plane split is permitted. L1 carries USB, clocks, I²S and audio; L3 carries regional power and slow controls, L4 slow analog/control over a stitched GND pour. The current board has **zero copper zones and zero tracks**, so this architecture is still a routing requirement.

At the DAC, DGND, AGND and AGND_L/R need local L2 vias and the exposed pad needs five vias. Each fast signal must retain its L2 return beneath the entire route, including at the digital-to-DAC boundary. The output-stage ground and headphone sleeves need a dedicated ≥3 mm L1 return strip with at least four L2 vias at each jack ground pin; USB surge, LED-string and jack ESD currents must not share that strip. Jack ESD returns go through L2 to the jack ground pins. These are concrete topology checks for the eventual PCB, not connections inferred from the GND net name.

## Measured placement conflicts

The earlier audit measured minimum copper-to-copper gaps between *pad bounding rectangles* on high-impedance protection nets and clock nets. It found **15 nets below the Notes' 5 or 10 mm separation targets** on the historical 100 × 100 mm automatic board, versus 19 on the 100 × 80 mm comparison. The current 120 × 100 mm manual primary reports zero pad-gap findings; routed-copper review is still required. The earlier examples are:

| Sensitive pad/net | Clock pad/net | Pad gap | Required separation |
| --- | --- | ---: | ---: |
| R680.2 `N6_V3AG_A` | C624.1 `N6_MCK_BUF` | 0.96 mm | 5 mm |
| R678.1 `N6_V3R_A` | C624.2 `N6_PMP` | 1.02 mm | 5 mm |
| R939.1 `N6_VLLP` | TP715.1 `BCLK` | 1.20 mm | 10 mm |
| R947.2 `N6_TWRPN` | J703.2 `BCLK` | 1.79 mm | 5 mm |
| R932.2 `N6_LWRP` | J703.4 `SDATA` | 1.98 mm | 5 mm |
| U620.3 `N6_VLLN` | D609.3 `N6_PMP` | 3.08 mm | 10 mm |

Moving R940/R941 away from the MCLK corridor removed the previous 0.83 mm `N6_VLLN`–`N6_MCK_IN` pad conflict. The wider problem remains: C624, D609 and their 80 MHz surveillance network are scattered around the LPW/high-impedance group rather than clustered around U607. J703 is a DNF service header, but its copper pads and branches still exist on the high-speed I²S nets. A fixed-footprint search found no free position near U202; the nearest alternative was about 24 mm from the CPLD centre, which would add a long clock branch. The disposition of J703 is an owner decision.

The independent 0.20 mm grid probes estimate R204/R205/R206 to DAC BCLK/LRCLK/SDATA at 19.60/18.57/21.10 mm, within 25 mm individually. They omit the three signal branches and do not establish 3W spacing, length matching within 5 mm, uninterrupted L2 returns or guard copper. FAM_CLK probes at 3.25 mm, also individually. The USB pair has no valid probe result because the conservative rectangular obstacle model cannot resolve the fine-pitch connector escape; a real 0.235/0.15 mm, 90 Ω pair with permitted short neck-downs and zero vias must be routed and field-solver checked.

## Quiet DAC/I/V and headphone output

The owner-approved VSSOP U403/U404 gives four independent 0.20 mm DAC-to-I/V grid estimates of 6.37/5.73/4.01/4.81 mm, below a **provisional** 7 mm input limit. It does not yet show simultaneous routes, matched DAC output neighbourhoods, GND guards, the 2 mm no-digital-copper envelope, a four-way VREF star, or the <5 mm² Rf/Cf feedback loops. Feedback-part pad distances reach 6.85 mm in the present placement, so loop area needs an explicit copper-polygon calculation after routing. The model recheck and its limitations are in `IV_7MM_RECHECK.md`.

The headphone output rule calls for 0.5 mm L1 paths from each relay through the jack ESD pad to the jack contact, each ≤20 mm, L/R never interleaved and separated by ≥2 mm with grounded copper between. Moving K602/K604 closer to J701 improved their individual 0.5 mm probes to 12.74/7.94 mm while preserving the 1.5 mm soldering-iron clearance. K601→J702 probes at 19.50 mm. The same conservative probe still found `JACK_LP` K601→J701 at 20.48 mm, `JACK_RP` K603→J701 at 27.69 mm, and K603→J702 blocked. These are screening estimates, but the placement cannot be called routable. J701's second contact pads on the same nets also need local copper branches, and the jack sleeve return needs its own wide L1 path. Relay LED-current routing must keep ≥2 mm from the audio output copper.

## Route acceptance checks

1. Resolve the service-header and MCLK test-point choices. A no-stub X201→R203→DAC path probes at 9.60 mm; forcing the present TP711 through it has a 10.77 mm straight-line lower bound against the absolute 10 mm rule.
2. Repack the U607/C624/D609 clock monitor away from the LPW and 3V3A high-impedance nodes; rerun the pad-gap audit until every required separation is geometrically possible. Keep the MCLK and I²S paths above continuous L2 GND.
3. Route the four DAC inputs together with guards, VREF, feedback and supply decoupling; measure actual lengths, neighbourhood symmetry, feedback-loop copper area and the 2 mm digital exclusion. Recheck the provisional 7 mm model envelope with extracted capacitance.
4. Route every relay-to-ESD-to-jack output at 0.5 mm and show length, L/R separation, ESD return and the dedicated jack-ground strip on the real board. The 20 mm output limit must apply to copper, not pad distance.
5. Fill and inspect L2/L4, place the local ground/stitch vias, run full KiCad DRC, review return-current continuity and near-field/crosstalk risk, then validate noise, THD+N, output impedance and channel separation on hardware against the Spec's limits.

Manufacturer guidance is consistent with the source documents' continuous return-plane approach: [TI's mixed-signal grounding note](https://www.ti.com/lit/an/slyt512/slyt512.pdf) and [Analog Devices' mixed-signal grounding article](https://www.analog.com/en/resources/technical-articles/2022/07/16/11/32/successful-pcb-grounding-with-mixedsignal-chips--follow-the-path-of-least-impedance.html). The numerical distances and hold decisions above come from the project's design notes and KiCad geometry audit.
