# Response to the independent sign-off verdict · 7 October 2026

Review: branch `ooyang0325-sign-off-verdict` (commit 11b0932). The suite is merged into this
branch under [signoff/](signoff/README.md) and was re-run on the board after every change below.

Board: [DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb)

| Run | FAIL | WARN | PASS |
| --- | ---: | ---: | ---: |
| Reviewer's run (board before block 16 and ECO F10) | 5 | 10 | 4 |
| Same suite on that run's starting board here (after F10, before this work) | 5 | 11 | 3 |
| **After this work** ([report](signoff/out/SIGNOFF_REPORT.md)) | **0** | **10** | **9** |

The reviewer's verdict text quotes "6 FAIL, 11 WARN, 3 PASS"; its committed report shows 5 FAIL.
All five FAIL gates are now closed. Most of the change is to the board (Section 1). Some
findings came from suite inputs that did not match the design; those were corrected with
sources (Section 2), and each correction is visible in `git log -p hardware/signoff`.

## 1. Board changes

| Finding | Change | Result |
| --- | --- | --- |
| **No stackup** (G05, G20, Tier 1 #1) | The board now declares JLCPCB **JLC06161H-3313**: 1 oz outer / 0.5 oz inner copper; 3313 prepreg 0.0994 mm (εr 4.1), 0.55 mm cores (εr 4.6), 2116 prepreg 0.1088 mm (εr 4.16); LPI mask 15 µm; ENIG. Values from jlcpcb.com/impedance. The generator writes it from the manifest (`stackup`). | G05 PASS |
| **USB impedance** (G20) | Solved with a 2-D field solver on the declared stackup (Section 3). As routed (0.16 mm) the coupled run was 93.5 Ω and the looser one 97 Ω. The traces were widened on the same centrelines: coupled sections **0.17 mm** at 0.385 mm pitch, **0.18 mm** at 0.5 mm pitch, and the split runs around the USBLC6 **0.20 mm**. | 88.7–90.0 Ω nominal; 81.2–98.6 Ω across ±10 % prepreg, ±0.2 εr, ±5 µm copper. Target 90 Ω ±15 % |
| **J101 drill-to-copper** (G06, Tier 1 #2) | New library footprint `J101_USB4105-GF-A_12lands_4stakes_NPTH030`, now J101's footprint in the schematic, BOM and integrated board: the four 0.6 mm VBUS/GND lands end 0.17 mm short on the locating-hole side (1.15 → 0.98 mm). Their VBUS escapes restart at the new land centres. The frozen study boards keep the original footprint, which is unchanged in the library. | NPTH-to-copper 0.13/0.17 → **0.30/0.33 mm** (JLC NPTH 0.20 mm; board rule 0.28 mm). G-3 overlay must confirm tail coverage |
| **USB 3W** (G20, Tier 1 #3) | The VBUS via beside D− moved 0.3 mm west. | 0.28 → 0.68 mm. The remaining CC1/BOOT0/ANA_FAULT_N approaches lie inside the J101 or MCU 0.5 mm pin fields (pinout-fixed) and are reported separately |
| **VNEG/VPOS ampacity** (G10, Tier 1 #4) | Re-checked at the real currents (Section 2). The 0.2 mm VNEG segments carry the protection comparators (≤ 2.6 mA), not the amplifier current. The power paths that really carry the High-mode current were reinforced: 5V_ANA now has two 0.7/0.3 mm vias at U503 and a 0.8/0.4 mm via at FB501 (was three single 0.2 mm vias); U102's output has a second 0.8/0.4 mm via (filled); U102 IN/OUT necks widened 0.30 → 0.36 mm (pad width); 5V_SYS L3 crossover 1.0 → 1.15 mm. | G10/G11: no FAIL. Smallest margins: 1.10× (5V_SYS L3, 0.66 A) and 1.13× (5V_ANA L3, 0.49 A), both at the High-mode limit, ≈ 8 K rise |
| **No silk refdes** (G05, Tier 1 #5), thin silk (G01) | All footprint silk strokes raised to 0.15 mm (909 were 0.10–0.13 mm). 261 `${REFERENCE}` legends (1.0 × 0.15 mm) were auto-placed clear of pads, bodies, other silk and the edge (`silkplace.py`). They include every connector and relay, and all but 18 of the ICs, crystals, ferrites, diodes and transistors. The other 273 parts, mostly dense 0402 passives, stay on the F.Fab assembly drawing. | G01, G05 PASS; KiCad DRC 0 |
| **Programming headers look like bare pads** (owner) | J201 (MCU, 1×8) and J202 (CPLD, 1×5) were already XKB SMD pin headers since ECO F05 (BOM C2883805/C2883802), but their footprints had no 3D model. Both now carry KiCad's stock `PinHeader_1x0n_P2.54mm_Vertical_SMD_Pin1Right` model, rotated onto the R1 land pattern (pin 1 dot on the edge row), and J201/J202 now have silk legends. | 3D render shows the headers; models are bundled for CI |
| **Return-path stitching** (G22) | 34 GND stitching vias were placed within 2 mm of clock and audio layer-change vias (`gndvia.py`; clearance-checked on every layer, 0.5 mm from the high-impedance N6_* nodes). | Clock/audio vias without a GND via within 2 mm: **66 → 27**. The rest are slow control and sense lines |

Every change was replayed by the generator. Checks run afterwards:
- KiCad DRC: 0 violations, 0 unconnected.
- Local CI replay of the integrated board: VALIDATE_OK. This covers the placement, DFA, JLC fab, via-pad, power-escape, timer, TVS, trace-budget and DAC-core gates.
- Schematic job steps, run locally: all pass.
- 3D audits: all pass.

## 2. Corrections to the suite inputs

| Item | Reviewer's assumption | Design value (source) | Effect |
| --- | --- | --- | --- |
| Rail currents | Estimates, e.g. VPOS/VNEG 0.4 A at ±15 V, 1V3 0.3 A | Calculation Package v1.1, c03/c17 (26 Sep 2026): VPOS/VNEG **±3.85 V**, LM27762 rated 250 mA; 1V3 60 mA (ESS 50 mA at 80 MHz); VBUS 0.77 A (High mode, S4); 5V_ANA 0.49 A (U503 High limit). Full table in `design_intent.RAILS` | VBUS is now *stricter* than before (0.5 → 0.77 A) |
| G10/G11 current per conductor | The full rail budget through every track and via | Each declared load (`loads`) is drawn at its own pads, and the netgraph solver gives the current in every track and via | Protection-comparator branches stop failing; trunks are judged on their real share |
| G40 loads | Regulator outputs found only by feedback net, so U503/U302/U102 output pins were judged as loads | Declared rail `source` parts excluded. Step current `transient_a` per rail: digital rails take their full budget as one step; analog rails take the load they switch | 1V3 passes at 60 mA (+1.5 dB) |
| G30/G41 LEG resistance | Worst pad pair on the net, including the 330 k–1 M sense-divider taps | Load-current path only (`OUTPUT_SERIES_TERMINALS`) | LEG_LP 0.485 → **0.002 Ω**; damping factor > 1000 into 32 Ω. G41 PASS |
| G13 | Regulator outputs, the MCU ADC divider (VBUS_SENSE) and OPA2210 VREF inputs counted as supply pins | Excluded (`source`, `supply: False`) | 47 → 40 WARN; the rest are real cap distances (Section 4) |
| G21 | N6_MCK_RC counted as a clock | It is the MCLK-alive detector's diode-pump output into 82 pF ∥ 1 MΩ, a DC level | G21 PASS |
| Stackup reading | SWIG `GetStackupDescriptor().GetList()` (missing in KiCad 10.0.1 here) | `extract.py` now parses the board file's `(stackup)` block. `build_stack` takes copper weights from it | — |
| LTspice on macOS | Windows paths only | `run.py` falls back to the bundled `ltspice_wine.sh` | — |

## 3. Impedance evidence

[sim/signoff/signoff_impedance.txt](sim/signoff/signoff_impedance.txt) comes from
`tline_fd.m`, MATLAB's 2-D finite-difference Laplace solver. It solves each geometry with
the dielectrics and in air, takes C from the field energy, and gives Z = 1/(c0·√(C·Cair)).
G20 runs a NumPy/SciPy port of the same solver (`signoff/tline.py`), and the two agree to
0.1 Ω.

- **Validation.**
  - A thin strip on a refined grid comes within 1.2–1.5 % of Hammerstad-Jensen.
  - At 1 oz (t/h = 0.35) the closed-form thickness correction reads 3–5 % higher. Even using
    that value, the worst USB corner would be about 103 Ω, inside +15 %.
  - The USB result changes by 0.9 Ω between 6 µm and 3 µm grids.
- **Clocks.** The 0.15 mm clock lines are 51.5 Ω on this stackup. The clock-SI LTspice deck
  was re-run at that value with no change: XI peaks at 3.29 V, nothing goes below 0 V, and
  edges are 1.0–1.3 ns.
- **Skew.** The odd-mode delay is 5.8 ps/mm, so the 2.15 mm intra-pair mismatch is 12 ps. The
  limit is 100 ps (3.81 mm); the WARN only says it uses more than half of that.

## 4. Remaining WARNs

| Gate | Finding | Disposition |
| --- | --- | --- |
| G03 | 0.2 mm vias at 8:1 in 1.6 mm | Inside JLC's 6-layer window (0.15 mm minimum drill). Owner via-floor decision ce339dc |
| G06 | 55 hole/copper pairs between 0.28 and 0.35 mm | Above JLC's 0.28 mm PTH minimum; 0.35 is their recommendation |
| G10/G11 | 1.10–1.32× margins on 5V_SYS/5V_ANA | Only at the High-mode current limit; ≈ 8 K rise. A 1 oz inner build would remove them at extra cost |
| G13 | 40 bypass distances of 3–12 mm | MCU VDD (iteration-2 item), TLV1704/TLV3402 comparators (µA, slow) and OPA2210/OPA1622 rails at 3–5.5 mm. The OPA1622 loop stability with the extracted parasitics is signed off ([SIGNOFF_SIMULATION](SIGNOFF_SIMULATION_2026-10-07.md) §1b) |
| G20 | Skew uses > 50 % of the budget | 12 ps against the 100 ps limit |
| G22 | 101 vias without a GND via within 2 mm | 27 are clock/audio vias with no legal site; the rest are slow control lines |
| G30 | JACK_LN/RN copper differs by 22 mΩ | 0.006 dB level difference into 32 Ω |
| G31 | I/V output nets long / large single-net loop | Hum depends on the differential loop between the P and N routes. MATLAB puts it at 61–134 mm², times the 1.54 difference-stage gain. With these loops added, the hum budget's smallest margin is **16.2 dB** (criterion 6 dB) ([signoff_hum_budget.txt](sim/signoff/signoff_hum_budget.txt)) |
| G32 | CC2 reaches its clamp through 18.7 mm | The CC lines are slow. Only R102/R104 and a test pad sit between J101 and U103 |

## 5. Fabrication notes for the order

- **Build.** Order JLC06161H-3313, 1.6 mm, 6 layers, outer 1 oz, inner 0.5 oz, ENIG.
- **Impedance control.** Request it for USB_DP/USB_DN at 90 Ω differential on L1, referenced to
  L2. Allow the fab to adjust the 0.17/0.18/0.20 mm widths.
- **Vias.** Fill and cap the in-pad vias, as the via-pad audit lists.
- **Legend.** Silkscreen is on the top side only. The F.Fab layer is the assembly drawing for
  the parts without a legend.
