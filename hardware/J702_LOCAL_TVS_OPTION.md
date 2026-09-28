# J702 local TVS fit and circuit option

J701 and J702 share JACK_LP/JACK_RP, but their matching contacts are about 35/27 mm apart. A TVS at J701 cannot also be a few millimetres from J702. The [board-only option generator](j702_esd_option.py) adds D707 (RP) and D708 (LP) to a **separate** placement study using the same [GOODWORK LESD5D5.0CT1G, JLC C41399463](https://jlcpcb.com/partdetail/GOODWORK-LESD5D50CT1G/C41399463) as D701–D704. **No schematic, Parts List or assembly BOM ECO has been made.**

| Fit/route study | Result |
| --- | --- |
| D707 RP | x152.0/y102.3 mm, 180°. The hand-drawn 0.5 mm L1 route K603.6 → D707.1 → J702.3 is DRC-clean at 9.785 mm total; the D707.1 → J702.3 portion is 3.861 mm. |
| D708 LP | x148.31/y117.1 mm, 270°. Its 0.5 mm J702.4 → D708.1 branch is 3.25 mm. The K601 → J702 main LP route is **not** drawn. |
| ESD return | Each diode has a 0.5 mm short GND stub to a Ø0.60/0.20 mm via into continuous L2. The option DRC has zero error/warning violations. |
| Solder access | D707 fits between K603 and J702; D708 fits below J702. The option satisfies the current 1.5 mm jack/relay courtyard access rule in KiCad. |

The generic rectangular `J702_to_lower_relays` corridor screen flags D707 because it occupies that reservation. Its location is intentional: D707 is a connection point **on** the RP path. The hand-drawn RP relay-to-jack copper passes DRC, but the full LP trunk, both returns, simultaneous channel routing and solder-tool approach still need physical review. A zero DRC count is not system ESD validation.

The [option geometry summary](J702_ESD_OPTION_SUMMARY.json) records the routed lengths and access checks. The JLC package-pair audit's zero classified findings cover the existing 455 JLC-placed references; D707/D708 are **not in the assembly BOM and are not classified by that proxy**. They need individual JLC package and order review if the ECO is adopted.

The [manufacturer datasheet](https://xonstorage.z8.web.core.windows.net/pdf/goodwork_lesd5d50ct1g__xonlink.pdf) gives 12 pF typical / 18 pF maximum junction capacitance at 0 V, 1 MHz, and 1 µA maximum leakage at 5 V stand-off. The v1.1 calculation package already models **15 pF** at each protected jack node and records an approximately 4.01 V peak output leg envelope. Adding another device on each shared LP/RP net suggests 24 pF typical and 36 pF maximum total device capacitance on those nets, before PCB/cable parasitics.

The [reproducible selected-corner sweep](review_j702_tvs_sensitivity.py) changed only that linear JACK-to-GND term in the package's calibrated OPA1622/switch model. Its [JSON results](J702_TVS_SENSITIVITY_REVIEW.json) are:

| Total modeled TVS capacitance | Worst phase margin | Minimum gain margin | Maximum sensitivity peak |
| ---: | ---: | ---: | ---: |
| 15 pF baseline | 49.712° | 7.861 dB | 6.145 dB |
| 30 pF candidate | 49.612° | 7.843 dB | 6.158 dB |
| 36 pF maximum-capacitance case | 49.572° | 7.835 dB | 6.162 dB |

Those differences are small **in this selected linear model**. The sweep is not an extracted board, nonlinear TVS or full cable/relay/ESD simulation. Before a formal D707/D708 ECO, review the diode's voltage-dependent capacitance and leakage across signal swing/temperature, output THD+N and stability, IEC discharge-current return, JLC placement/stock and physical samples. Then update the controlled workbook, schematic generator, BOM, 3D model review and CI netlist counts together. The separate option board is not PCBA order data.
