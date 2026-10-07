# DAC-HPA layout sign-off simulation (LTspice + MATLAB) · 7 October 2026

Board: [DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb)
with ECO F10.

Tools: LTspice 26.0.2 and MATLAB R2025a, with TI vendor models:

| Part | TI model | Use |
| --- | --- | --- |
| OPA1622 | SBOM958D | Stability, CMRR |
| TLV767 | SLVMCY1 (TLV76701 unencrypted) | U504 transient |
| LM27762 | SNVMAV1 | See note under row 5 |

Scripts, decks and results: [sim/signoff/](sim/signoff/README.md). The independent review of this
sign-off and the changes it led to are in [SIGNOFF_REVIEW_RESPONSE_2026-10-07.md](SIGNOFF_REVIEW_RESPONSE_2026-10-07.md).

**Verdict: PASS on every criterion below.**

The one REVIEW item found during sign-off was a shared-ground whine path on the 3.5 mm
output. It was closed by **ECO F10** (owner-approved): a ground-sense reference at the
J702 sleeve. Physical measurements (Section 3) remain the final gate for the assumptions
listed in Section 2.

## 1. Results

| # | Check | Tool | Criterion | Result | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Hum and whine at the headphone output (Section 1a) | MATLAB | Every term ≥ 6 dB below audibility on a 135 dB SPL/V IEM | Smallest margin **16.2 dB** after F10, including the I/V-output pair loops (was **1.0 dB**) | PASS |
| 2 | OPA1622 output-stage stability (Section 1b) | LTspice | PM ≥ 45°, GM ≥ 6 dB, all cases | Min PM **57.1°**, min GM **13.9 dB** | PASS |
| 3 | Difference-stage CMRR (F10) | LTspice | Rejects ground differences ≥ 40 dB | Worst tolerance corner **−56.4 dB** at 60 Hz–1 kHz, −54.9 dB at 8 kHz, −50.5 dB at 20 kHz | PASS |
| 4 | U504 TLV767 placement (block 16) | MATLAB extraction + LTspice | Schematic rule ≤ 3 mm; datasheet COUT 1–220 µF, ESR 2–500 mΩ | See Section 1c | PASS |
| 5 | U501 LM27762 ground pad (block 16) | LTspice | Lower 2 MHz ground bounce | **87 → 29 mV p-p** at the IC pad; 5V_ANA (before FB501) 0.55 mV p-p | PASS |
| 6 | MCLK 80 MHz and BCLK signal integrity | LTspice | No overshoot past the rails, monotonic edges; X201 load ≤ 14.23 pF | See Section 1d (Z0 51.5 Ω field-solved) | PASS |
| 7 | USB HS pair on the declared JLC06161H-3313 stackup | MATLAB 2-D field solver (`tline_fd.m`) | 90 Ω ±15 % at every build corner; intra-pair skew ≤ 100 ps | Coupled 0.17/0.18 mm and split 0.20 mm sections 88.7–90.0 Ω nominal, 81.2–98.6 Ω at the corners; 2.15 mm = 12 ps ([signoff_impedance.txt](sim/signoff/signoff_impedance.txt)) | PASS |
| 8 | Ground-solver validation | MATLAB | Convergence and reciprocity | 0.3 vs 0.2 mm grid within 4 %; matches the independent Python solver; reciprocity and synthetic-sheet unit tests pass | PASS |

**Note on row 5.** TI's switching model needs about 19,000 time points per 2 MHz cycle
in LTspice and could not reach steady state. Row 5 therefore uses a reduced-order switching-current
model (datasheet operating point, 10 ns edges) on the extracted capacitor and ground parasitics.

### 1a. Hum and whine ([signoff_hum_budget.txt](sim/signoff/signoff_hum_budget.txt), before F10: [signoff_hum_budget_pre_f10.txt](sim/signoff/signoff_hum_budget_pre_f10.txt))

**Method**

- The six-layer GND copper is solved as a resistive grid with all 724 GND vias and plated
  holes.
- Transfer resistances run from each current source to the output reference minus the
  jack sleeve.
- The 50/60 Hz magnetic pickup uses the vector potential along the extracted series audio
  route. The loop closes either through the resistive plane return (by reciprocity) or,
  after F10, through the extracted N4_GSENSE route.
- Audibility limit: the higher of two thresholds:
  - ISO 226 threshold in quiet;
  - masking by the amplifier's own noise in one ERB (15.7 nV/√Hz per leg, calc package v1.1).

| Term (worst case) | Before F10 | After F10 |
| --- | ---: | ---: |
| USB frame-rate MCU/CPLD current (20 mA p-p), 3.5 mm | 0.205 µV, margin **1.2 dB** | 0.6 nV, margin 51.5 dB |
| DAC digital current (10 mA p-p), 3.5 mm | 0.208 µV, margin **1.0 dB** | 4.9 nV, margin 33.6 dB |
| Same, 4.4 mm balanced | margin 12.8–15.9 dB | margin 27.6–45.5 dB |
| 60 Hz field 10 µT, 3.5 mm (worst channel) | 2.09 µV (R), margin 17.5 dB | 2.06 µV (L), margin 17.6 dB |
| 60 Hz field 10 µT, 4.4 mm balanced | margin ≥ 29.2 dB | margin ≥ 25.2 dB |
| USB 100/120 Hz ripple | margin 50 dB | margin 50 dB |

The magnetic loop moved from R to L, at the same size (≈ 550 mm²). The 3.5 mm loop is
now the output route plus the sense route.

**I/V outputs to the difference stage** (added after the independent review, G31). A 60 Hz EMF
between the P and N routes of an OPA2210 output pair is a differential input of the difference
stage, so it reaches the output × 2.0 k/1.3 k = 1.54. The differential loops are LP 63.5, LN 88.6,
RP 133.8 and RN 61.1 mm². Added in magnitude to the output loops (worst case), the 10 µT terms
are 2.43 µV (3.5 mm L, margin 16.2 dB) and 1.99 µV (4.4 mm R, 17.9 dB).

**Why the 60 Hz loop is not "trace length × height".** At 60 Hz the return current spreads
through the plane resistively. Near the board edge its centroid bows up to ~12 mm from
the trace, so the effective loop is the area between the route and that resistive centroid.
The solver's unit test reproduces this bow on a uniform sheet.

### 1b. OPA1622 stability ([signoff_hp_stability.txt](sim/signoff/signoff_hp_stability.txt))

**Setup**

- TI model, broken at IN− (Middlebrook injection).
- Extracted per-leg parasitics:
  - N4_LP_OUT: 19 pF;
  - LEG_LP: 37 pF, including the protection taps;
  - JACK_LP: 24.5 pF;
  - plus 12 pF TVS, TLP3545A RON 0.081 Ω, and COFF 1 nF when off.
- Load cases: relay off; unplugged; 16, 32 and 300 Ω with 1.2–3 m cable; 300 Ω with 2 nF.
- Variants: as built, with the EMS ferrite + 220 pF ECO, and with the F10 sense return
  (40 nH, 0.3 Ω).

**Results**

- Crossover 2.0–2.6 MHz.
- Phase margin 57–72°.
- Gain margin ≥ 13.9 dB.
- F10 changes no margin.

### 1c. U504 regulator capacitors ([signoff_ldo_paths.txt](sim/signoff/signoff_ldo_paths.txt), [lt/ldo_u504.log](sim/signoff/lt/ldo_u504.log))

| Path | Old | New |
| --- | --- | --- |
| OUT → C512 | 27.3 mm, 4.65 nH, 24.6 mΩ (on a stub) | 1.9 mm, 0.77 nH, 3.3 mΩ |
| IN → C501 | 14.4 mm, 2.34 nH | 2.1 mm, 0.35 nH |

**LTspice, 40 → 160 mA load step**

| Quantity | Old | New |
| --- | ---: | ---: |
| Undershoot | 16.0 mV | 16.3 mV |
| Overshoot | 15.7 mV | 16.2 mV |
| Output-impedance peak | 0.22 Ω at 13 MHz | 0.25 Ω at 24 MHz |

- **Effect of the move.** The old wide B.Cu trunk was already low-inductance. The move
  satisfies the schematic ≤ 3 mm rule and TI layout guidance; it is not a measurable
  transient fix.
- **Model limitation.** TI's TLV767 model is behavioral (fixed output R + 20 kHz pole). It
  does not model loop stability against COUT. Stability therefore rests on the datasheet
  ranges: C512 is 10 µF X5R (≈ 6 µF effective at 3.3 V) with ≈ 5 mΩ ESR, inside
  1–220 µF and 2–500 mΩ.

### 1d. Clock signal integrity ([lt/clk_si.log](sim/signoff/lt/clk_si.log))

**Setup**

- Extracted L1 microstrip, Z0 58 Ω.
- Electrical lengths: MCLK 43 ps, X201 → R203 20 ps, BCLK 99 ps.
- Drivers at 0.3, 0.5 and 1 ns edges.
- 33 Ω source resistors.

**Results**

- XI peaks at 3.29 V and BCLK at 3.30 V, with no dip below 0 V.
- Edges are monotonic. Rise time is 1.0–1.3 ns at XI and 0.8–1.1 ns at BCLK.
- X201 load ≈ 8.7 pF against the 14.23 pF rule.

## 2. Assumptions that measurements must confirm

1. **Digital ground current.** USB frame-rate modulation is taken as 20 mA p-p
   (MCU + CPLD) and 10 mA p-p (DAC). Both values are pessimistic and unmeasured. After F10
   the margin is ≥ 27 dB even if they are 20× larger.
2. **Magnetic field.** 10 µT at 60 Hz is the close-to-a-transformer case; 1 µT is
   typical, and gives margins ≥ 37 dB.
3. **Stack-up and copper.** Declared on the board since the review response: JLC06161H-3313,
   0.0994 / 0.55 / 0.1088 mm, εr 4.1 / 4.6 / 4.16, 1 oz outer, 0.5 oz inner, 15 µm mask. The
   hum and parasitic models use εr 4.3, which moves Z0 by about 2 %.
4. **Component data.**
   - TLP3545A COFF ≤ 1 nF.
   - ES9018K2M input capacitance 5 pF (not published).
   - OPA1622 noise 15.7 nV/√Hz per leg (calc package).
5. **Vendor model limits.**
   - LM27762: switching taken from the datasheet operating point.
   - TLV767: behavioral output stage.

## 3. Bring-up measurements that close the sign-off

1. Output FFT on the 3.5 mm and 4.4 mm jacks, with 16 Ω and an IEM, while streaming USB
   HS audio. Look for 1 kHz and 8 kHz spurs; the target is below the noise floor.
2. 10 µT, 60 Hz Helmholtz field (or a laptop brick at 5 cm). The predicted worst case is
   2.1 µV at 60 Hz.
3. Small-signal step response at LEG_xx and JACK_xx with 0 and 1 nF loads, with the relay open and closed.
4. U501 2 MHz ripple at VPOS/VNEG and at the U501 pad, and U504 load-step undershoot.
5. The EMS report §6 immunity tests.
