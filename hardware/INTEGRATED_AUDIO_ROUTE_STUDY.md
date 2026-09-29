# Integrated DAC/I/V-to-jack and U501 route study — 29 September 2026

**Use this as the current integrated routing review candidate, not as order data.**
The editable [KiCad board](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb)
keeps the 120 × 100 mm four-layer outline, 544 footprints, 250 named nets and
the v1.1-ECO1 schematic pad map, including the explicit U403/U404 A/B-channel
reassignment in the [functional ECO](FUNCTIONAL_ECO_2026-09-28.md). Every
placement and waypoint in this trial was chosen manually; no placement or
routing search was run. Component values did not change.

The later [DAC/core route checkpoint](DAC_CORE_ROUTE_STUDY.md) extends this
study's DAC/CPLD routing measurements: MCLK is 8.381 mm, and BCLK/LRCLK/SDATA
are 22.213/22.324/22.879 mm with 0.666 mm spread. It adds routed local
U202/U302 paths and a connected 25.393 mm U303→DAC 1V3 trunk with two vias.
Two vias in U202's EP and five in U301's DAC EP are flagged filled/capped;
U401/U402 output-amplifier EP thermal routes remain open. The current board
has 848 track/via items (143 vias), 866 full ratsnest links, 499 DRC-
unconnected items and zero DRC violations. Full routing, system ESD, EMI and
audio tests remain open; zero DRC violations applies to partial copper only.

## What this trial closes geometrically

- U301 DACL/DACLB/DACR/DACRB reach U403 pin 6/pin 2 and U404 pin 6/pin 2,
  respectively, on F.Cu without vias. Their routed pad-centre lengths are
  **4.294/6.030/6.837/4.786 mm**, all under the owner-approved provisional
  7 mm target; DACR has only **0.163 mm** margin. R423–R426 and C417–C420
  have local feedback copper. The largest **projected 2D centreline**
  feedback area is **4.875 mm²**, using
  straight closures across part and op-amp pads; it excludes vertical and
  return-current area and does not establish stability. Courtyard gaps near
  C423/C426 are only **0.150–0.194 mm** and need assembly review.
- The four I/V output copper groups reach all **eight first T resistors** and
  their respective clamp and common-mode tap pads. The longest routed feed
  is **47.752 mm** (`N4_IVR_P` to R409); the right `N4_IVR_N` feeds to
  R411/R413 are **27.289/41.648 mm**. These feeds change layers and need
  parasitic, coupling and return-path extraction. The central
  VREF branches are drawn, with a longest route of **14.422 mm**; low-noise
  VREF distribution and its return remain unverified.
  The local L3 VPOS bridge crosses the two right I/V L4 feeds near
  x = 115–121 mm, y = 74–76 mm. Their projected overlap areas are about
  **0.52/0.25 mm²** (`N4_IVR_N`/`N4_IVR_P`). A simple plate estimate using
  an **assumed** 0.15–0.30 mm L3/L4 dielectric and relative permittivity
  3.5–4.5 gives roughly **0.054–0.139/0.026–0.066 pF**, excluding fringing
  and nearby vias. The actual stack-up and rail noise have not been
  extracted; this is a coupling review item, not an audio-noise prediction.
  The saved filled L2 GND is directly beneath all four DAC→I/V input traces
  at **0.01 mm** route samples and normal offsets **0, ±0.05, ±0.10 mm**.
  This sampled support does not establish return impedance. DACL's
  U403→C417 feedback branch still lacks direct L2 beneath **1.9426 mm** of
  its centreline near an I/V-output via, **0.0597 mm more** than the
  **1.8829 mm** prior committed baseline measured like for like. The L2
  polygon remains connected, but this feedback return detour stays on HOLD
  for relocation or extraction and stability validation.
- U401/U402 face the I/V stage. Their four 10 pF Rf/Cf paths are routed with
  **4.833 mm² centreline loop area each**, below the provisional 5 mm² screen.
  The headphone-current branches leave 0.932 mm, 0.25 mm-wide VSON escapes;
  load current does not travel through the 0.20 mm feedback traces.
- K601, K602 and K603 form a lower row, while K604 stays upper right.
  R417/R418/R419 are below their lower relays; R420 serves K604. The four
  amplifier outputs reach their relay input contacts through 1.0–1.5 mm
  L4 trunks and 1.0 mm L1 `LEG_*` branches, with two Ø0.60/0.20 mm signal
  vias per leg. `LEG_*` and `JACK_*` remain on L1 with no vias. The custom
  DRC now requires **2 mm left/right clearance on F.Cu pre-link
  `N4_*_OUT` copper** against the opposite channel's pre- and post-link
  output copper, alongside the existing post-link rule. L4 coupling still
  needs extraction and measurement. K601/R417 were shifted 2.4 mm and their
  copper rerouted to open the input corridor; J701/J702 did not move.
- All eight local input T triplets now have F.Cu copper from input resistor
  through output resistor to the corresponding U401/U402 input, with their
  shunt-capacitor branches connected and each capacitor returning to L2.
  The routed branch maxima are
  **6.53 mm Rin→Rout, 7.25 mm capacitor→Rout and 8.29 mm Rout→amplifier**.
  R444 and C433 were rotated 180° to avoid T/ground crossings. Signal copper
  now connects the DAC current pads through I/V and T cells to U401/U402
  inputs; extracted behavior and powered operation remain unverified.
- All four relay outputs physically reach the intended J701 audio contacts.
  LP and RP also reach J702 through their local TVS branches. J701 LP pads
  7/8 are joined around switch pads 9/10; RP pads 4/5 avoid the mounting peg;
  RN pads 2/3 and LN pad 6 are connected. J702 break contacts 5/6 and J701
  switch pads 9/10 remain no-connect copper, never tied to GND.
- U401/U402 GND pins, all four amplifier input-shunt returns, and the jack
  sleeve pads connect to the **same single filled L2 GND polygon**. Each
  input shunt also reaches its corresponding amplifier input pin. The six
  [named-pad TVS paths](INTEGRATED_AUDIO_LOCAL_TVS_AUDIT.json) remain
  **3.255–4.03 mm**, under the owner-approved provisional 4.2 mm screen.
- U401 pin 4/exposed pad/C410 and U402 pin 4/exposed pad/C412 now form short
  local V− copper groups; each 100 nF capacitor returns to L2 through a
  nearby GND via. U401 pin 2/C409 and U402 pin 2/C411 have local 100 nF V+
  loops: two short L3 bridges bypass the crowded input-pin corridor, and a
  PWR-layer trunk joins the two local groups. Their GND pads return to L2.
  Both pin-8 **EN inputs** now have F.Cu copper to this local VPOS network;
  EN is an input, not a second supply pin. **Neither the VPOS nor VNEG
  source feed is routed to these local groups**, and the exposed-pad thermal
  path is still open. [TI's OPA1622 guidance](https://www.ti.com/lit/ds/symlink/opa1622.pdf)
  requires a valid EN and close rail bypassing; the local copper alone does
  not establish powered operation.
- U501's local switching, VIN, VPOS/VNEG capacitor and feedback groups are
  routed, and its capacitor/divider/exposed-pad grounds reach the filled L2
  zone. Three bounded **0.20 mm** WSON VIN escapes at pins 12/3/8 measure
  **1.050/0.860/1.146 mm** before the ≥0.8 mm feeder. C510/C511 ground vias
  are **8.160/6.767 mm** from the U501 GND via across L2 by straight via
  spacing. These are not extracted return-current lengths or a switching-noise
  acceptance result; upstream supply and amplifier-rail distribution remain
  open.
  A hand detour moves the B.Cu `5V_ANA_F` feeder away from F.Cu `N5_FBP`:
  projected track overlap fell from **0.1663 to 0 mm²**, and the
  unshielded pad-inclusive projection fell from **0.0861 to 0 mm²**.
  The original power-via antipad remains, but the feeder no longer crosses
  FBP there. The U501 pin-3 VIN→C507 route grew from **5.859 to 6.014 mm**,
  within its **6.1 mm** checker bound. Switching-return impedance, noise
  and regulation stability still need extraction and measurement.
- All 12 U609/U610 timer signal branches pass the named-pad **≤8 mm** screen
  without timer-net vias. U609 LP C/Q/R measures **6.089/5.340/4.943 mm**;
  LN measures **6.038/5.814/6.685 mm**. U610 LP C/Q/R measures
  **6.442/7.607/1.789 mm**; LN measures **7.177/7.712/7.787 mm**.
  C631/C632/C633/C634 GND returns reach L2 in **3.580/3.656/2.650/2.650 mm**.
  C635/C636 U609 VPOS/VNEG bypasses connect through 11 new vias (six GND,
  three VPOS, two VNEG); upstream rail feeds and U609 VT/control escapes
  remain open. R921 was hand-moved to **(95.15, 112.61)** and its LN_L and
  VPOS escapes redrawn. KiCad's native `fromTo` length for U609.10→R921.2 is
  **7.885 mm**; the named-pad shortest-copper audit reports **6.685 mm** because
  KiCad's rule includes **1.20 mm** of the sibling C632 branch. Both pass 8 mm.
  R921 body gaps are **1.167 mm** to U609 and **0.582 mm** to Q624; its
  courtyard gaps are only **0.055/0.092 mm**, so actual body fit stays on the
  G-3 overlay list. U605 and R675/R676/R679/R677 shifted left **1.2 mm**,
  while C625 moved beside R666;
  this clears six measured 5 mm I²S/protection gaps. C638 uses a two-via L3
  VNEG bridge to keep the timer corridors clear. C636 has a pair-specific
  **0.60 mm** side-courtyard gap to C631/C632. All
  four film-cap north/south solder approaches pass at ≥**1.5 mm** (minimum
  **3.045 mm**) per the [film solder-access audit](INTEGRATED_AUDIO_FILM_SOLDER_ACCESS_AUDIT.json).

After close visual review, 33 explicit 45° mitres replace sharp turns on
the amplifier inputs, clock monitor, power rail and headphone trunks. Two
short 0.4/0.3 mm doglegs were redrawn as diagonals, and two later I/V/VREF
corners were chamfered. The [integrated checker](check_integrated_audio_study.py)
rejects exact/near-90° bends and 80–100° free-copper elbows; both counts are
**zero**. It treats pad-centred exits and electrical T/cross junctions
separately from free-track bends.

The manual record now contains **138 explicit footprint moves, eight removed
source copper items and 821 added copper items** relative to the functional-ECO
board. The current board keeps 544 footprints, 250 named nets and 848 track/via
items (143 vias) and reports **zero KiCad custom-rule DRC violations**, zero
footprint bounding-box overlaps and zero classified JLC spacing findings.
The board also has zero exact/near-90° bends. The U609/U610 timer and
film-cap geometry gates pass; JLC review for 45 unfilled near-pad sites
remains open. All populated pad nets match the schematic. DRC reports zero
violations and 499 unconnected items; the full
`pcbnew` ratsnest counts **866**. These are partial-copper checks, not
functional or PCBA acceptance.
The manual C622 update places the capacitor at **(108.65, 105.50, 0°)** and routes U604.8→C622.1 on 0.30 mm F.Cu for **4.615 mm**, then C622.2 to a Ø0.7/0.3 mm GND via at **(110.15, 105.50)** for **1.020 mm**. Continuous saved L2 GND supports both paths; the global 3V3D feed remains open.
[Machine-readable summary](INTEGRATED_AUDIO_SUMMARY.json),
[trace/impedance sensitivity](INTEGRATED_AUDIO_TRACE_BUDGET.json) and the
[review guide](PLACEMENT_REVIEW_GUIDE.md) give the reproducible details.

## Output impedance remains a measured gate

The trace audit follows the least-resistance connected copper from each
amplifier output through its 0 Ω link and relay to each jack pad. It uses
the v1.1 calculation package's **0.551 mΩ per square at 50 °C for 35 µm
copper**. Its illustrative via term uses a 1.6 mm board, 0.20 mm drill and
20 µm hole-wall plating; [JLCPCB describes roughly 20–25 µm plating](https://jlcpcb.com/blog/pcb-plating-thickness),
not an order-specific guaranteed resistance. R-15's existing 0.383 Ω
balanced figure includes 20 mΩ assumed trace resistance and two 50 mΩ
0 Ω links. The audit replaces the trace term with study copper/vias and
uses the [review-only Yageo output-link ECO](OUTPUT_LINK_BOM_ECO.md),
whose manufacturer maximum is 1 mΩ per link.

| 4.4 mm channel | Worst pad path, 1 kHz planning estimate | 20 kHz model sensitivity if the same 0.5 Ω limit applies |
| --- | ---: | ---: |
| Left | **0.3862 Ω** | **0.3990 Ω** |
| Right | **0.3737 Ω** | **0.3864 Ω** |

The 20 kHz sensitivity substitutes the calculation package's modelled
OPA1622 closed-loop output impedance of 6.7 mΩ/leg for its 1 kHz value of
0.33 mΩ/leg. The left 20 kHz candidate estimate leaves **101.0 mΩ** in
the same conditional model. If the same 0.5 Ω criterion applies at 20 kHz,
the former 50 mΩ-per-link allowance would put this copper at 0.4970 Ω,
leaving only 3 mΩ in the model;
this is a sensitivity, not a measurement. The 3.5 mm candidate signal-only lower bounds are 0.2255 Ω (L)
and 0.2188 Ω (R); the sleeve return
has not been extracted. All these figures inherit the owner's **50 mΩ per
jack contact engineering estimate**, which has no maker maximum. They omit
contact variation, plated-via variation, connector solder joints, AC
parasitics and loaded measurements. **R-15 is not signed off.** Measure output
impedance at both jacks over the intended audio band and recalculate the
fully routed return before accepting the ≤0.5 Ω requirement.

The nearest 100 nF **pad-distance lower bounds** are now **2.72/3.08 mm**
from U401/U402 V+ pin 2, **2.91 mm** from either V− pin 4 and **3.00 mm**
from either exposed pad. [The checker records all six distances](INTEGRATED_AUDIO_SUMMARY.json).
These are pad distances, not extracted supply-and-return loop lengths. The
L3 V+ bridges use tented Ø0.60/0.20 mm vias close to small input-shunt
footprints; nominal via-to-input copper clearance is only about 0.23 mm
against the 0.20 mm project floor. Obtain JLC DFM/mask acceptance before
freezing this arrangement. Main V+/V− source feeds, EP thermal routing and
measured bypass impedance remain on hold.
[TI's OPA1622 layout guidance](https://www.ti.com/lit/ds/symlink/opa1622.pdf)
calls for 0.1 µF low-ESR capacitors close to the positive and negative
supply pins and connects the exposed pad to the **most negative supply**.
The present local GND pin vias do not complete either supply loop or the
exposed-pad thermal/electrical connection.

## Required before routing or fabrication release

1. **Extract the I/V path and finish amplifier supplies.** The four DAC→I/V
   routes, eight I/V→first-T feeds, I/V Rf/Cf and central VREF have copper.
   Check summing-node capacitance, the true 3D feedback/return loop, the
   **1.9426 mm DACL feedback L2 gap**, VREF noise and the long right-side
   cross-layer feeds; test I/V stability over load and process corners.
   Route VPOS and VNEG from their sources through
   bulk and local bypass to the amplifier groups, establish the exposed-pad
   thermal path, then extract supply-and-return impedance and test amplifier
   stability and THD+N under cable/load corners. A clean partial DRC does
   not establish powered operation.
2. **Design the L3/L4 audio return.** Reserve quiet reference copper under
   the four L4 outputs, keep L2 continuous, keep switching and digital power
   away from their return currents, and add/check local stitching. Extract
   L/R coupling and shared-return impedance; measure loaded crosstalk and
   EMI. The current single L2 polygon is necessary but not sufficient.
3. **Close connector and manufacturing gates.** Verify relay/jack solder-iron
   access, J101/J702 slot soldering and board-edge process, J701 1:1 G-3
   overlay, all G-4 polarities, JLC order DFM, final BOM rotations and system
   IEC ESD. Inspect C423/C426's 0.150–0.194 mm courtyard gaps, the tight
   C437/J701/K602 region and via-to-small-capacitor mask/tenting in the JLC
   order preview.
4. **Complete the other circuit routes and functional holds.** USB, remaining
   I²S branches and controls, U609 VT/control escapes, upstream rail feeds,
   other protection routes and most of the 866 ratsnest gaps remain.
   System ESD, EMI and audio tests are also open.
   F01 all-rate post-CPLD capture and DAC-side WS fault coverage are unproven;
   F02 readback corners, F03 attach current and F04 ESD need validation.

For zoomable layer plots, DRC and a GLB 3D view, use the [CLI visual review
workflow](PCB_CLI_VISUAL_REVIEW.md):

```sh
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-integrated-audio-review \
  hardware/DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb
```

Inspect F.Cu, mirrored B.Cu, the filled L2 plot and 3D view together.
Report any problem by reference, pad, layer and PCB x/y coordinate.
