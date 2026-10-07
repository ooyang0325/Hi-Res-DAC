# Independent sign-off suite

A self-contained review of the Hi-Res DAC board, built from published
criteria rather than from the repository's existing CI. Nothing here imports
or re-uses the other checks in this repo; the intent is a second opinion that
can disagree with the first.

## Running it

On macOS, `run.py` finds LTspice 26's Wine bottle and drives it through
`ltspice_wine.sh`; extract with KiCad's own Python
(`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`).
The gates need NumPy and SciPy (G20's field solver).


```powershell
# Extract the board model (positional argument, not --pcb)
python hardware/signoff/extract.py <board.kicad_pcb> -o hardware/signoff/out/model_integrated.json

# Run every gate
python -m hardware.signoff.run

# A single gate, or skip the simulations
python -m hardware.signoff.run --gate G40
python -m hardware.signoff.run --no-spice
```

Outputs land in `hardware/signoff/out/`:

| File | Contents |
| --- | --- |
| `signoff_result.json` | Full machine-readable result: metrics, findings, assumptions |
| `SIGNOFF_REPORT.md` | Human-readable summary |
| `spice/*.cir` | Every generated LTspice deck |
| `spice/*.log` | Measurement logs backing the simulation verdicts |

The exit code follows the worst gate status, so this works as a CI step.

## Design

```
extract.py   -- the only module that imports pcbnew; emits plain JSON
     |
     v
model_integrated.json  (tool-independent board model)
     |
     +-- geom.py        pad/track/drill geometry
     +-- netgraph.py    resistive network solver per net
     +-- parasitics.py  capacitor ESL/ESR and mounting inductance
     +-- rules.py       published numeric criteria
     +-- design_intent.py  what each net is for
     |
     v
gates_*.py  -->  run.py  -->  JSON + Markdown
```

Keeping KiCad behind `extract.py` means the gates are testable without the
EDA tool, and the same model feeds the geometric checks and the simulations,
so they cannot silently disagree about the board.

## Validation

A review tool that is wrong is worse than no review, so the geometric engine
was checked against KiCad's own DRC before any verdict was trusted:

```powershell
kicad-cli pcb drc --format json --severity-all -o hardware/signoff/out/kicad_drc.json <board.kicad_pcb>
```

| Check | KiCad | This suite |
| --- | --- | --- |
| Unconnected items | 0 | 0 opens across all 12 rails |
| `hole_clearance` errors | 4 (all at J101) | the same 4, same pads, same gaps |

Reaching that agreement found three real bugs in this suite, all of which had
produced confident but wrong output:

1. **T-junctions.** Tracks were modelled as a single endpoint-to-endpoint
   edge, so copper landing part way along another track was treated as
   unconnected. 70 of 333 VPOS endpoints land mid-span, which invented 53
   phantom islands and a 45-billion-millivolt IR drop. Tracks are now split at
   every node that touches them.
2. **Slot drills.** J701/J101 use oval slots. Treating them as circles of the
   major axis produced a false hole-to-hole failure and a physically
   impossible negative annular ring. Slots are now modelled as capsules.
3. **Rounded pad corners.** 762 pads are roundrect. Treating them as sharp
   produced a drill-to-copper violation KiCad did not report; with the real
   corner radius it disappears.

The LTspice measurement parser was likewise validated against a series R-L-C
circuit whose impedance is analytically known, before being pointed at the
board:

| Frequency | Analytic | LTspice via this parser | Error |
| --- | --- | --- | --- |
| 1 MHz | 1.65626 ohm | 1.65656 ohm | 0.02% |
| 10 MHz | 0.50112 ohm | 0.50212 ohm | 0.20% |

That test also caught a regex that let a log preamble line swallow the
following measurement's value.

## What the simulations do differently

`hardware/sim/dac_1v3_bypass.cir` states in its own header that its
inductances are "explicit assumptions" (5 nH and 20 nH). The decks in
`spice/` are generated instead from the board:

- **Capacitance** parsed from the placed part's value field.
- **ESL and ESR** from the actual package (`C_0402_1005Metric` -> 0402).
- **Mounting inductance** from the real via pair under each capacitor --
  measured pitch, measured drill, measured pad-to-via run -- via the
  loop-inductance result in C. R. Paul, *Inductance*.
- **Series resistance and path length** from the solved copper network, so a
  capacitor 33 mm away through copper is modelled as 33 mm away.

Measured mounting inductances come out at 1.0-2.1 nH, so the existing deck's
5 nH best case was pessimistic while its 20 nH case was unrepresentative.

## Handling what cannot be known

The board declares **no stackup**, so the height from the outer layer to the
first plane is unknowable from the design. Rather than pick a number, every
PDN deck sweeps `h` over the plausible construction range (0.09 / 0.12 /
0.20 mm) with `.step` and the gate reports the worst case. The same principle
is applied elsewhere:

- **G10** reports what each conductor would carry at 1 oz inner copper as
  well as the assumed 0.5 oz, which separates findings that survive the
  assumption from those that do not.
- **G40** reports, for every failing rail, the transient current at which it
  *would* pass, so the finding can be settled against a datasheet figure
  instead of against an estimate.

Current budgets in `design_intent.RAILS` are estimates and are marked
`assumed: True`. They should be reconciled with the Calculation Package.

## Gates

| ID | Title | Basis |
| --- | --- | --- |
| G01 | Fabricator process window | JLCPCB capability sheet |
| G02 | Electrical clearance | IPC-2221B Table 6-1 |
| G03 | Plated-hole geometry | IPC-6012 |
| G04 | Assembly geometry | IPC-7351B |
| G05 | Fabrication documentation | IPC-2614 / controlled-impedance practice |
| G06 | Drill-to-copper clearance | JLCPCB 0.28 mm; validated against KiCad DRC |
| G10 | Conductor ampacity | IPC-2221B `I = k dT^0.44 A^0.725` |
| G11 | Via ampacity | IPC-2221B applied to barrel cross-section |
| G12 | DC IR drop | Solved network against a per-rail budget |
| G13 | Decoupling placement and mounted resonance | Mounted self-resonant frequency |
| G20 | USB high-speed pair | USB 2.0 spec: 90 ohm +/-15%, 3.81 mm skew |
| G21 | Clock routing and aggressor spacing | 3W rule; jitter-limited SNR |
| G22 | Return path continuity | Ott, *EMC Engineering* |
| G23 | Switching-node keep-out | Analogue/digital separation floor |
| G30 | Output path resistance and channel matching | Self, *Audio Power Amplifier Design* |
| G31 | I/V and feedback loop geometry | Loop area as a magnetic antenna |
| G32 | External port ESD protection | IEC 61000-4-2 stub let-through |
| G40 | PDN impedance (LTspice) | Smith/Bogatin target impedance |
| G41 | Output loading and damping (LTspice) | Damping factor into the rated load |

`G06`, `G40` and `G41` are the gates with no counterpart in the existing CI.

## Known limits

- Copper weight is assumed (no stackup); G10/G11/G12 inherit that.
- `infer_rail_sources()` is a heuristic. G40 instead identifies regulators by
  their feedback net, which correctly separates the 1V3 LDO (U303, which has
  `N3_1V3_FB`) from the DAC that consumes the rail.
- G40 models each rail at its single worst-case pin, not as a distributed
  plane; it is a lumped study, not a 3D field solve.
- Zones are included in the solved network, but the board routes its rails as
  0.4 mm traces rather than poured planes, so this matters little here.

## Changes after the first run (7 October 2026)

The designer's response is in
[../SIGNOFF_REVIEW_RESPONSE_2026-10-07.md](../SIGNOFF_REVIEW_RESPONSE_2026-10-07.md). Summary of
what changed in the suite (board changes are listed there):

- `design_intent.RAILS` takes its currents and voltages from Calculation Package v1.1, adds
  `source` (rail drivers, never loads), `loads` (per-part maxima), `transient_a` (G40 step) and
  `supply: False` for sense/reference nets.
- G10/G11 solve the current each track and via carries with the declared loads at their pads
  (`NetNetwork.item_currents`); rails without `loads` keep the full-budget check.
- G30/G41 measure the load-current path (`OUTPUT_SERIES_TERMINALS`), not the sense taps.
- G20 computes the differential impedance of every coupled and split section with
  `tline.py` on the declared stackup and its build corners; 3W approaches inside the pin
  field of a part the pair lands on are reported as INFO.
- `extract.py` reads the board file's `(stackup)` block when SWIG cannot; `build_stack`
  takes the copper weights from it.

