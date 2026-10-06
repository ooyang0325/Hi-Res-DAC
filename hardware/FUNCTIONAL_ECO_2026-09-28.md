# Functional schematic ECO: readbacks, J702 ESD and I/V channel assignment

**Status:** captured in the KiCad schematic and review BOM, with the I/V channel assignment updated on 29 September 2026. The unchanged Parts List v0.9 and Calculation Package v1.1 remain the baseline. `generate_schematic.py` asserts the baseline pin maps before applying this ECO; `verify_schematic.py` checks the exact 34 source-to-schematic pin/net differences. This is a review capture, not a schematic or fabrication release. The full-rate capture guard, measured 3V3M attach current and physical gates remain open.

## I/V macro: equivalent amplifier channels reassigned

The two channels of each OPA2210IDGKR are functionally equivalent. The manually selected VSSOP placement assigns each positive DAC current leg to physical amplifier B and each negative leg to amplifier A. The feedback R/C, clamps, common-mode taps, DAC pads and downstream T inputs remain on their original named nets; only four U403 pins and four U404 pins change net assignment. This is an explicit schematic ECO so the PCB pad map can be checked against the captured circuit.

| Op amp | Physical A: pins 2 input / 1 output | Physical B: pins 6 input / 7 output |
| --- | --- | --- |
| U403 | `DACLB` / `N4_IVL_N` | `DACL` / `N4_IVL_P` |
| U404 | `DACRB` / `N4_IVR_N` | `DACR` / `N4_IVR_P` |

The [integrated route study](INTEGRATED_AUDIO_ROUTE_STUDY.md) checks the corresponding copper and the provisional ≤7 mm DAC-to-I/V routes. Its plan-view feedback-area screen is a placement check, not extracted stability or a fabrication approval.

## F02: supervisor readback isolation

The independent functional review identified insufficient worst-case logic margin where U605's open-collector 3V3A-good outputs reach U201 PA12/PB9 through R688/R689 = 470 kΩ. These resistors remain in place to avoid changing the comparator's existing pull-up/hysteresis network. A dual noninverting Schmitt buffer now senses the isolated nodes and drives the MCU inputs:

| Reference | Value / JLC code | Pin or connection |
| --- | --- | --- |
| R688/R689 | Existing 470 kΩ | Pin 1 stays on `N6_V3AG_A/B`; pin 2 now goes to `N6_V3AG_A/B_BUF_IN`. |
| U621 | TI SN74AUP2G17DCKR, C507231 | Pin 1 = A input; 2 = GND; 3 = B input; 4 = B output; 5 = 3V3M; 6 = A output. Noninverting channels preserve the existing fault-high polarity. |
| R952/R953 | 10 kΩ, C25744 | Between each U621 output and the existing MCU readback net `N6_V3AG_A/B_MCU`. |
| R954/R955 | 100 kΩ, C25741 | From 3V3M to each MCU-side readback net; an open U621 output reads high. |
| C667 | 100 nF, C1525 | 3V3M to GND at U621 pin 5; placement must keep the supply/return loop local. |

U201 pin 45 (PA12) and pin 62 (PB9) retain their existing readback net names. U605 pins 1/7 and Q619/Q620 hardware interlock connections are unchanged. The buffer is powered from the same always-on 3V3M domain as U605 and U201; the existing hardware gate remains independent of MCU readback firmware.

The [TI SN74AUP2G17 datasheet](https://www.ti.com/lit/ds/symlink/sn74aup2g17.pdf) confirms the six-pin DCK map, 0.5 µA maximum input leakage over −40 to 85 °C, and 3.0 V Schmitt thresholds of at most 2.29 V rising and at least 0.88 V falling. A resistor-network screen at the documented 3V3M minimum of 3.207 V gives approximately 2.919 V at a released U621 input under 0.5 µA leakage. With a low U605 output, the [TI TLV3402 datasheet](https://www.ti.com/lit/ds/symlink/tlv3402.pdf) lists 0.30 V maximum `VOL` at 50 µA over its full temperature range; adding the worst 0.235 V drop across 470 kΩ gives an approximately 0.535 V U621 input. These are useful margins against TI's **3.0 V table row**; TI does not publish those threshold extrema at exactly 3.207 V, so the full rail/temperature corner remains a qualification check.

On the MCU side, a 100 kΩ pull-up alone holds a disconnected high readback at approximately 2.907 V with 3 µA MCU input leakage at 3.207 V, above the reviewed 1.591 V high requirement. A conservative screen with 0.45 V U621 output-low, a 10 kΩ series resistor, a 100 kΩ pull-up and 3 µA leakage into the MCU node gives approximately 0.728 V, below the reviewed 1.000 V low limit. These calculations do not prove startup sequencing, comparator hysteresis, metastability, a broken ground, or firmware self-test behavior; test both comparator states and the rail-fault response over voltage and temperature. MCU internal pull resistors must remain disabled for these readbacks.

## F04: local J702 ESD devices

D707 connects `JACK_RP` to GND and D708 connects `JACK_LP` to GND. Both are the same GOODWORK LESD5D5.0CT1G, JLC C41399463, as the J701 devices. Their KiCad footprint and two-pin map are inherited from D701/D702. The earlier [J702 fit trial](J702_LOCAL_TVS_OPTION.md) remains a physical starting point; the revised candidate board must retain short signal branches and direct local GND vias while proving the complete audio and return routes.

The existing calculation package models 15 pF of device capacitance at each protected jack net. The [GOODWORK datasheet](https://xonstorage.z8.web.core.windows.net/pdf/goodwork_lesd5d50ct1g__xonlink.pdf) lists 12 pF typical / 18 pF maximum per device at 0 V and 1 MHz. Two parallel devices per LP/RP net therefore imply 24 pF typical / 36 pF maximum before PCB and cable parasitics. The [selected-corner sensitivity study](J702_LOCAL_TVS_OPTION.md) found little movement in its linear stability metrics; output THD+N, nonlinear capacitance/leakage, discharge return and IEC system ESD still require measurement and review.

## CAD and manufacturing checks

- The exact JLC C507231 EasyEDA Pro device was added to `JLC_Source/JLC_DAC_HPA.elibz`. Its [native footprint](JLC_Imported.pretty/SC-70-6_L2.2-W1.3-P0.65-LS2.1-BL.kicad_mod) and [normalized STEP body](EASYEDA_MODELS/SC-70-6_L2.0-W1.3-H1.0-P0.65.step) came from that device. The model's original and converted SHA-256 values are recorded in `EASYEDA_MODELS/MODEL_SOURCES.json`.
- `verify_eco_assets.py` compares the source and native six-pad geometry, checks the 0.30 mm minimum internal pad-copper gap, and verifies the STEP hash. The [TI DCK0006A example land](https://www.ti.com/lit/ds/symlink/sn74aup2g17.pdf) has a 2.2 mm opposing pad-centre span; JLC's supplied C507231 land uses 1.68 mm. The exact JLC CAD is used for this JLC assembly candidate, but G-3 physical overlay and JLC DFM must resolve that difference before order.
- The review BOM now contains 463 JLC-placed references, including all eight ECO parts. The [current board](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb) has 544 footprints after excluding J703. The workbook's nominal 3V3M capacitor inventory was 6.4 µF; C667 increases it to **6.5 µF**. The [inventory-derived planning screen](ATTACH_CHARGE_RECONCILIATION.json) gives **43.695 µC** Region A without a load credit under its stated capacitor/temperature bound, leaving 6.305 µC against the 50 µC project criterion. The v1.1 calculation package still has the older 6.05 µF input; voltage-dependent charge, regulator output-cap stability and measured attach-current overlap remain qualification gates.
- Regeneration and checks: 534 schematic components, 1,465 pin rows, 1,422 connected pins, 43 no-connect pins, 250 named nets, 545 assigned schematic symbol/footprint pad sets, and **0 KiCad ERC violations**. The 1,445 workbook pin rows still match the calculation package exactly. The separately edited board must be synchronized, DRC checked and routed before PCBA upload.

**Open functional dependency:** the CH32V307 MCU's published I²S clock limit still affects the post-CPLD guard above 96 kHz. The [SPI2/DMA capture proposal](MCU_SPI2_CAPTURE_ECO.md) avoids the published I²S clock limit on the same pins, but lacks implemented firmware/RTL and a proved monitor for DAC-side WS faults. F01 and its high-rate frozen-word fault-energy credit remain open.
