# R417–R420 output-link BOM candidate — 28 September 2026

This is a review-only, same-value substitution for the four removable 0 Ω
design-for-test links. The pin nets and `R_0402_1005Metric` land stay the same.
R107, the USB shield link, remains on the original part. The controlled v0.9
Parts List and v1.1 Calculation Package remain unchanged; the generated
schematic and review BOM assert this overlay explicitly.

| Item | Source workbook | Review candidate |
| --- | --- | --- |
| R417–R420 | UNI-ROYAL 0402WGF0000TCE, JLC C17168, 0 Ω / ≤50 mΩ link budget | [YAGEO PA0402-R-070RL, JLC C4044221](https://jlcpcb.com/partdetail/YAGEO-PA0402_R070RL/C4044221), 0 Ω / [≤1 mΩ manufacturer maximum](https://www.yageogroup.com/content/Resource%20Library/Datasheet/PYU-PA_JUMPER_L_51_ROHS.pdf) |
| Assembly | 0402 SMT | 0402, JLC Extended SMT; stock was observed on 28 September 2026 and must be checked again at order |

Yageo's PA0402 code-07 table rates the jumper at 11 A and 1/8 W. JLC's
catalogue instead displays 62.5 mW, so the power-field discrepancy needs
order-stage clarification. The PCB trace, pads and relay contacts have their
own current and thermal limits; the component rating does not establish a
board rating. Check the actual JLC land/rotation and paste preview against
the current generic 0402 footprint before assembly release.

## Electrical budget

The v1.1 R-15 model uses **50 mΩ per fitted output link**. Replacing that
term with the Yageo **1 mΩ maximum** subtracts 49 mΩ per leg or 98 mΩ
from a balanced loop. The model's nominal starting values consequently
change from 0.25133 to 0.20233 Ω at the 3.5 mm jack and from 0.38266 to
0.28466 Ω at the 4.4 mm jack, before this PCB's routed-copper adjustment.
This is a comparison of specified maxima in an engineering model. It does
not predict a 49 mΩ measured improvement over the original physical
jumpers, whose actual resistance may be well below their maximum.

For the [manually routed integrated study](INTEGRATED_AUDIO_ROUTE_STUDY.md),
the [copper audit](INTEGRATED_AUDIO_TRACE_BUDGET.json) replaces the model's
20 mΩ trace allowance with the routed signal-path estimate and illustrative
via barrels. Its worst J701 pad paths with the candidate are:

| Channel | 1 kHz model | 20 kHz model sensitivity |
| --- | ---: | ---: |
| Left | 0.3862 Ω | 0.3990 Ω |
| Right | 0.3737 Ω | 0.3864 Ω |

The 20 kHz estimate uses the calculation package's OPA1622 closed-loop
output impedance. It is conditional on the **50 mΩ per jack-contact
engineering estimate**, 35 µm copper at 50 °C, illustrative via plating,
and the modelled amplifier response. The 3.5 mm audit gives signal-only
lower bounds of 0.2255 Ω left and 0.2188 Ω right; its sleeve return is not
routed/extracted. No maker maximum for the jack contact is available.
**Neither jack has a measured ≤0.5 Ω R-15 result.**

## Model sensitivity beyond R-15

An isolated temporary extraction of the v1.1 calculation package was used.
For `r2_power.py` and `r10_fixes.py`, `r2_common.R_LINK` and its derived
series terms were rebound from 0.050 to 0.001 Ω in memory. Temporary
copies of `r3_fixes.py` and `stability_switch.py` changed only their
0.05 Ω output-link element to 0.001 Ω; their 5 nH link/trace parasitic
stayed fixed. The rounded High-mode peak
power changed from 54.9 to 55.0 mW at the 3.5 mm/32 Ω load and from
114.3 to 114.7 mW at the 4.4 mm/60 Ω load. At a **fixed Default
firmware/leg-drive ceiling**, the 3.5 mm/32 Ω jack rises from 38.000 to
38.116 mW. The modelled `5V_ANA` peak including `ANA_SENSE` rises from
178.961 to 179.114 mA, reducing the thin eFuse margin from 1.090 to
0.937 mA. Retuning the drive to hold exactly 38 mW would instead reduce
the current slightly, but that is a separate firmware action and is not
assumed for this BOM-only ECO. The eFuse/current result depends on the
LM27762 and auxiliary-current estimates and remains a bench gate.
The closed-switch amplifier/cable model retained about 51.3° phase margin,
with gain margin changing from 7.7 to 7.6 dB; its 2 nF case changed
from 47.2° to 47.1° phase margin. These are model sensitivities with the
same assumed parasitics, not a routed-board stability result.

The LEG protection taps sit after the links. At the calculation package's
190 mA output-current bound, the lower maximum link drop shifts LEG by at
most 9.31 mV relative to the amplifier output. Detector thresholds and
timers are unchanged, but normal-content false trips and fault timing
still require the stated bring-up tests.

The package's protection-energy equations use ideal load `V²/R` and do
not take credit for the old 50 mΩ link. A separate fixed-source illustrative
32 Ω balanced case changed from 14.546 to 14.634 mJ, below the 15 mJ
screen, but the existing no-swing-credit High-mode frozen-word case can
still exceed it. A-45 and the short-circuit gate remain **open**. The
lower-DCR jumper is not a fuse and does not provide the optional ferrite's
33 Ω at 100 MHz ESD impedance.

## Acceptance before choosing the part for PCBA

1. Recheck JLC assembly stock, exact footprint/rotation and the power
   catalogue discrepancy, then confirm the intended four designators in the
   final BOM and placement file. A stock count from 28 September cannot
   reserve order quantity.
2. Recheck the above model sensitivities against the finalized output-stage
   copper, cable/load parasitics and fault timing. Preserve the removable
   link function for rail-stuck emulation. The 50 mΩ source model is not
   a qualified contact, relay or fault-energy bound for the new board.
3. Route the remaining amplifier power, input/T and return networks, then
   extract both jack paths and measure output impedance, stability, THD+N,
   crosstalk and system ESD. The optional 33 Ω-at-100 MHz ferrite is a
   separate ESD design alternative, not part of this substitution.

The review BOM selects C4044221 so that the four output links can be
evaluated as a concrete assembly candidate. It is **not a fabrication
approval**; G-3/G-4, JLC DFM and the board-level qualification remain open.
