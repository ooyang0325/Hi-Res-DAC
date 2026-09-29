# Visually inspect the PCB from the command line

Use these commands on the Git commit under review. The script defaults to the earlier 120 × 100 mm functional-ECO baseline; **pass the integrated board as its second argument** to inspect the current routing study. It writes views to your chosen output directory without moving footprints or regenerating the board. KiCad 10 and its `kicad-cli` are required. The project includes the bundled stock, JLC, Toshiba and custom model files needed for 3D viewing.

## One-command export

From the repository root on Linux or any system where `kicad-cli` is on `PATH`:

```sh
bash hardware/make_review_views.sh /tmp/dac-hpa-review
```

On macOS with KiCad installed in `/Applications/KiCad`:

```sh
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-hpa-review
```

The script sets `KICAD10_3DMODEL_DIR` to the bundled stock models unless you already set it. Each SVG is plotted at board-area scale without a drawing-sheet border. The directory contains:

To inspect the earlier 536-footprint macro placement for comparison, pass its PCB as the second argument:

```sh
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-hpa-macro-review \
  hardware/DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb
```

To inspect the newer manual four-channel output route study, pass its separate
board as the second argument. Compare the F.Cu, B.Cu and L2 plots at the same
zoom; the L4 audio return and relay-to-jack routing remain under review:

```sh
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-hpa-output-review \
  hardware/DAC_HPA_120x100_OUTPUT_MACRO_STUDY_ONLY.kicad_pcb
```

For the current DAC-through-jack and U501 local route candidate, use the
integrated board. It shows the DAC/CPLD clock and I²S paths measured in the
[DAC/core checkpoint](DAC_CORE_ROUTE_STUDY.md), all four DAC→I/V inputs, eight
I/V→first-T feeds, four amplifier-to-jack paths, VREF and local U501 copper.
Most other nets remain unrouted:

```sh
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-hpa-integrated-review \
  hardware/DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb
```

The default file is the `hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb` capture baseline. The integrated board is the current audio-routing study. The older primary and generated J702 two-TVS fit trial predate the captured functional ECO; use them only for geometry comparison. The current board has 544 footprints, 250 named nets, 756 total track/via items, zero DRC violations, 499 DRC unconnected items and 896 full ratsnest links. The [integrated summary](INTEGRATED_AUDIO_SUMMARY.json) records the audio checks and holds; the [DAC/core route audit](DAC_CORE_ROUTE_AUDIT.json) records clock/I²S and local power measurements, seven filled/capped U202/U301 EP vias, and 35 local GND pads to L2. The separate [via-pad process audit](INTEGRATED_AUDIO_VIA_PAD_PROCESS_AUDIT.json) finds 45 unfilled via-to-SMT-pad sites within 0.35 mm for JLC review. U401/U402 output-amplifier EP thermal routes remain open. DRC is a partial-board check; full routing, system ESD, EMI and audio tests remain open.

On the integrated plots, zoom to U202/U301 at x = 78–95 mm, y = 62–85 mm to inspect BCLK/LRCLK/SDATA, MCLK, FAM_CLK, L3 supply feeders, the two filled/capped U202 EP vias and five U301 EP vias. Then zoom to U301/U403/U404 at PCB x = 91–104 mm, y = 70–88 mm. Compare all four F.Cu DAC inputs with filled L2: the checker found direct L2 beneath the routes at 0.01 mm samples and offsets 0, ±0.05, ±0.10 mm, while U403→C417 feedback still has a **1.9426 mm** centreline gap near an I/V-output via. Follow the right I/V feeds across L3/L4 toward the T cells, including R411/R413 at **27.289/41.648 mm**, and check the L3 VPOS crossing near x = 115–121 mm, y = 74–76 mm. Check the U303→DAC 1V3 PWR route (25.393 mm, two vias), U302 capacitor paths and U202 local bypass routes. Zoom to U501 at x = 68–77 mm, y = 128–137 mm: its B.Cu `5V_ANA_F` feeder now detours around F.Cu `N5_FBP`, but the original via antipad remains. Inspect the three VIN escapes and capacitor returns. The via-pad audit flags 45 nearby unfilled via sites for JLC mask/process review. The copper audit rejects free-track bends within 80–100°; joins at component pads and straight-through T/cross branches are classified separately. Plots do not extract return impedance or coupling.

| File | What to inspect |
| --- | --- |
| `01_body_courtyard.svg` | F.Fab bodies, F.CrtYd and board outline. Zoom in on J101/J702 edges, J701 top-side solder access, K601–K604 iron access, dense U301/U403/U404 and timer groups. Check that courtyard clearances leave routing channels. |
| `02_top_copper.svg` | F.Cu pads and traces. The current board contains **756 total track/via items** across layers, so this is not an F.Cu segment count. Follow D701–D704 to J701, D707/D708 to J702, and X201→R203→TP711→U301. On the integrated board also inspect U202→U301 clock/I²S paths, the U303→DAC 1V3 trunk, all DAC/I/V inputs, local T cells, jack branches and J101's still-unrouted fine-pitch escape. |
| `03_l2_ground.svg` | Saved filled In1.Cu/L2 GND zone and outline. Look for continuous copper under future USB, clocks, I²S and analog paths; on the integrated board, inspect sampled DAC-input support and the DACL feedback gap near the I/V-output via. Refill the zone in KiCad and recheck after routes, holes and stitching vias are added. |
| `10_l3_power.svg` | In2.Cu/L3 power copper and outline. On the integrated board, inspect the local VPOS bridge crossing the two right I/V L4 feeds around PCB x = 115–121 mm, y = 74–76 mm. Compare it with `07_bottom_copper.svg`; this projected overlap is not extracted coupling. |
| `04_top_mask.svg` | Top mask openings around fine-pitch parts and the plated jack/USB slots. Compare to copper to spot potential slivers or unexpected exposed metal. |
| `05_top_paste.svg` | Top paste apertures. J101 shell stakes S1–S4 and J702 slots 1/2 currently have **no paste aperture**; this is a JLCPCB process hold, not an accidental omission to fix from the plot alone. |
| `06_top_silkscreen.svg` | Top legend and polarity/pin-1 marks. Inspect D102, D705/D706, U202, X201–X203, jacks and dense assembly regions. |
| `07_bottom_copper.svg` | Mirrored B.Cu view, useful for checking underside hand-solder access, the U501 feeder detour and later return routes. |
| `08_board_3d.glb` | Portable 3D assembly for an external GLB viewer; inspect connector projection and component bodies/heights. The four C631–C634 VRML body envelopes do not appear in the GLB; they do appear in KiCad's 3D Viewer. |
| `09_drc.json` | KiCad error/warning DRC report. The current partial board has zero DRC violations and 499 DRC unconnected items; this does not mean all nets are routed. The full `pcbnew` ratsnest is **1,144** on the default baseline and **896** on the current integrated board. Keep these counts distinct. |

## Open or rasterize the output

SVG is vector artwork, so zoom in without losing pad/courtyard detail. From a terminal, open the output directory or one plot with `open /tmp/dac-hpa-review/01_body_courtyard.svg` on macOS or `xdg-open /tmp/dac-hpa-review/01_body_courtyard.svg` on Linux. Open `08_board_3d.glb` in a GLB-capable 3D viewer. The checked-in [functional-ECO baseline PNG](DAC_HPA_FUNCTIONAL_ECO_PLACEMENT_REVIEW.png) is a quick comparison; the [older 3D whole-board image](DAC_HPA_3D_review.png) and [J101 closeup](DAC_HPA_J101_3D_detail.png) predate the ECO but still show the connector model alignment. Export the integrated board for the current view.

For a PNG that can be attached to a review finding, if `rsvg-convert` is installed:

```sh
rsvg-convert -w 2400 /tmp/dac-hpa-review/01_body_courtyard.svg \
  -o /tmp/dac-hpa-review/01_body_courtyard.png
```

For four full-resolution placement quadrants, rasterize wider and tile with ImageMagick:

```sh
rsvg-convert -w 4800 /tmp/dac-hpa-review/01_body_courtyard.svg \
  -o /tmp/dac-hpa-review/placement_4800.png
magick /tmp/dac-hpa-review/placement_4800.png -crop 2x2@ +repage \
  /tmp/dac-hpa-review/placement_tile_%d.png
```

Tiles 0/1 are the upper left/right and 2/3 the lower left/right. Use the same approach on copper, mask or paste when a crowded area needs a close inspection. Open an individual tile or attach it to a finding with its original SVG layer and PCB coordinate.

For terminal-only image display, `chafa /tmp/dac-hpa-review/01_body_courtyard.png` is optional if `chafa` is installed. At fine pitch, use the SVG/PNG at full resolution and KiCad pad measurements; terminal image characters cannot resolve a 0.1 mm overlap or solder-mask bridge. A command-line 3D geometry sanity check is `assimp info /tmp/dac-hpa-review/08_board_3d.glb` if Assimp is installed, but mesh counts do not prove model alignment.

Summarize the exported DRC from the terminal without confusing a clean partial board with a routed one. The separate [layout summary](FUNCTIONAL_ECO_LAYOUT_SUMMARY.json) gives the full ratsnest count:

```sh
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("violations:",len(d["violations"]),"unconnected:",len(d["unconnected_items"]))' \
  /tmp/dac-hpa-review/09_drc.json
```

The provisional 4.2 mm J701/J702 TVS limits need a **separate named-pad
copper-path check** when paired jack contacts and relay branches are routed.
Use the KiCad Python that includes `pcbnew` (`python3` in the GitLab KiCad
image, or the bundled interpreter on macOS):

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
  hardware/audit_local_tvs_paths.py \
  hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb
```

Pass the output-study PCB path instead to check that board. The script finds
the actual shortest L1 path between each named jack and TVS pad; a generic
KiCad net `length` check can count extra branches and report a false excess.

## What to measure after looking

1. Mark suspicious locations by reference and **PCB x/y in mm**, side and layer in [Review findings template](REVIEW_FINDINGS_TEMPLATE.md). Use KiCad's PCB Editor for exact coordinates/pad numbers; plots are a fast visual screen.
2. Compare the SVGs with the actual board and [placement review guide](PLACEMENT_REVIEW_GUIDE.md). A 2D plot cannot prove simultaneous headphone routes with 0.25 mm VSON escapes, 90 Ω USB impedance, the true 3D I/V feedback loop, jack return quality or U501 switching-noise isolation; the <5 mm² I/V result is a projected centreline screen.
3. For physical fit, print [G-3 overlay sheets](G3_OVERLAY_INDEX.md) at 100% and verify the 10 mm bars, then check real samples or calibrated CAD. The CLI SVGs and GLB do not close G-3 or G-4.

Run the script again after any PCB edit and compare the same view names between revisions. Keep the exported files with the reviewed commit SHA; they are inspection aids, not Gerbers, stencil files or PCBA order data.
