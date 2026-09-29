# Discharge capture and calculation review · 29 September 2026

**Release state: HOLD.** This is a source-to-model discrepancy report for the
current review-only schematic and PCB. It does not change the owner-supplied
Parts List, Spec, Notes or calculation ZIP. Use the machine-readable
[capture audit](DISCHARGE_CAPTURE_AUDIT.json) to see the exact fitted parts and
capacitor inventory read from the v0.9 workbook.

## Captured circuit versus the calculation package

| Item | Captured source / latest design intent | Calculation package v1.1 |
| --- | --- | --- |
| U504 EN pin 4 | `AUD_EN` | `AUD_EN` |
| U303 EN pin 3 | `3V3D`, tied to its IN | `c06_discharge.py` and `c12_u303_tlv758p.py` assume `AUD_EN` |
| 1V3 discharge | R530/Q506 can load U303 while 3V3D is falling | C06 assumes U303 is already disabled, then quotes 1V3 <0.1 V by 0.134 ms |
| Current prose | [Spec v1.1](../doc/DAC_HPA_Design_Spec_v1.1.docx) §3.2 deliberately ties EN to 3V3D to protect DVDD/DVCC rail order, yet still prints the 0.134 ms result. [Notes v1.0](../doc/DAC_HPA_Schematic_Design_Notes_v1.0.docx) describes an approximately 0.76 ms 1V3 sequence. | `verify_release.py` reproduces the shipped C06 output but does not compare its EN assumption with the captured netlist. |

The EN tie was an intentional later design correction for 3V3D fault and
hard-unplug ordering. Keep the present U303 pin map while rebuilding the
discharge evidence. Connecting EN back to `AUD_EN` would reopen the DAC supply
order fault that the latest Spec says was closed.

## Source-derived inventory and first power screen

The workbook connects **11.81 µF nominal directly to 3V3D**, **1.30 µF** on
the FB202 CPLD branch and **2.30 µF** on the FB301 DVCC branch, including
C439's 2.2 µF. The total is **15.41 µF nominal** or **16.951 µF** if each is
10% high. The package's C06 high-capacitance expression evaluates to
**15.09 µF including its 1 µF reserve**, and does not enumerate all the
captured capacitors. Voltage bias, supplier tolerance and bead dynamics still
need a qualified model.

For illustration only, if U504 is already off and the rail acts as one
16.951 µF capacitor discharged through 10.1 Ω plus 55.2 mΩ FET resistance,
an assumed 89 µs gate delay gives **0.693 ms** to 0.1 V from 3.333 V. Adding
a separate 1 µF reserve gives **0.728 ms**. These are **not guaranteed shutdown
times**: they exclude U303 sourcing current into R530, regulator turn-off
delay, reverse current, load variation and rail separation by the beads.

| Fitted resistor | Initial electrical screen | Why it remains open |
| --- | ---: | --- |
| R527, 10 Ω 0603, 0.1 W | 1.145 W at 3.366 V and −1% R | Pulse rating for this exact part and regulator overlap need verification. |
| R529, 10 Ω 0603, 0.1 W | 1.122 W at 3.333 V and −1% R | The summed 3V3D capacitor energy alone is 94.2 µJ at +10% C, before any LDO drive; the workbook's 0.1 mJ pulse annotation lacks an identified manufacturer pulse limit. |
| R530, 4.7 Ω 0603, 0.1 W | 0.400 W at 1.365 V and −1% R | U303 can regulate into this load while its 3V3D input remains high enough. |

The power figures are *instantaneous* (V^2/R), not proof of damage or a
qualified pulse rating. The capacitor energy is not an upper bound on the
energy in R529 if a regulator continues to supply the rail.

## Physical ECO study and next evidence

A manual temporary fit trial placed a **2512 R529** at (44.4, 125.5), 90° and
a **1210 R530** at (57.5, 136.0), 180°, moving R531 to (49.0, 127.5) and
TP738 to (45.5, 130.5). It showed zero KiCad placement DRC violations and
nearest body gaps of 1.04/1.20 mm respectively. Their discharge-current
tracks, copper heat spreading, package-specific JLC assembly access and
thermal behavior were **not** verified. R527 has no large-footprint fit trial.

A candidate 10 Ω 2512 part is [YAGEO RC2512FK-7W10RL](https://yageogroup.com/component-documentation/download/specsheet/RC2512FK-7W10RL),
whose manufacturer sheet rates it 2 W at 70 °C. A candidate 4.7 Ω 1210 part
is [KOA SG73P2E1RTTD4R7J](https://jlcpcb.com/partdetail/KOA_SpeerElec-SG73P2E1RTTD4R7J/C5894132),
listed by JLCPCB as 1 W, ±5%; its tolerance changes the low-resistance power
corner and its order availability must be rechecked. These are **fit-study
candidates**, not approved BOM substitutions.

Before replacing the 0603 parts or claiming discharge timing:

1. Rebuild C06/C12 from the captured U303 EN=3V3D topology and complete
   3V3D/1V3 capacitor inventory. Include U504 turn-off and U303 output/load
   behavior, MOSFET gate timing, fault cases and bead branches.
2. Resolve the Spec's 0.134 ms statement against the later Notes' approximate
   0.76 ms sequence. Keep the ≥1 ms firmware re-enable interval unless a new
   worst-case bound and DAC rail-order analysis justify a change.
3. Select pulse/steady-rated R527/R529/R530 parts with current JLC assembly
   availability, then fit, route and thermally check their actual footprints.
4. Scope 3V3D, DVCC, 1V3, `AUD_EN`, Q505/Q506 gates and 5V_SYS current during
   reset, suspend, unplug, brown-out and a 3V3D fault. Measure resistor and
   U303/U504 temperatures through repeated cycling. Do not label a C06 rerun
   or a zero-DRC partial board as electrical qualification.

The [TI TLV758P datasheet](https://www.ti.com/lit/ds/symlink/tlv758p.pdf)
specifies its enable and output-discharge behavior; its 95 Ω internal
pulldown figure is typical, so the captured R530/Q506 path remains relevant.
