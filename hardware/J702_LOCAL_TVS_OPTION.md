# J702 local TVS schematic ECO and placement trial

J701 and J702 share JACK_LP/JACK_RP, but their matching contacts are about 35/27 mm apart. A TVS at J701 cannot also be a few millimetres from J702. The [functional ECO](FUNCTIONAL_ECO_2026-09-28.md) now captures D707 (RP) and D708 (LP) in the KiCad schematic and review assembly BOM. They use the same [GOODWORK LESD5D5.0CT1G, JLC C41399463](https://jlcpcb.com/partdetail/GOODWORK-LESD5D50CT1G/C41399463) as D701–D704. Parts List v0.9 and Calculation Package v1.1 remain the immutable baseline; the ECO is asserted in the schematic generator. The [separate board-only trial](j702_esd_option.py) below was an earlier fit study and is not PCBA order data.

| Fit/route study | Result |
| --- | --- |
| D707 RP | x152.0/y102.3 mm, 180°. The hand-drawn 0.5 mm L1 route K603.6 → D707.1 → J702.3 is DRC-clean at 9.785 mm total; the D707.1 → J702.3 portion is 3.861 mm. |
| D708 LP | x148.31/y117.1 mm, 270°. Its 0.5 mm J702.4 → D708.1 branch is 3.25 mm. The K601 → J702 main LP route is **not** drawn. |
| ESD return | Each diode has a 0.5 mm short GND stub to a Ø0.60/0.20 mm via into continuous L2. The option DRC has zero error/warning violations. |
| Solder access | D707 fits between K603 and J702; D708 fits below J702. The option satisfies the current 1.5 mm jack/relay courtyard access rule in KiCad. |

The generic rectangular `J702_to_lower_relays` corridor screen flags D707 because it occupies that reservation. Its location is intentional: D707 is a connection point **on** the RP path. The hand-drawn RP relay-to-jack copper passes DRC, but the full LP trunk, both returns, simultaneous channel routing and solder-tool approach still need physical review. A zero DRC count is not system ESD validation.

The [option geometry summary](J702_ESD_OPTION_SUMMARY.json) records the earlier routed lengths and access checks. D707/D708 are now in the [review assembly BOM](JLCPCB_BOM_REVIEW_ONLY.csv), increasing its JLC-placed count from 455 to 463 with the other functional ECO parts. The [current schematic-aligned board](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb) carries the same short branches and local vias; its [layout summary](FUNCTIONAL_ECO_LAYOUT_SUMMARY.json) checks the placement and pad nets. Full audio/return routing, package clearance and stock remain open before any order.

The [manufacturer datasheet](https://xonstorage.z8.web.core.windows.net/pdf/goodwork_lesd5d50ct1g__xonlink.pdf) gives 12 pF typical / 18 pF maximum junction capacitance at 0 V, 1 MHz, and 1 µA maximum leakage at 5 V stand-off. The v1.1 calculation package already models **15 pF** at each protected jack node and records an approximately 4.01 V peak output leg envelope. Adding another device on each shared LP/RP net suggests 24 pF typical and 36 pF maximum total device capacitance on those nets, before PCB/cable parasitics.

The [reproducible selected-corner sweep](review_j702_tvs_sensitivity.py) changed only that linear JACK-to-GND term in the package's calibrated OPA1622/switch model. Its [JSON results](J702_TVS_SENSITIVITY_REVIEW.json) are:

| Total modeled TVS capacitance | Worst phase margin | Minimum gain margin | Maximum sensitivity peak |
| ---: | ---: | ---: | ---: |
| 15 pF baseline | 49.712° | 7.861 dB | 6.145 dB |
| 30 pF candidate | 49.612° | 7.843 dB | 6.158 dB |
| 36 pF maximum-capacitance case | 49.572° | 7.835 dB | 6.162 dB |

Those differences are small **in this selected linear model**. The sweep is not an extracted board, nonlinear TVS or full cable/relay/ESD simulation. The schematic ECO remains provisional until voltage-dependent capacitance and leakage across signal swing/temperature, output THD+N and stability, IEC discharge-current return, JLC placement/stock and physical samples are reviewed. The current board places the pair locally; both output trunks, returns and solder access still have to coexist on a completed route.
