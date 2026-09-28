# Integrated amplifier-to-jack route study — 29 September 2026

**Use this as the newest audio-routing review candidate, not as order data.**
The editable [KiCad board](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb)
keeps the 120 × 100 mm four-layer outline, 544 footprints, 250 named nets and
the v1.1-ECO1 schematic pad map. Every placement and waypoint in this trial
was chosen manually; no placement or routing search was run. Component values
and the electrical schematic did not change.

## What this trial closes geometrically

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
  R444 and C433 were rotated 180° to avoid T/ground crossings. These are
  local connections: **U403/U404 I/V outputs do not yet feed the first T
  resistors**, so the DAC-to-amplifier signal path is still open.
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

After close visual review, 33 explicit 45° mitres replace the sharp
two-segment turns on the amplifier inputs, clock monitor, power rail and
headphone trunks. Two short 0.4/0.3 mm doglegs were redrawn directly as
diagonals. The [integrated checker](check_integrated_audio_study.py) now
rejects any remaining two-segment 90° track bend; this board has **zero**.
Its geometry audit treats T junctions and pad entries separately from bends.

The manual record now contains **54 explicit footprint moves, four replaced
source tracks and 250 added copper items** relative to the functional-ECO
board. The exact board keeps
544 footprints and 250 named nets and reports **zero KiCad custom-rule DRC
violations**, zero footprint bounding-box overlaps, zero classified JLC package/edge proxy
findings and no via-ring failure. All populated pad nets match the schematic.
The exported KiCad DRC still lists 499 missing links; the full `pcbnew`
ratsnest counts **1,049**, down 40 from the prior integrated checkpoint. These
are partial-copper checks, not functional or
PCBA acceptance. [Machine-readable summary](INTEGRATED_AUDIO_SUMMARY.json),
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

## Required before this placement can replace the primary

1. **Finish the upstream I/V signal path and amplifier supplies.** The eight
   local T triplets, four amplifier input shunts, Rf/Cf, local 100 nF V+/V−
   links and both EN ties have copper. Route U403/U404 outputs into the first
   T resistors, then finish the DAC→I/V inputs, I/V feedback and bypass
   loops. Route VPOS and VNEG from their sources through bulk and local
   bypass to the amplifier groups, establish the EP thermal path, then
   extract supply-and-return loop impedance and test amplifier stability
   and THD+N under cable/load corners. A clean partial DRC cannot establish
   a complete audio path or powered operation.
2. **Design the L3/L4 audio return.** Reserve quiet reference copper under
   the four L4 outputs, keep L2 continuous, keep switching and digital power
   away from their return currents, and add/check local stitching. Extract
   L/R coupling and shared-return impedance; measure loaded crosstalk and
   EMI. The current single L2 polygon is necessary but not sufficient.
3. **Close connector and manufacturing gates.** Verify relay/jack solder-iron
   access, J101/J702 slot soldering and board-edge process, J701 1:1 G-3
   overlay, all G-4 polarities, JLC order DFM, final BOM rotations and system
   IEC ESD. Inspect the tight C437/J701/K602 region and via-to-small-capacitor
   mask/tenting in the JLC order preview.
4. **Complete the other circuit routes and functional holds.** USB, I²S,
   rails, protection timers/control and most of the 1,049 ratsnest gaps remain.
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
