# Integrated amplifier-to-jack route study — 28 September 2026

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
  vias per leg. `LEG_*` and `JACK_*` remain on L1 with no vias.
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

The exact board reports **zero KiCad custom-rule DRC violations**, zero
footprint bounding-box overlaps, zero classified JLC package/edge proxy
findings and no via-ring failure. All populated pad nets match the schematic.
The exported KiCad DRC still lists 499 missing links; the full `pcbnew`
ratsnest counts **1,101**. These are partial-copper checks, not functional or
PCBA acceptance. [Machine-readable summary](INTEGRATED_AUDIO_SUMMARY.json),
[trace/impedance sensitivity](INTEGRATED_AUDIO_TRACE_BUDGET.json) and the
[review guide](PLACEMENT_REVIEW_GUIDE.md) give the reproducible details.

## Audio margin remains thin

The trace audit follows the least-resistance connected copper from each
amplifier output through its 0 Ω link and relay to each jack pad. It uses
the v1.1 calculation package's **0.551 mΩ per square at 50 °C for 35 µm
copper**. Its illustrative via term uses a 1.6 mm board, 0.20 mm drill and
20 µm hole-wall plating; [JLCPCB describes roughly 20–25 µm plating](https://jlcpcb.com/blog/pcb-plating-thickness),
not an order-specific guaranteed resistance. R-15's existing 0.383 Ω
balanced figure includes 20 mΩ assumed trace resistance; the audit replaces
that term with the study copper and adds the illustrative vias.

| 4.4 mm channel | Worst pad path, 1 kHz planning estimate | 20 kHz model sensitivity if the same 0.5 Ω limit applies |
| --- | ---: | ---: |
| Left | **0.4800 Ω** | **0.4928 Ω** |
| Right | **0.4676 Ω** | **0.4803 Ω** |

The 20 kHz sensitivity substitutes the calculation package's modelled
OPA1622 closed-loop output impedance of 6.7 mΩ/leg for its 1 kHz value of
0.33 mΩ/leg. The left 20 kHz estimate leaves only **7.2 mΩ**. The 3.5 mm
signal-only lower bounds are 0.2755 Ω (L) and 0.2671 Ω (R); the sleeve return
has not been extracted. All these figures inherit the owner's **50 mΩ per
jack contact engineering estimate**, which has no maker maximum. They omit
contact variation, plated-via variation, connector solder joints, AC
parasitics and loaded measurements. **R-15 is not signed off.** Measure output
impedance at both jacks over the intended audio band and recalculate the
fully routed return before accepting the ≤0.5 Ω requirement.

## Required before this placement can replace the primary

1. **Finish each amplifier's input/T and supply subcircuit.** Rf/Cf and input
   shunts are local, but several T-network, 100 nF bypass and bulk rail nets
   remain open or remote. Route VPOS/VNEG, the exposed VNEG pads, local bypass
   supply-and-return loops and thermal copper; then extract and test
   amplifier stability and THD+N under cable/load corners. A clean partial
   DRC cannot establish that the amplifiers will power or remain stable.
2. **Design the L3/L4 audio return.** Reserve quiet reference copper under
   the four L4 outputs, keep L2 continuous, keep switching and digital power
   away from their return currents, and add/check local stitching. Extract
   L/R coupling and shared-return impedance; measure loaded crosstalk and
   EMI. The current single L2 polygon is necessary but not sufficient.
3. **Close connector and manufacturing gates.** Verify relay/jack solder-iron
   access, J101/J702 slot soldering and board-edge process, J701 1:1 G-3
   overlay, all G-4 polarities, JLC order DFM, final BOM rotations and system
   IEC ESD. Via-to-small-capacitor mask/tenting needs the order preview.
4. **Complete the other circuit routes and functional holds.** USB, I²S,
   rails, protection timers/control and most of the 1,101 ratsnest gaps remain.
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
