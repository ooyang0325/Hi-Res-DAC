# Sign-off simulations (7 October 2026)

These files support [../../SIGNOFF_SIMULATION_2026-10-07.md](../../SIGNOFF_SIMULATION_2026-10-07.md).

## Inputs

- **Board dump.** Dump the routed board with KiCad's python:
  `../board_dump.py ../../DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb board.json`, then
  run `BOARD=board.json matlab -batch signoff_ground_hum`.
  It is not committed (about 6 MB).
- **TI vendor models.** Download them from ti.com into `lt/`. They are not committed: they
  are TI-licensed.

  | File | Download ID |
  | --- | --- |
  | `OPA1622.LIB` | SBOM958 |
  | `TLV76701_TRANS.lib` | SLVMCY1 |
  | `LM27762_TRANS.LIB` | SNVMAV1 (only for the attempted full switching run) |

## MATLAB (R2025a)

| File | Purpose |
| --- | --- |
| `signoff_ground_hum.m` | Parasitic extraction (`signoff_parasitics.csv`), six-layer GND grid solve at 0.3 and 0.2 mm (`signoff_gnd_transfer.csv`), and the hum/whine budget with audibility margins (`signoff_hum_budget.txt/.png`). Set `BOARD=` to pick a dump; `_pre_f10` files come from the board before ECO F10. |
| `gndsolver.m` | Resistive grid of the GND copper on every layer, plus vias. Also computes the plane flux of a unit current (the reciprocity form of the 60 Hz EMF). |
| `netgraph.m`, `routepath_.m`, `allpads_.m` | Routed path extraction: T-junctions, vias and pass-through pads. |
| `pathLC.m`, `ldo_paths.m` | Series L/R of a routed path. `signoff_ldo_paths.txt` compares U504's capacitor paths before and after block 16. |
| `ltraw.m`, `hp_margins.m` | Read the LTspice ASCII raw files and compute crossover, phase margin and gain margin (`signoff_hp_stability.txt`). |
| `test_gndsolver.m` | Unit test on a synthetic sheet: a symmetric pair gives zero chord deviation; an edge pair bows into the sheet. |
| `check_routes.m` | Plots the extracted single-ended routes against their straight returns (`check_routes.png`). |
| `tline_fd.m`, `signoff_impedance.m` | 2-D finite-difference field solver for L1 microstrip on the declared stackup, validated against Hammerstad-Jensen; USB pair sections and clock Z0 at the build corners (`signoff_impedance.txt`). The sign-off suite's G20 uses a NumPy port of the same solver (`../../signoff/tline.py`). |

## LTspice 26.0.2 (`lt/`)

Run with
`CX_BOTTLE_PATH="$HOME/Library/Application Support/LTspice/Bottles" /Applications/LTspice.app/Contents/SharedSupport/ltspice/LTspice/wine --bottle=ltspice --wait-children 'C:\Program Files\ADI\LTspice\LTspice.exe' -b -ascii 'Z:\path\deck.cir'`.

| Deck | Question |
| --- | --- |
| `hp_loop*.cir` | OPA1622 leg loop gain in 7 load/relay cases, as built / with the ferrite + 220 pF ECO / with the F10 sense return |
| `hp_cmrr.cir` | Difference-stage common-mode gain at the worst 0.1 % / 0.05 % resistor corners (ECO F10) |
| `ldo_ref.cir`, `ldo_u504*.cir` | TLV767 regulation point, load step and output impedance with the old and new extracted paths |
| `cp_u501_ro.cir` | LM27762 reduced-order 2 MHz switching current: ground bounce at the pad, old vs new |
| `clk_si.cir` | MCLK 80 MHz and BCLK signal integrity with the extracted transmission lines |
