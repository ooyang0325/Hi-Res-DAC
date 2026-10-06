# DAC-HPA EMS verification — layout iteration 1 · 30 September 2026

**Verdict: layout-level EMS screen done for the routed areas; not yet certified.** The board is
USB-powered (no mains transformer) and has a continuous L2 GND plane, stitched GND
pours on L1/L3/L4, protected I/O and low-noise regulation.

- **Hum and USB ripple:** the models put magnetic hum ≥ 40 dB below the output noise
  floor at 1 µT (≥ 20 dB at 10 µT, close to a transformer), and USB ripple > 40 dB below.
- **USB ground loop (line-out into an earthed amplifier):** not modelled; test 5 covers it.
- **Wi-Fi, Bluetooth, DECT and GSM1800:** predicted far below the noise floor.
- **Main residual risk — VHF/UHF (30 MHz–1 GHz) on the headphone cable:**
  - as built, the model shows demodulated buzz above the noise floor at 3 V/m;
  - the no-new-footprint part of the fix is R417–R420 → ferrite bead;
  - the full fix also adds a 220 pF C0G per leg, which is a schematic ECO (Section 5);
  - with the ECO, 380 MHz–6 GHz drops ≥ 37 dB below noise, but 30–300 MHz keeps a
    modelled residual of up to +19 dB that must be measured.

This is a design and layout verification (circuit review, geometry screens and
LTspice/MATLAB review models), not an immunity test. Section 6 lists the tests
that decide it.

Board: [DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb).
Screens: [audit_ems_layout.py](audit_ems_layout.py) → [INTEGRATED_AUDIO_EMS_AUDIT.json](INTEGRATED_AUDIO_EMS_AUDIT.json),
[audit_return_path.py](audit_return_path.py). Simulations: [sim/README.md](sim/README.md).


> **Update 1 October — 6-layer stack.** The study board is now 6 layers:
> L1 sig / L2 GND / L3 PWR / L4 sig / L5 GND / L6 sig. L6 (B.Cu) and L4 now
> reference the solid L5 plane, so B.Cu track lacking a GND reference fell
> from 45 % to 11 % (`INTEGRATED_AUDIO_EMS_AUDIT.json`). Hum-loop heights
> shrink with the thinner dielectrics. The worst audio loop, LEG_LP at
> 108 mm², gives about 0.41 µV at 10 µT / 60 Hz, below the 1.56 µV output
> noise floor. The stack-up is assumed and must be confirmed with JLC; the
> USB pair must be re-dimensioned for 90 Ω on the thinner L1–L2 dielectric.

> **Update 6 October — routing closed, layout iteration 1 complete.** The board
> now has 0 ratsnest links and 0 DRC errors or warnings, with all 544
> footprints placed. The audit was re-run on the final copper
> (`INTEGRATED_AUDIO_EMS_AUDIT.json`).
>
> | Screen | 1 Oct | 6 Oct | Note |
> | --- | ---: | ---: | --- |
> | GND vias + PTH | 644 | 723 | MCU/CPLD and comparator areas stitched now that routing is closed (block 15) |
> | Worst pour point to a GND via (F.Cu / L3 / L4 / B.Cu) | 9.05 mm | 6.76 / 6.76 / 6.76 / 5.95 mm | Under λ/20 up to ≈ 2.2 GHz; the 5 mm grid was placed wherever via sites exist |
> | Largest board-edge fence gap | 47.5 mm | 13.7 mm | The 13.7 / 12.8 / 11.1 mm gaps are where edge passives (C651/C652/R946/R947 top, C509/R501/R502 bottom) sit on the fence line, plus a right-edge stretch near the jacks; all are < λ/20 at 1 GHz (15 mm) |
> | Worst audio hum loop | LEG_LP 108 mm² | LEG_LP 120 mm² | 0.45 µV at 10 µT / 60 Hz (−10.7 dB re the 1.56 µV floor); 45 nV at 1 µT (−30.7 dB) |
> | L2 plane fill | 89.5 % | 89.3 % | Still one continuous outline |
> | Left–right headphone copper | 0.392 mm | 0.392 mm | LEG_LP/LEG_RP on L3 at the J701 contacts (DRU jack-pitch exception); ≥ 2 mm elsewhere. Both are low-impedance amplifier outputs, so coupling is negligible at audio frequencies |
>
> - **Hum loops.** The LEG_LP/LN growth comes from plain-net vias
>   punching L2 antipads beside the legs (7.8 mm of LEG_LP lacks L2
>   directly beneath). This still leaves > 10 dB margin at a transformer-close
>   10 µT field.
> - **Digital routes.** The routes added since 1 October are slow control
>   lines: the CPLD/MCU link bus, CPLD_IRQ (ECO F09), the JTAG pins and
>   enables. They stay inside the digital area, and none crosses the DAC
>   core, I/V or output stages (`check_dac_core_routes` passes).
> - **Unchanged.** The residual VHF/UHF finding and its ECO (Section 5) are
>   unchanged. So is the N6_MCK_RC 80 MHz monitor node, 0.49–0.58 mm from
>   N6_CML / N6_V3R_B on facing layers; review it in the next ECO.
>
> **Verdict.** For a home environment (1–3 V/m RF, ≤ 10 µT hum, USB supply), the
> layout screen finds no new coupling path. Hum, ripple, Wi-Fi/BT/cellular and
> ESD stay inside the margins of Sections 2–4. The VHF/UHF cable-borne residual
> still needs the Section 5 ECO and the Section 6 measurements before
> immunity can be claimed.

> **Update 7 October — SI/EMI/hum layout review.** See
> [LAYOUT_REVIEW_SI_EMI_AUDIO_2026-10-07.md](LAYOUT_REVIEW_SI_EMI_AUDIO_2026-10-07.md).
> A six-layer ground solve puts USB/MCU/DAC ground currents ≥ 17 dB below the noise floor at
> both jacks. Block 16 moved U504's input/output capacitors to ≤ 2 mm and added in-pad vias
> to U501. LTspice/MATLAB sign-off
> ([SIGNOFF_SIMULATION_2026-10-07.md](SIGNOFF_SIMULATION_2026-10-07.md)) led to
> **ECO F10**, a ground-sense reference at the J702 sleeve. All hum, whine, stability and
> signal-integrity criteria now pass, with a smallest audibility margin of 17.6 dB. The 60 Hz loop
> figures in this report (trace length × height) understate the resistive plane return;
> use the sign-off values.

## 1. Home threat model

| Threat | Level assumed | Coupling path on this board |
| --- | --- | --- |
| Wi-Fi 2.4/5 GHz, Bluetooth, DECT 1.9 GHz | 1–3 V/m at 1 m from a router/phone | Headphone and USB cables (antennas); board traces are short vs λ |
| Cellular 0.7–2.7 GHz incl. 217 Hz TDMA/TDD bursts | 3 V/m (IEC 61000-4-3 residential), ~10 V/m for a phone ≈1 m away | Cable common mode → output stage → demodulation ("GSM buzz") |
| VHF/UHF broadcast, TETRA, 433 MHz ISM remotes | 1–3 V/m | Same; the 1.2 m headphone cable is near-resonant at 60–250 MHz |
| 50/60 Hz magnetic field (chargers, transformers) | 1 µT typical, 10 µT close to a transformer | Loop area of audio nets over their return plane |
| USB host/charger ripple and ground noise | 50 mV p-p at 100/120 Hz (poor charger) | VBUS → regulators → op-amp/reference PSRR |
| Ground loop via USB (line-out use into an earthed amplifier) | mA-level 50/60 Hz loop current | Shared GND between USB receptacle and jack sleeve |
| User ESD at jacks/USB | IEC 61000-4-2 ±4 kV contact / ±8 kV air | TVS diodes to L2 GND |

## 2. Layout screen results ([INTEGRATED_AUDIO_EMS_AUDIT.json](INTEGRATED_AUDIO_EMS_AUDIT.json))

| Item | Result | Assessment |
| --- | --- | --- |
| L2 GND plane | 1 continuous filled outline, 90.6 % of the board area | Solid reference under all L1 routing; no splits |
| Outer and L3 GND pours | GND pours on F.Cu, L3 and B.Cu, 0.3 mm clearance, refilled with the `.kicad_dru` rules (high-Z 0.5 mm, USB 0.6 mm) | Shields L1/L4 traces and gives short return vias |
| GND stitching | 645 GND vias and plated holes; 375 stitching vias on a 4 mm grid plus a 2.5 mm edge fence | Worst pour point to via 9.0 mm and one 47.5 mm edge-fence gap, both in the MCU/CPLD and protection-comparator areas that are **stitched after their routing closes** |
| Return path | 428 mm of 3 407 mm F.Cu track (12.6 %) lacks L2 copper directly beneath; see note | Gaps sit at via antipads and the board-edge pull-back; the DAC inputs, MCLK and I²S keep continuous L2 (gated by `check_iv_macro` / `check_dac_core_routes`) |
| Hum loops (60 Hz) | Largest audio-net loops: LEG_RP 41 mm², LEG_RN 36 mm², LEG_LN 27 mm², I/V rails ≤ 22 mm² | ≤ 15 nV at 1 µT and ≤ 0.15 µV at 10 µT, against a 1.56 µV output noise floor |
| Headphone L/R | Minimum left–right copper gap 2.03 mm | Meets the 2 mm DRU rule |
| Jack sleeve returns | J701.1, J702.1 and J702.2 each have five 0.6/0.2 mm GND vias on 0.5 mm F.Cu straps | J701.1's vias sit 1.9–3.4 mm away, because the DRU forbids vias inside the J701 courtyard |
| VREF | R446/R447/TP709 moved to the divider; the reference no longer crosses the digital area | Removes a 0.45 mm LINK_SCK adjacency and a 30 mm antenna stub |
| Clock / USB separation | MCLK↔DAC inputs ≥ 1.6 mm (≥ 2 mm outside U301, gated); I²S L1-only at 0.15 mm | Residual: an existing DAC-core VREF stub is 1.14 mm from MCLK, and the 80 MHz monitor RC node N6_MCK_RC is 0.58 mm from N6_V3R_B (neither is in a DRU rule). Review in the next ECO. |

Return-path note: B.Cu tracks are referenced to L3. There, the GND pour shares the layer
with the ± rail pair and power spurs, so 45 % of B.Cu length lies over L3 power copper
rather than L3 GND. L2 still sits one core (1.07 mm) away. The L4 audio nets (LEG_*,
I/V feeds) are slow, low-impedance nodes; their loops are counted in the hum row above.

## 3. I/O protection

| Port | Protection | Layout |
| --- | --- | --- |
| USB-C J101 | USBLC6-2SC6 flow-through on D+/D−; TPS25200 eFuse on VBUS; CC ESD; shield via R107 0 Ω (C101 4.7 nF option) | Pair on L1 at 0.235/0.15 mm over continuous L2, no vias |
| J701 / J702 jacks | LESD5D5.0 TVS on each tip/ring (D701–D704, D707, D708), 12 pF | TVS within the 4.2 mm local-path screen (`audit_local_tvs_paths.py`); returns to L2 through the sleeve vias above |


## 4. Circuit-level immunity (schematic review + simulation)

**Supply chain.** VBUS → TPS25200 eFuse → 5V_SYS → TPS259621 → 5V_ANA → FB501
(BLM18PG121SN1D) + 10 µF → LM27762 (2 MHz charge pump + low-noise ±LDOs) →
VPOS/VNEG. 3V3A comes from an LP5907 behind FB302; the DAC 1V3 from a TLV758; the
MCU and CPLD have their own LDOs.

**Filter resonance.** LTspice ([ems_5vana_filter.cir](sim/ems_5vana_filter.cir))
shows the FB501/10 µF resonance, with the MLCCs derated to 40 %:

| | Without R531/C513 | With R531/C513 at FB501.2 |
| --- | ---: | ---: |
| Line-transfer peak | +5.4 dB | +1.8 dB |
| U501 input-impedance peak | 1.25 Ω | 0.74 Ω |

The damper was moved from 20 mm away to the FB501.2 node in this iteration. The
filter keeps the LM27762 2 MHz ripple 52–60 dB down on 5V_ANA.

**Mains-frequency ripple.** MATLAB [ems_budget.m](sim/ems_budget.m) uses datasheet
PSRR curves:

| Datasheet curve | At 100 Hz |
| --- | ---: |
| LM27762 OUT+ | ≈65 dB |
| LM27762 OUT− | ≈52 dB |
| LP5907 | 90 dB |
| OPA1622 (RTI) | 140 dB |

For 50 mV p-p of 100 Hz on VBUS, the results at the headphone output are:

- **via the ± rails:** 0.025 nV;
- **via 3V3A → VREF (common mode, 1 % resistor match):** 7.9 nV.

Both are more than 40 dB below the 1.56 µV output noise, so USB ripple is not a hum
path.

**RF filtering already in the signal path.**

| Stage | Filter |
| --- | --- |
| I/V stage | 698 Ω ∥ 820 pF feedback (278 kHz pole); the DAC current output node is an RF short (820 pF ≈ 0.2 Ω at 900 MHz) |
| Difference stage | 680 Ω + 10 pF input RCs (23 MHz) and 2 kΩ ∥ 10 pF feedback |
| Protection comparators | 1 MΩ/3.3 nF, 910 kΩ/100 nF and 330 kΩ/1 nF RC inputs (48 Hz, 1.7 Hz, 482 Hz poles) |

The OPA2210 EMIRR is ≈36–47 dB up to 1 GHz and ≥70 dB above 1.8 GHz (datasheet
Fig. 6-39).

**Headphone output (the weak point).** The OPA1622 output reaches the jack through a
0 Ω link (R417–R420), the photo-relay and a 12 pF TVS. Its open-loop Z<sub>O</sub>
rises inductively above 1 MHz (5.5 Ω → ≈40 Ω at 100 MHz, datasheet Fig. 40), so
cable RF is barely absorbed by the amplifier. The feedback 10 pF then couples it
into the inverting input.

LTspice ([ems_headphone_rf.cir](sim/ems_headphone_rf.cir)) finds an LC resonance near
350–450 MHz with ≈0 dB coupling. MATLAB turns this into a 217 Hz buzz estimate:
OPA2210 EMIRR used as a proxy (the OPA1622 publishes none), square law,
−20 dB cable CM→DM conversion. Values are relative to the 1.56 µV output noise:

| Band | As built, 3 V/m | As built, 10 V/m | ECO, 3 V/m | ECO, 10 V/m |
| --- | ---: | ---: | ---: | ---: |
| VHF 30-80 MHz | +53 dB | +74 dB | +18 dB | +39 dB |
| FM broadcast | +60 dB | +81 dB | +0 dB | +21 dB |
| VHF 150-300 MHz | +47 dB | +68 dB | +19 dB | +40 dB |
| TETRA/433 ISM/DVB-T | +50 dB | +71 dB | -37 dB | -16 dB |
| LTE800/GSM900 | -9 dB | +12 dB | -104 dB | -83 dB |
| GSM1800/DECT | -124 dB | -103 dB | -215 dB | -194 dB |
| Wi-Fi 2.4 | -134 dB | -113 dB | -224 dB | -203 dB |
| Wi-Fi 5 | -133 dB | -112 dB | -248 dB | -227 dB |

## 5. Recommended ECO (owner decision)

1. **R417–R420: 0 Ω → 0402 ferrite bead**, 120 Ω @ 100 MHz, DCR ≤ 0.1 Ω, ≥ 1 A.
   - Same footprints; no layout change needed for this part.
   - The bead sits outside the OPA1622 feedback loop, adding about 0.05 Ω of output
     resistance (damping factor > 300 into 16 Ω).
2. **Add 220 pF C0G 0402 from each LEG_* net to GND**, beside R417–R420 on the relay
   side.
   - Four new parts, so this needs a schematic ECO and a BOM update.
   - [review_output_rf_filter.py](review_output_rf_filter.py) uses the unchanged
     calibrated OPA1622 model from Calculation Package v1.1
     ([results](OUTPUT_RF_FILTER_STABILITY_REVIEW.json)):
     - worst phase margin 47.1° (49.7° today);
     - worst gain margin 6.46 dB (7.86 dB today).
   - Larger values were rejected:
     - 600 Ω bead + 1 nF: phase margin 7°;
     - 120 Ω + 470 pF: gain margin 5.8 dB.
3. With 1 + 2, the model puts 380 MHz–6 GHz buzz ≥ 37 dB below the noise floor at
   3 V/m.
   - 30–300 MHz improves by 28–60 dB, but a modelled residual of up to +19 dB above noise
     remains at 3 V/m.
   - The model is uncertain there (cable CM→DM conversion, EMIRR proxy), so measure
     before adding more filtering.

## 6. Tests that decide immunity

1. IEC 61000-4-3, 80 MHz–6 GHz at 3 V/m, 1 kHz 80 % AM (EN 55035 residential).
   - Record A-weighted output noise and 1 kHz / 217 Hz spurs with a 32 Ω load and
     1.2 m cable, each jack.
2. IEC 61000-4-6 conducted, 150 kHz–80 MHz at 3 V EMF.
   - Inject on the USB cable and the headphone cable.
3. GSM/LTE phone test: calling phone at 10 cm and 1 m; 217 Hz and 1.73 kHz spurs.
4. Magnetic 50/60 Hz: a 10 µT Helmholtz field, or a laptop charger at 5 cm; output
   spectrum.
5. USB ground loop: line-out into an earthed amplifier through a PC; measure hum,
   with and without the C101/R107 shield option.
6. IEC 61000-4-2 ESD at J701/J702 sleeve/tip and USB shield.
   - Check there is no latch-up and that the relay/protection recovers.
7. Near-field scan of the LM27762 (2 MHz) and the CPLD/MCU clocks.
   - Confirm clock harmonics are not visible in the audio-band noise.
