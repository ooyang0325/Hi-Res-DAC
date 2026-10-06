# I/V package and 7 mm input route recheck — 27 September 2026

U403/U404 now capture the owner-approved **TI OPA2210IDGKR**, JLCPCB part **C2876414**, on a VSSOP-8 DGK land. This is a package change from the v0.9 Parts List's OPA2210IDR SOIC-8; the electrical netlist and pin numbers remain unchanged. [TI's OPA2210 datasheet](https://www.ti.com/lit/ds/symlink/opa2210.pdf), Figure 5-3 and Table 5-2, assign the same pins to the D and DGK versions. [JLCPCB lists the DGK part](https://jlcpcb.com/partdetail/TexasInstruments-OPA2210IDGKR/C2876414) for SMT assembly as an Extended part. JLC sourcing for the five-board quantity plus attrition is not reserved.

The KiCad footprint reuses `JLC_Imported:VSSOP-8_L3.0-W3.0-P0.65-LS5.0-BL`, already present for TI's DGK-package C140314. Its eight numbered lands were checked against the TI pin table. This is package-equivalent reuse, not a claim that the exact C2876414 EasyEDA footprint was imported. The JLC land is approximately 1.662 × 0.364 mm with pad centres ±2.131 mm; TI's DGK example land is 1.4 × 0.45 mm with a 4.4 mm row spacing. The G-3 overlay and JLC DFM review must settle the final land.

TI gives OPA2210 junction-to-ambient thermal resistance of 126.1 °C/W in D (SOIC) and 132.7 °C/W in DGK (VSSOP). The 6.6 °C/W difference adds about 0.33 °C at 50 mW/package; the actual package dissipation and copper heat spreading still need a layout thermal check.

## Trace capacitance and the supplied stability model

Notes v1.0 §9.1 states 64.5 Ω and 6.0–6.2 ps/mm for a 0.20 mm masked L1 trace over L2. Using `C′ = delay / Z0` gives **0.093–0.096 pF/mm**, about **0.65–0.67 pF for 7 mm**. Increasing the limit from 5 to 7 mm adds about **0.19 pF** of trace capacitance, before pads, package and coupling effects.

The v1.1 calculation package's `analog/scripts/stability_iv.py` already sweeps 2/5 pF of stray capacitance at the DAC/I/V input. I reran its selected R8 CM-summing-load case over the same 1,080 model corners while increasing the upper stray bound. The supplied ZIP was read without changing it (SHA-256 `90046c84a8e102a656e6f47af1f0189a24b30f57547e72c25e81f688355c2b6d`).

| Input stray sweep | Lowest phase margin | Lowest gain margin across all corners |
| --- | ---: | ---: |
| 2–5 pF, supplied envelope | 67.54° | 4.46 dB |
| 2–6 pF, provisional 7 mm envelope | 67.44° | 4.43 dB |
| 2–8 pF, sensitivity | 67.25° | 4.38 dB |
| 2–10 pF, sensitivity | 67.06° | 4.34 dB |

The package's published 5.6 dB gain margin is the gain margin **at the corner with the lowest phase margin**, not the minimum gain margin over all 1,080 corners. At 5 pF the true global minimum in this model is 4.46 dB, at another model corner; this distinction predates the proposed route-length change. The model remains an engineering estimate of OPA2210 output impedance and DAC pin capacitance, not a measured stability result.

## Placement result and conditional rule

On either current outline, the JLC DGK land gives DAC-to-I/V direct pad distances **4.81 / 4.72 / 3.13 / 3.95 mm** for DACL / DACLB / DACR / DACRB. An individual L1 grid route probe with 0.20 mm trace and 0.1 mm cells estimated **6.37 / 5.73 / 4.01 / 4.81 mm**. The probe routes nets separately and approximates pad shapes by bounding rectangles; it does not establish that the four traces, guards, feedback loops and VREF can coexist. The former 5 mm rule is not attainable with this placement; **7 mm is a provisional candidate** supported by the model sensitivity check, subject to the actual routed-length report, extracted input capacitance within the 6 pF test envelope, and I/V step-response/ringing measurement at bring-up.

The existing v1.1 DOCX/XLSX documents still specify the SOIC part and 5 mm rule. The capture generator asserts that old workbook signature and applies the owner-approved override so this discrepancy is explicit. A revised document set should incorporate the DGK MPN, C2876414, and the final routed rule before manufacturing freeze.
