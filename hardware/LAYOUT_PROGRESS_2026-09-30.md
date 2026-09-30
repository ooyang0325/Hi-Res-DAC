# DAC-HPA layout progress · 30 September 2026

**State: engineering study, release HOLD.** This continues the
[29 September handoff](LAYOUT_ENGINEER_HANDOFF_2026-09-29.md) on the
[integrated 120 × 100 mm board](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb),
base commit `72c24c3`. All additions are recorded in the frozen
[manual delta](INTEGRATED_AUDIO_MANUAL_DELTA.json) and replayed by
[manual_integrated_audio_study.py](manual_integrated_audio_study.py). Do not
order PCBA from this copper.

| Measure | 29 Sep | 30 Sep |
| --- | ---: | ---: |
| Manual footprint moves | 138 | 178 |
| Added copper items | 828 | 5406 |
| Vias (manifest) | 143 | 1305 |
| Full `pcbnew` ratsnest links | 864 | **82** |
| KiCad DRC violations (errors + warnings) | 0 | 0 |
| Exact / near-90° free bends | 0 | 0 |

The CI job `validate_integrated_audio_study` passes locally with KiCad 10.0.1
(checkpoint commit; routing continues, see *Checkpoint changes* below).
The unfilled near-SMT-pad via triage list grew from 45 to 187; none is below
the 0.10 mm gate. Most new ones are GND return vias 0.20–0.35 mm from 0402
pads. Choose JLC via tenting or plugging for them in the order.

## What was routed

- **USB-C (J101 → U101 → U201).** U101 is rotated 180° so the pair flows
  through the USBLC6 in pin order without a crossing. Both nets stay on L1 with
  no vias, at 0.235/0.15 mm over continuous L2, with 10.7 mm coupled. The A7
  land joins B7 under the receptacle body and A6 joins B6 around A7. Skew is
  +2.76 mm (about 18 ps) with the plug one way and +0.32 mm the other.
  The closed-form edge-coupled microstrip estimate for JLC's default 7628
  stack-up is about 90–93 Ω. **This is not a field-solver or quoted-stack-up
  result.** CC1/CC2 cross under the pair on B.Cu. VBUS joins both receptacle
  lands on L3 and feeds U502 on B.Cu; both J101 necks pass the escape audit.
  U502/C102/C502/TP703 moved to the empty pocket north of J101. U103, R101–R104
  and TP726/TP727 moved east of the pair. The shield stakes are tied on B.Cu to
  the R107/C101 RC.
- **GND returns.** 181 new GND vias tie pad islands to L2. Each is the nearest
  clear spot, at least 0.2 mm from any SMD pad and at least 0.35 mm where
  possible. 16 GND islands remain (mostly U201 LQFP GND pins; see below).
- **VPOS/VNEG.** A 1.2 mm L3 pair leaves U501's output caps C510/C511. It runs
  at 1.5 mm pitch (0.3 mm gap) along y≈125 and then north at x≈132–133, clear
  of the L3/L4 I/V feed barrier, and lands on the existing amplifier bridge.
  Keeping the pair tight minimises loop area and therefore 50/60 Hz magnetic
  pickup. Two B.Cu crossings (x≈100.6 and 121.2) feed VPOS loads enclosed by
  the VNEG trunk, and two B.Cu crossings feed C414 and D412. The U613–U620
  cluster has stacked buses, VPOS on L3 and VNEG on B.Cu, fed from the
  amplifier bridge and U402's EP island. All VPOS/VNEG pads are on one network.
- **OPA1622 exposed pads.** Filled/capped thermal vias tie them to VNEG:
  three in U402 with L3 and B.Cu islands, and two in U401. U401 gets only two,
  in the lower half, because the prior `N4_IVR_P` B.Cu diagonal passes under the
  top of its pad (see holds).
- **I/V-stage rails.** N4_VPOS_IV/N4_VNEG_IV run from D411/D412/C442/C443 as a
  B.Cu pair (0.5 mm tracks, router kept to 0.8 mm pitch) to U404, plus D413 and
  TP751.
- **3V3M, 3V3D, 3V3A, 5V_SYS.** 3V3M is an L3 tree from U502. 3V3D is a 0.8 mm
  B.Cu backbone from U504 along the west edge, then y≈99, then the CPLD, with
  branches. 3V3A runs from U302 to the DAC R301/R302 branch on B.Cu, then
  protection loads. 5V_SYS is at least 1 mm except the whitelisted U102/U504
  WSON necks, and runs from U102 to D104/D105/R105/TP701 and the
  U503/C501/C505/U504 group.
- **Checker change.** `check_integrated_audio_study.py` now requires the local
  U401/U402 VPOS/EN group to be a *subset* of the connected group rather than
  equal to it. The old equality encoded "main feed open". Its summary wording
  now reflects the connected feeds.

## Method

Critical copper was drawn with hand-chosen waypoints: the USB pair, the ± trunk
pair and buses, EP vias, and the corners. Short power spurs, the rail trees and
GND return vias used a local octilinear (45° only) grid router with a
nearest-clear-via helper. These ran one connection at a time inside a window I
chose, and were checked against DRC, the CI gates and layer crops. No
placement search and no whole-board autorouter was used. The helper scripts
are not in the repository; the frozen delta is the record.

## Holds and decisions for the owner

1. **I/V feed topology (audio quality).** The prior N4_IV* feeds cross the
   board as long L3/L4 diagonals. N4_IVR_P and N4_IVR_N run under or beside the
   **left** output amplifier U401 to reach R409/R411. Together with VREF they
   enclose U403 on every layer, so **U403's N4_VPOS_IV/N4_VNEG_IV pins and
   TP750 are still open.** Connecting them needs a coherent reroute of the four
   I/V feeds. Doing that properly probably means re-placing the output stage so
   that neither channel's I/V → output path crosses the other channel. This is
   an ECO decision.
2. **RF immunity measures that change project policy.** Outer-layer GND pours
   with edge and via stitching, and L3 GND "shadow" copper under the four L4
   headphone trunks, would both strengthen immunity to Wi-Fi/cellular fields.
   The checker and replay currently allow exactly one zone (L2 GND), so either
   needs an owner decision.
3. **Still open.** 477 ratsnest links remain: protection N6_* signals, MCU and
   CPLD fan-out and digital signals. Also open are the U201 GND pins
   12/18/31/47/63 and 3V3M pins 13/19 (each next to a GND pin at 0.5 mm pitch;
   they need an MCU fan-out block), 5V_SYS to U302/C301 and the relays
   K601/K603, 5V_ANA/5V_ANA_F, VBUS to U102/R109/TP736/TP753, 1V3/VREF/AVCC
   local links, R657 (3V3A) and D414.1 (N4_VNEG_IV). All holds from the
   29 September handoff (discharge ECO, 2512 lands, all-rate capture guard,
   G-3/G-4, JLC DFM, measurements) still apply.

## Checkpoint changes (second half of 30 September)

- **Pours.** GND pours on F.Cu, L3 and B.Cu (clearance 0.3 mm, L2 clearance
  0.3 mm) are part of the manifest (`added_zones`, `l2_clearance_mm`). The
  replay now refills every pour with `kicad-cli`, because the pcbnew scripting
  filler ignores the `.kicad_dru` pour rules (high-impedance nodes 0.5 mm and
  USB pair 0.6 mm to GND pour).
- **Placement moves to clear blockages:** R505 (5V_ANA_F pull-up) out of the
  U505/R511 pocket; R531/C513 (1 Ω + 10 µF input damper) from 20 mm away to the
  FB501.2 node; R245 (DC_SENSE_RN series R) off the U201 south pin row; DNF R703
  beside the MCLK trunk, ≥2 mm from the DAC inputs.
- **Routed:** 5V_SYS to U302/C301 and the K601/K603 photo-relay inputs, all
  5V_ANA/5V_ANA_F feeds at 0.8 mm, VBUS to U102/R109/TP736/TP753, the U201 south
  fan-out (VDD pins 13/19 straight to C204/C205), 1V3/VREF/AVCC local links, and
  most protection and control signals.
- **Checker scope changes.** `check_dac_core_routes.py` counts only the two
  0.7/0.3 mm U303→U301 bridge vias as the 1V3 bridge; the 0.6 mm TP706/R530/R670
  branch vias are reported separately. Earlier: U401/U402 VPOS/EN subset check,
  GND pours allowed, LEG_* sense taps allowed off L1 (Spec R07).
- **Short VREF.** DNF trims R446/R447 and TP709 moved from 25–30 mm away to the R431/R432/C421
  divider, so the ~4.9 kΩ I/V reference no longer runs through the digital area (it was 0.45 mm
  from LINK_SCK and ~1.1 mm from MCLK).
- **U201 escape ring.** Seventeen series/pull resistors around the MCU moved ~3.5 mm outward to
  make room for fan-out vias; decoupling caps, crystal group and Q207 stay.
- **GND stitching and jack returns.** 375 stitching vias (4 mm grid + 2.5 mm edge fence) and
  five strapped GND vias per jack sleeve pin. The MCU/CPLD core and the protection-comparator
  block are stitched after their routing closes. See [EMS_VERIFICATION_2026-09-30.md](EMS_VERIFICATION_2026-09-30.md).
- **DRU policy: slow digital control nets at 0.15 mm.** 47 MCU/CPLD control nets (enables, JTAG/SWD,
  I²C, link, ADC sense; no clocks, USB, I²S, power, audio or protection nodes) may sit 0.15 mm from
  each other (JLC 4-layer capability 0.1 mm); every other pair keeps ≥ 0.2 mm. **Owner review.**
- **U201 fan-in.** Twenty MCU pins sealed on the outside drop to vias in the ring between the pin
  rows and the GND-island core under the package body and continue on L3/L4.
- **DAC input via keep-away.** Router vias stay ≥0.8 mm from DACL/DACLB/DACR/DACRB
  copper, and from the critical I²S/MCLK/FAM_CLK copper, so L2 stays solid under them (`check_iv_macro`, `check_dac_core_routes`).
- **EMS simulations.** LTspice/MATLAB review models in [sim/](sim/README.md) and the
  calibrated-model stability sweep `review_output_rf_filter.py` (output RF filter ECO proposal).
- **Discharge fit option.** The separate 2512 fit-option board was drawn against the
  integrated board at 72c24c3; its check now compares against a frozen copy of that snapshot
  (`DAC_HPA_120x100_DISCHARGE_FIT_SOURCE_72c24c3.kicad_pcb`). Its moves (e.g. R531) and routes
  overlap this session's layout, so the fit option must be re-studied on the current board.
- **Tooling.** Signal links are drawn by a scratch octilinear three-layer grid
  router with DRU pair rules (headphone L/R 2 mm, clock-to-high-Z 5/10 mm,
  high-Z 0.3–0.5 mm, I²S 0.15 mm on L1 only). DRC-flagged router connections are
  dropped and re-routed. The frozen manifest is the record; the router is not in
  the repository.
