# Layout review — signal integrity, EMI and audio (hum) · 7 October 2026

Board: [DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb)
after layout iteration 1 (0 ratsnest links, 0 DRC).

**Verdict.** For headphone use, the routed copper has no hum or whine path above the
1.56 µV output noise floor. No fast clock, I²S, USB or charge-pump node couples into
the DAC outputs, the I/V stage, the difference stage or VREF.

The review found two placement defects and fixed both in block 16:

- **U504 capacitors.** The input and output capacitors of the 3.3 V LDO (U504) were
  13.5 mm and 20 mm from the regulator. The schematic rule is ≤ 3 mm.
- **U501 ground pad.** The LM27762 charge pump's exposed ground pad had no via
  within 3 mm.

One placement weakness is left for iteration 2: decoupling at three MCU supply pins
(Section 5).

Method: geometry screens on the saved board, plus a resistive solve of the ground copper
on all six layers ([sim/gnd_transfer.py](sim/gnd_transfer.py),
[sim/coupling_screen.py](sim/coupling_screen.py); dump with
[sim/board_dump.py](sim/board_dump.py)).

**Assumptions**

- Copper: 1 oz outer, 0.5 oz inner.
- Stack: JLC 6-layer, with L1–L2 = 0.099 mm, L3–L4 = 0.109 mm and 0.55 mm cores.
- The ground solve uses a 0.3 mm grid and is accurate to about ±30 %.

This is a design review, not a measurement. The tests in
[EMS_VERIFICATION_2026-09-30.md](EMS_VERIFICATION_2026-09-30.md) §6 still decide immunity.

## 1. Hum and whine through shared ground

**Topology**

- **3.5 mm output (J702).** Each single-ended leg is referenced to its difference-stage
  ground resistor (R404 / R408 / R412 / R416, all near the DAC). The listener hears that
  reference minus the jack sleeve.
- **4.4 mm output (J701).** The balanced legs see only R404 − R408 (and R412 − R416).

For each current source, the table gives the **transfer resistance**: the voltage between
the left reference (R404) and the sleeve, per ampere flowing through the board ground.

| Current through GND | R404 − J702 sleeve | R404 − J701 sleeve | Realistic current | Result at the output |
| --- | ---: | ---: | --- | --- |
| MCU + CPLD supply → USB GND (J101) | 10.6 µΩ | 4.4 µΩ | 20 mA p-p USB frame-rate (1 kHz / 8 kHz) modulation | 0.21 µV, **−17 dB** re noise |
| DAC (U301) supply → J101 | 21.3 µΩ | 18.7 µΩ | 10 mA p-p | 0.21 µV, **−17 dB** |
| LM27762 input current → J101 | 24.6 µΩ | 10.4 µΩ | Rectified load current, 88 mA peak (1 Vrms into 16 Ω) | 2.2 µV, −116 dB re 1 Vrms (H2 floor) |
| 3.5 mm load return (J702 → U501) | 246 µΩ | — | 62 mA (1 Vrms, 16 Ω) | −96 dB (L→R crosstalk −97 dB) |
| Ground loop J101 → J702 sleeve | 271 µΩ | 97 µΩ | Only with line-out into an earthed amplifier, from an earthed PC | 10 mA loop → 2.7 µV (+4.8 dB) |

- **Hum and whine.** Digital and USB ground currents stay 17 dB or more below the noise
  floor. With headphones there is no second ground connection, so the ground-loop row
  does not apply.
- **Crosstalk.** The 3.5 mm load return is a linear crosstalk term, not hum. The jack
  contact and the shared cable sleeve (20–50 mΩ) set the real single-ended crosstalk
  near −55 dB. The board's share is 40 dB below that.
- **Line-out into an earthed amplifier.** The remaining hum path is the USB ground loop.
  The fixes are system-level:
  - use the balanced 4.4 mm output into a balanced input;
  - use a USB isolator;
  - or run the source on battery.
  The C101/R107 shield option does not break this loop: the USB GND wire carries it.

## 2. Magnetic (50/60 Hz) pickup

The earlier EMS screen reported LEG_LP at 120 mm² (0.45 µV at 10 µT, −10.7 dB). That
figure counts the whole LEG net. LEG_LP is 265 mm long because it also feeds the DC
and over-range protection dividers (R900–R933, R624–R627). Those 330 kΩ–1 MΩ taps
carry no headphone current. Their pickup appears only at the comparator inputs,
millivolts below the thresholds.

The audio loop is the series path only: OPA1622 → R417 → K601 → jack → sleeve →
GND. That path is about 40 mm of LEG/JACK copper, so −10.7 dB is a conservative bound.

## 3. Signal integrity

| Net group | Routing | Reference | Result |
| --- | --- | --- | --- |
| MCLK (X201 80 MHz → R203 → U301) | L1 only, 7.1 mm, no vias; X201 → XI 8.3 mm (rule ≤ 10), R665 → U607 1.6 mm (rule ≤ 3) | 100 % over solid L2 | Pass |
| BCLK / LRCLK / SDATA, oscillator outputs | L1 only, 1.7–16.6 mm, no vias, series source resistors | 100 % over L2 | Pass |
| USB HS D+/D− | L1 only, no vias; 0.16 mm / 0.225 mm gap; 2.2 mm intra-pair mismatch | Solid L2 at 0.099 mm | Zdiff ≈ 90 Ω (IPC-2141); skew ≈ 15 ps, below the ~100 ps guideline. Pass |
| LINK bus, I²C, JTAG/SWD, enables, LRCLK_FB | L1/L3/L4/L6 with vias | L3/L4 over the 0.55 mm cores; 3–15 mm void beneath on the facing L3/L4 layer | Slow control nets; acceptable. Keep any future fast net on L1/L6 |

**Stack-up note.** L3 and L4 are 0.109 mm apart and 0.55 mm from their planes, so L4
traces return partly on whatever L3 copper is above them. Only slow nets use these
layers. Do not route clocks or I²S on L3/L4 in later revisions.

## 4. Coupling into the audio path

[sim/coupling_screen.py](sim/coupling_screen.py) checks every toggling net (clocks, I²S,
USB, LINK, I²C, JTAG/SWD, LEDs, the charge-pump switch nodes) against every audio and
high-Z net. A pair is flagged when the edge gap is < 0.5 mm on the same layer, or < 0.3 mm
between L3 and L4 (broadside).

- **Audio path: none flagged.** The screen finds no coupling to DACL/DACLB/DACR/DACRB,
  the I/V nodes, the difference-stage inputs or VREF.
- **Pairs found (all benign):**

  | Victim | Aggressor | Coupling | Why it is harmless |
  | --- | --- | --- | --- |
  | AVCC_EN | LED_G | Broadside, 17.5 mm | Both static |
  | VPOS / VNEG / 1V3 | LED_R / LED_G | Broadside, ≤ 5 mm | Rails are decoupled |
  | DC_SENSE_LP | I²C / LINK | Broadside, ≤ 5 mm | Pre-filtered DC sense into the MCU ADC |
  | 3V3A | I2C_SDA | Same layer, 4.2 mm at 0.36 mm | ≈ 0.08 pF into a 2.2 µF node, nV level |

- **Firmware constraint.** Keep the LEDs static or PWM them above 20 kHz. Do not poll the
  DAC over I²C continuously during playback.

## 5. Placement: decoupling and ground pads

| Item | Before | After block 16 | Note |
| --- | --- | --- | --- |
| C501 (U504 TLV767 input) → IN pin | 13.5 mm | **1.8 mm** | Schematic rule ≤ 3 mm; 1 mm 5V_SYS link to the IN via |
| C512 (U504 output) → OUT pins | 20 mm via a 0.15 mm stub | **1.9 mm** | LDO stability and 3V3D (X201 MCLK supply) noise |
| U501 (LM27762) exposed GND pad → nearest via | 3.07 mm | **0.55 mm** (2 filled vias in the pad) | 2 MHz ground return and heat |
| ES9018K2M AVCC_L/R, VCCA, DVCC, 1V3 caps | 1.9–2.4 mm | — | OK |
| OPA1622 / OPA2210 rail caps | 2.2–4.6 mm | — | OK; OPA1622 thermal pads have in-pad vias |
| MCU (CH32V307) VDD pins 19 / 32 / 64 | 7.0 / 8.5 / 9.2 mm | unchanged | **Iteration 2**: no free 0402 site without reworking the dense LQFP fanout. Not an audio path (its ground current is −17 dB re noise, Section 1); it affects MCU EMI margin |
| U208 GND pin 4 → nearest via | 3.5 mm | unchanged | No legal via site; slow LINK buffer |

**How block 16 made room**

- Q504 (AUD_EN discharge FET, slow) moved to the free strip under U504, so C501 could
  take its place.
- N5_DIS_D now runs along that strip.
- The two vias that flank C512's pads are filled and capped, matching the other in-pad
  vias on the board.

**Checks after block 16:** DRC 0, unconnected 0, VALIDATE_OK (placement, DFA, JLC fab,
via-pad, power-escape, timer, TVS, trace-budget and DAC-core gates).

## 6. Owner actions (unchanged from the EMS report)

1. R417–R420 → 120 Ω ferrite and a 220 pF C0G per leg (VHF/UHF cable immunity, EMS §5).
2. Run the §6 measurements, including:
   - the 10 µT field test;
   - the line-out ground-loop test with and without C101/R107.
3. Iteration 2: add MCU decoupling at VDD pins 19/32/64 within 2 mm.
