# Four-channel output macro route study — 28 September 2026

**Status: intermediate review study, not the primary board or PCBA order data.** The newer [integrated-audio study](INTEGRATED_AUDIO_ROUTE_STUDY.md) carries these amplifier paths through J701/J702 and is the current audio-routing comparison. Open
[the separate KiCad board](DAC_HPA_120x100_OUTPUT_MACRO_STUDY_ONLY.kicad_pcb)
alongside the [current functional-ECO board](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb).
Both have 544 footprints and the same 250 named nets. This study moves 22
footprints by explicit hand-selected coordinates in
[`manual_output_macro_study.py`](manual_output_macro_study.py); it changes no
schematic connection, component value, jack, relay footprint or board outline.

## What was made drawable together

U401 and U402 are side by side at 270°, with their input pins facing the I/V
stage. Each channel's Rf/Cf pair is on the output side. R417–R420 are placed
near their relay input contacts. Four 1.0 mm L1 `LEG_*` paths join the links
to K601–K604 pad 4. The corresponding amplifier-output nets also reach each
link, and all four Rf/Cf pairs connect to the intended output and inverting
input pads. The [checker](OUTPUT_MACRO_STUDY_SUMMARY.json) verifies those pad
groups from KiCad's physical copper connectivity, not just net names.

The centreline area bounded by each output/inverting-input route through its
feedback capacitor is **4.833 mm²**, below the provisional 5 mm² screen. This
is a geometry estimate; pad current distribution, loop inductance, capacitance
and amplifier stability still need extraction and a powered test. The first
0.932 mm leaving each VSON output is 0.25 mm wide; its headphone-current
branch then widens to 0.5 mm on L1 and 1.0 mm on L4. The branch starts at the
pad escape, so the 0.20 mm Rf/Cf trace does not carry the load current.

LP, LN and RN use two Ø0.60/0.20 mm signal vias apiece and an L4 trunk. RP
stays on L1. The L4 tracks avoid J701's underside keepout. The saved L2 GND
fill remains one connected polygon after the six new signal-via clearances.
The L3 reference under the L4 paths, local GND stitching, coupling to power
planes and extracted return-current path have **not** been designed or
qualified. These are electrical holds, despite a zero-error geometry DRC.

| Leg | Load path to relay pad 4 | Trace resistance estimate at 50 °C |
| --- | --- | ---: |
| LP | U401 → R417 → K601 | 21.22 mΩ |
| LN | U401 → R418 → K602 | 18.20 mΩ |
| RP | U402 → R419 → K603 | 33.94 mΩ |
| RN | U402 → R420 → K604 | 21.16 mΩ |

The resistance screen uses the v1.1 calculation package's **0.551 mΩ per
square for 35 µm copper at 50 °C** and the actual segment lengths and widths.
It excludes vias, link/relay resistance and all relay-to-jack copper. The
original R-15 estimate allocated **20 mΩ of trace resistance to a balanced
pair**. This trial already uses 39.42 mΩ for L+/L− and 55.10 mΩ for R+/R−
before jack branches. The published 0.383 Ω balanced output-impedance
estimate must therefore be recalculated from the complete routed geometry;
this study does **not** establish the ≤0.5 Ω requirement. The assumed 50 mΩ
per jack contact remains an engineering estimate pending measurement.

## Checks passed, and what remains

The saved board passes KiCad 10 DRC with its matching `.kicad_dru`: **zero
violations** on partial copper. The placement audit reports zero bounding-box
overlaps and zero sensitive-to-clock pad gaps. The conservative JLC package
spacing and board-edge proxies have zero classified findings; 16 placed
references still need individual process review. The slot/via ring audit has
no failure. The exported DRC lists 499 missing links; the full `pcbnew`
ratsnest counts **1,120**, so most of the board remains unrouted.
The separate [local TVS copper audit](OUTPUT_MACRO_LOCAL_TVS_AUDIT.json)
checks all six provisional ≤4.2 mm named-pad paths. It remains valid as
paired contacts and relay branches are added, when a generic net-length
constraint can count the wrong branch.

Before replacing the primary placement, draw these networks **on the same
candidate** and repeat the electrical and manufacturing checks:

1. Complete all four relay outputs to both J701 and J702, including paired
   contacts, local TVS branches, sleeves and top-side solder access. The
   K602 `JACK_LN` escape and K604 `LEG_RN` approach are a likely planar
   conflict in the present two-row relay arrangement. A lower single-row
   relay arrangement is an untested manual alternative.
2. Regroup and route each amplifier's input/T network, 100 nF bypass, bulk
   supply capacitors, VREF and ground vias. Some of these remain remote in
   this study, so feedback geometry alone is not an amplifier sign-off.
3. Reserve and inspect a quiet L3/L4 return corridor for the three L4 audio
   outputs, then extract their conductor/via impedance, coupling and thermal
   effect. Keep L2 continuous. Recalculate R-15 at both jacks and check
   loaded crosstalk, output stability and EMI with the actual copper.
4. Complete USB, I²S, power and protection routing, repeat physical G-3/G-4
   and JLC order-specific DFM, and close the F01–F04 functional holds.

To inspect the layers and 3D view from the command line, use the [CLI visual
workflow](PCB_CLI_VISUAL_REVIEW.md) with this board as its second argument:

```sh
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-output-macro-review \
  hardware/DAC_HPA_120x100_OUTPUT_MACRO_STUDY_ONLY.kicad_pcb
```

Inspect `02_top_copper.svg`, `07_bottom_copper.svg`, `03_l2_ground.svg` and
`08_board_3d.glb` together. The [review guide](PLACEMENT_REVIEW_GUIDE.md)
explains how to report a coordinate, layer and reference for any route blocker.
