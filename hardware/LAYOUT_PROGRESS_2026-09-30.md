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
| Manual footprint moves | 138 | 179 |
| Added copper items | 828 | 5795 |
| Vias (manifest) | 143 | 1366 |
| Full `pcbnew` ratsnest links | 864 | **12** |
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

## 6-layer stack (owner decision, 1 October)

Routing on 4 layers plateaued at 63–64 links, so the study moved to 6
layers. Block 72 adds L4 and L5; the replay sets `copper_layers: 6` in the
manifest.

| Layer | Role |
| --- | --- |
| L1 F.Cu | signal |
| L2 | solid GND plane (unchanged) |
| L3 PWR | signal / power with GND pour |
| L4 SIG | signal with GND pour (new) |
| L5 GND5 | solid GND plane (new) |
| L6 B.Cu | signal |

Results:
- One automated pass plus two Freerouting rounds took the board from 64 to 51
  links, with 0 DRC and VALIDATE_OK.
- B.Cu track without GND directly beneath fell from 1 150 mm (45 %) to
  301 mm (11 %), because L6 now sits over the L5 plane.

Open gates:
- **Stack-up.** Confirm JLC's 6-layer 1.6 mm stack. The EMS audit assumes
  L1–L2 / L5–L6 ≈ 0.10 mm, L3–L4 ≈ 0.11 mm and cores ≈ 0.55 mm.
- **USB impedance.** The 0.235/0.15 mm pair (sized for 0.21 mm to L2) is now
  0.16 mm wide at the same 0.385 mm pitch (0.225 mm gap). Over 0.10 mm L1–L2
  that estimates to about 91 Ω differential (IPC-2141 edge-coupled microstrip).
  Confirm with the JLC impedance calculator once the stack is fixed.
- **Crosstalk.** L3 and L4 are a tightly coupled pair. Keep their long runs
  orthogonal to limit broadside crosstalk.

### Inner-layer rip-up (round 9, 2 October)

After two rounds L4 still carried only 505 mm of track on 13 nets. All copper of
the 90 plain digital/control nets was ripped (1 775 copper lines, about 3.4 m,
hand copper included) and re-routed by Freerouting with fan-out over the four
signal layers, followed by one automated pass. Fixed throughout: audio, high-Z,
clock/I2S, USB, power and analog nets.

| Layer | Before (mm / nets) | After (mm / nets) |
| --- | --- | --- |
| L1 F.Cu | 4 158 / 235 | 3 686 / 235 |
| L3 PWR | 3 377 / 100 | 3 259 / 99 |
| L4 SIG | 505 / 13 | 1 560 / 50 |
| L6 B.Cu | 2 744 / 97 | 2 212 / 77 |

Result: 51 -> 34 links, 0 DRC, VALIDATE_OK. High-Z deviation pairs fell from
30 to 25. Freerouting slivers and right-angle elbows were removed
(`chamfer.py`/`sliver.py` in the routing scratchpad). Audio output legs routed
on L3/L4 overlap adjacent-layer copper broadside for at most 6 mm per net, and
only DC or slow control nets (N6_H, LED_G). These outputs are low-impedance, so
the coupling is negligible.

Round 10 repeated the rip-up with 16 Freerouting passes plus one automated pass:
34 -> 30 links, 0 DRC, VALIDATE_OK, high-Z deviation pairs 27. Seven router vias
that sit within 0.10 mm of an SMD pad are filled and capped: six on their own
test-point/pin net, plus RELAY_EN beside U604.6.

### Clock-mux and ground clean-up after the rip-up (2 October)

- **Oscillator clocks on F.Cu only.** The 49.152 MHz (X202) and 45.1584 MHz
  (X203) clocks, the mux inputs and the mux output are now L1-only nets with no
  vias, over the solid L2 plane. N2_MUX_I0 and N2_MUX_I1 had run 25–31 mm with
  2–3 vias over L3/L4, because their pull-downs R216/R217 sat 14 mm away.
  - **Moves:** R216 and R217 moved to within 2.5 mm of U205, R224 (LINK_SCK
    series R) moved toward U208, and R210 was turned so the two clocks never
    cross.
  - **Result:** all five nets are now 1.7–4.3 mm.
- **Stranded GND pads.** Inner-layer routing had split F.Cu pour fragments, and
  nine GND pads lost their path to L2: four U201 VSS pins, U205.2 (the clock mux
  ground between its two inputs), R216, R234, R640 and C641.
  - **Fix:** each pad has a stub + via or a short tie to a stitched via (block
    73), with digital copper moved out of the way.
  - **Neighbouring changes:** MUX_I0 now comes into U205 from the south;
    DC_SENSE_RN jogs west under R640; N6_VORP pin 9 drops to B.Cu inside the
    U612 pin row, so N6_VORN crosses under U612 directly instead of a 30 mm
    loop round C641.
  - **Check:** a KiCad connectivity check (every GND pad reaches the L2 plane)
    now passes.

29 links, 0 DRC, VALIDATE_OK, high-Z deviation pairs 28.

## I²S capture copies (functional ECO F07, owner decision, 2 October)

The design notes put the 330 Ω bit-perfect capture taps R228–R230 at the CPLD
end of N2_BCLK_SRC / N2_LRCLK_SRC / N2_SDATA_SRC. Those three lines leave U202
pins 18–20 side by side as F.Cu-only 0.15 mm 3W routes. With no vias allowed,
the middle (LRCLK) line cannot branch a tap without crossing a neighbour, and
the taps had been unrouted since the first iteration. The owner chose
CPLD-driven copies:

| U202 pin | New net | Series R | Capture net / MCU pin |
| --- | --- | --- | --- |
| 22 | N2_CPY_CK | R228 330 Ω (pad 1) | N2_CAP_CK → PB13 |
| 15 | N2_CPY_WS | R229 330 Ω (pad 1) | N2_CAP_WS → PB12 |
| 23 | N2_CPY_SD | R230 330 Ω (pad 1) | N2_CAP_SD → PB15 |

- **Source series resistors.** R228–R230 now sit at the CPLD, 1.5–5 mm from
  their pins. The DAC-bound SRC lines carry no capture stubs.
- **RTL.** Must drive the three copy pins from the same I²S output registers,
  on the same clock edge as pins 18–20.
- **What the capture covers.** The bit-perfect capture now verifies the CPLD
  output logic, not the waveform at the DAC pins.
- **TP717 (SDATA test pad).** Moved onto the SDATA 45° run below R206: zero
  stub, instead of a 6.5 mm test branch.
- **R224.** Stays at the MCU (design note). It and the MUX_I0 pull-down R216
  share the pocket between R210/U205 and X203. The X203 supply via moved to its
  pad (filled) to make room.
- **Code.** Captured in `generate_schematic.py` (asserted overlay),
  `verify_schematic.py` (approved delta) and board block 76 (`added_nets` and
  `renamed_pads` in the replay).

28 links, 0 DRC, VALIDATE_OK, schematic checks PASS, high-Z deviation pairs 28.

Round 11 (2 October) re-ripped the 88 plain digital nets (now including the F07
copy nets) with 16 Freerouting passes: 28 -> 23 links, 0 DRC, VALIDATE_OK, all
GND pads on the L2 plane (R213.2 re-tied), high-Z deviation pairs 29.
AVCC_EN had fallen under the `AVCC_*` 0.3 mm supply-width rule; it now has an
explicit 0.15 mm entry, so the MCU pin can escape. Two router vias beside
other-net SMD pads (TP751, U604.6) pass DRC and are filled and capped against
mask bridging.

### Fixed-net closures (2 October)

- **N6_LWRN** (high-Z, F.Cu only, no vias). LEG_RN passes through R933 pad 1 in a
  Λ that walled pad 2 off from C646. R933 turns 180° about pad 1, so the
  LEG_RN copper is unchanged, and C646.2's GND via moves west.
- **N6_ORLP** (high-Z, F.Cu only, no vias). U611 pins 4–7 now loop south of the
  pin row, mirroring N6_ORLN on the north side. The R937→U611.6 N6_VORN link
  that enclosed pin 7 now takes a short L4 hop at the body edge.
- **LEG_LP → R624** (DC-sense divider tap). 24 mm, of which 20 mm is on L4; the
  local DC_SENSE_LP copper that enclosed R624.1 was re-routed. The leg is the
  low-impedance amplifier output.
- **Open EMS item.** Freerouting gave DC_SENSE_LP and DC_SENSE_LN 150–165 mm
  perimeter routes, mostly on L3, to the MCU ADC. They are RC-filtered DC
  monitors behind high-value resistors, so they cannot couple into the audio,
  but they should be shortened to a direct centre-board route before release.

20 links, 0 DRC, VALIDATE_OK, all GND pads on L2.

- **N6_VT** (DC threshold node, vias allowed). On U609 and U610, pins 9 and 11
  straddle the no-via N6_TLN pin, and pin 11 was boxed in.
  - **U610.** Pin 12's VNEG via steps 0.3 mm east, and pin 11 drops to a via
    straight below its pad.
  - **U609.** LEG_RN jogs 0.65 mm east on B.Cu under the pin row, pin 12's VNEG
    via steps west, and N6_TLN_L's north branch is re-shaped: shorter than
    before, starting at the pad tip so KiCad's 8 mm U609.10→R921.2 timer path
    still passes.
  - Both vias join N6_VT on L4.

Every fixed (analog, high-Z, audio, clock, power) net is now complete. The 18
remaining links are all on plain digital/control nets: 18 links, 0 DRC,
VALIDATE_OK, high-Z deviation pairs 29.

Round 12 (2 October): 89-net digital rip-up (AVCC_EN now included), 16
Freerouting passes, automated clean-up. 18 -> 12 links, 0 DRC, VALIDATE_OK, all
GND pads on L2, high-Z deviation pairs 28.

## CPLD pin reassignment (functional ECO F06, 1 October)

Owner-approved, layout-driven AGRV2K (U202, QFN-32) I/O swap. Only
general-purpose `IO/PIN_n` pins move; FAM_CLK (IO_GB pin 1), JTAG, NRST,
power and the already-routed I²S/LINK_SCK/LRCLK_FB pins are unchanged.
**The CPLD RTL pin constraints must follow this table.**

| Net | Source pin | F06 v2 pin | Side | Why |
| --- | ---: | ---: | --- | --- |
| LINK_FRAME | 11 | 26 | north | faces U208 (isolator) |
| LINK_MOSI | 10 | 27 | north | faces U208 |
| LINK_MISO | 12 | 28 | north | escapes north toward U201 |
| CPLD_IRQ | 14 | 29 | north | escapes north toward U201 |
| OSC48_EN | 2 | 31 | north | X202/TP713/R212 are north and west |
| OSC44_EN | 3 | 8 | west row, escapes south | X203/U205/R213/TP714 |

v2 replaces the first F06 table. The west row is walled by FAM_CLK and its
0.8 mm L2-protection via keep-out, so it now keeps only FAM_CLK (pin 1),
CPLD_NRST (pin 4, dedicated) and VDDA33 (pin 6). Pins 2, 3, 10, 11, 12 and 14 become NC. The schematic overlay is in
`generate_schematic.py`, and the approved delta is in `verify_schematic.py`.
The board replay applies the same map through the manifest's `renamed_pads`.
A second rip-up Freerouting round after F06 routed LINK_MOSI (63 links). The
CPLD 3V3 L3 spine was moved from beside the west pin row (x 79.5) to under the
package body (x 80.6), clear of the EP vias; C213/C214/C215 path screens are
unchanged. The west pins are still sealed: FAM_CLK (R215 → TP712 → pin 1)
runs vertically beside pins 1–5, and its 0.8 mm L2-protection via keep-out,
together with U205's 3V3D via, leaves no via site. Next step: give U202 more
room (east shift with its decoupling) rather than squeeze its west side.

MCU GPIO swaps were reviewed and not taken: U201's south side is all ADC,
oscillator and reset pins, so no swap shortens the south-bound control nets.

**FAM_CLK corridor (block 66).** R215 now stands level with U202 pin 1, so
FAM_CLK is a straight 1.5 mm L1 run along the pin-1 row (L2 support check
passes). The mux output N2_MUX_Y takes the vertical leg instead. TP712 sits
on a 1.25 mm stub, and C222's GND return uses C220's existing via. This opens
one legal via site beside CPLD_NRST (pin 4).

**Routing status.** Several further rip-up rounds were tried; none got below
63 links:
- reserved inward/outward fan-out for U201/U202/U208;
- Freerouting with plain-net hand copper movable.

About 49 link ends are pads that cannot escape, 20 of them on U201. The next
step agreed with the owner is to re-floorplan the MCU/CPLD digital block into
the free NE area. VREF was briefly caught by the plain-net filter in one round
and has been restored to its hand route; the filter now excludes VREF and the
analog sense nets.

## Programming headers (functional ECO F05, 1 October)

J201 and J202 were bare 2.54 mm debug pad rows. They now carry JLC-assembled
SMD vertical pin headers, so a WCH-LinkE (MCU) and the AGM programmer (CPLD)
plug straight in:

| Ref | Part | LCSC | Pins |
| --- | --- | --- | --- |
| J201 | XKB X6511WVS-08H-C60D48R1, 1×8 SMD, staggered legs | [C2883805](https://www.lcsc.com/product-detail/C2883805.html) | 3V3 (via DNF R241), SWDIO, SWCLK, NRST, GND, BOOT0, USART_TX, USART_RX |
| J202 | XKB X6511WVS-05H-C60D48R1, 1×5 SMD, staggered legs | [C2883802](https://www.lcsc.com/product-detail/C2883802.html) | 3V3D, CPLD_JTCK, CPLD_JTMS, CPLD_NRST, GND |

- SMD rather than through-hole: the headers drill nothing, so L2 stays whole
  and the L3/B.Cu routes under the north edge (DC_SENSE_LP, BOOT0,
  N2_CAP_SD) are untouched. The land pattern is from the XKB drawing: 1.27 ×
  2.2 mm pads, rows ±1.8 mm, R1 type (pin 1 on the board-edge row).
- The pin line moved 0.5 mm south (y 43.0 → 43.5) for 0.6 mm pad-to-edge.
  R241 moved to (49.5, 44.0) beside J201.1; FID5 moved 1 mm south.
- Captured in `generate_schematic.py` as ECO F05 (the Parts List workbook is
  unchanged; add the two rows there when it is next revised). The replay swaps
  the footprints through the manifest's new `swapped_footprints` entry.

## Freerouting gap fill (late 30 September)

The remaining open links were exported to Freerouting 2.4.1 with **every
existing track and via fixed**, the F.Cu/L3/B.Cu GND pours removed, L3 declared
a signal layer and GND un-routed (pours and stitching own it). Net classes were
rebuilt from the router rules: L1-only nets restricted to F.Cu, high-impedance
nodes at 0.3 mm, slow digital nets 0.15 mm. Only new copper of target nets was
imported, then cleaned for the bend gate (in-pad landing fragments removed,
near-90° elbows chamfered) and screened by KiCad DRC.

- Completed: `CPLD_JTCK`, `DC_SENSE_LP`, `N6_GMC`, `N6_IREF`.
- `DC_SENSE_LP` (R242 → R628, DC-servo sense, RC-filtered at the MCU) runs
  about 100 mm on L3 along the west edge. L3 is shielded by L2 GND and the
  B.Cu GND pour; re-route shorter once the protection block is re-placed.
- GND ties: U202.17 and R212.2 pour pieces had no via; each now has an F.Cu
  stub + via to L2. C641.2, R640.2 and U608.4 still have no legal via spot.
- With all copper fixed, Freerouting found no path for the other links: the
  remaining 67 are a placement/rip-up problem, not a router-quality one.
- **Rip-up round.** A second run let Freerouting move the router-drawn copper
  of 93 plain control/test nets (hand copper and every clock, I²S, audio, LEG,
  high-Z, L1-only and power net stayed fixed; via keepouts 0.8 mm along the
  clock/DAC tracks keep L2 continuous under them; fiducials keep 0.6 mm).
  After import, DRC and gate screening: 67 → 64 links, high-Z deviations
  unchanged at 29. The remaining links need component re-placement.

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
- **U201 fan-in.** Forty MCU pins (two rounds) sealed on the outside drop to vias in the ring between the pin
  rows and the GND-island core under the package body and continue on L3/L4.
- **CPLD neighbours.** R231/R225/R211/R212/R213 moved outward from U202; trapped protection passives
  (R624, R657, R674, R927, R625, R662) nudged where free courtyard space existed.
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

## High-impedance spacing deviations (owner review)

Design Notes v1.0 §9.3.1 asks for ≥ 0.5 mm from high-impedance nodes to other copper. The DRU
enforces 0.5 mm to the GND pour and 0.2 mm elsewhere. To finish the protection-comparator
links, the router was allowed 0.2 mm locally (under solder mask; leakage negligible at ~1 MΩ
node impedance, but less margin against contamination/humidity). 29 high-Z/other pairs are
now below 0.5 mm outside the 1.8 mm pin-escape zones; the ten closest:

| High-Z net | Neighbour | Gap (mm) | At (x, y) |
| --- | --- | ---: | --- |
| N6_DB_R | N6_DD_R | 0.225 | (117.9,114.1) |
| N6_DD_R | N6_DB_R | 0.225 | (117.5,114.2) |
| N6_VORP | VPOS | 0.250 | (80.0,123.1) |
| N6_CML | N6_OLN_L | 0.250 | (76.9,98.3) |
| N6_TWLPP | N6_VLLP | 0.268 | (99.9,49.5) |
| N6_MCK_RC | 3V3A | 0.307 | (82.4,95.0) |
| N6_VORP | N6_OLN_R | 0.310 | (91.0,125.2) |
| N6_DB_R | VPOS | 0.330 | (122.1,126.4) |
| N6_CML | V3A_MON | 0.330 | (71.8,111.4) |
| N6_V3AG_A | 3V3A | 0.370 | (80.6,87.8) |
