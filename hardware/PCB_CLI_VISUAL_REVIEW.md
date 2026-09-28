# Visually inspect the PCB from the command line

Use these commands on the Git commit under review. They **export views from the current 120 × 100 mm functional-ECO PCB candidate** and write only to your chosen output directory. No footprint is moved and no board file is regenerated. KiCad 10 and its `kicad-cli` are required. The project includes the bundled stock, JLC, Toshiba and custom model files needed for 3D viewing.

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

The default current file is `hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb`. The older primary and generated J702 two-TVS fit trial predate the captured functional ECO; use them only for geometry comparison.

| File | What to inspect |
| --- | --- |
| `01_body_courtyard.svg` | F.Fab bodies, F.CrtYd and board outline. Zoom in on J101/J702 edges, J701 top-side solder access, K601–K604 iron access, dense U301/U403/U404 and timer groups. Check that courtyard clearances leave routing channels. |
| `02_top_copper.svg` | F.Cu pads and 28 existing tracks. Follow D701–D704 to J701, D707/D708 to J702, and X201→R203→TP711→U301 with the R227 ground via and R665→U607 branch. The LP main trunk and most other connections remain unrouted. Inspect J101 fine-pitch escape and the four output-leg crossovers. |
| `03_l2_ground.svg` | Saved filled In1.Cu/L2 GND zone and outline. Look for continuous copper under future USB, clocks, I²S, DAC and analog paths. Refill the zone in KiCad and recheck after routes, holes and stitching vias are added. |
| `04_top_mask.svg` | Top mask openings around fine-pitch parts and the plated jack/USB slots. Compare to copper to spot potential slivers or unexpected exposed metal. |
| `05_top_paste.svg` | Top paste apertures. J101 shell stakes S1–S4 and J702 slots 1/2 currently have **no paste aperture**; this is a JLCPCB process hold, not an accidental omission to fix from the plot alone. |
| `06_top_silkscreen.svg` | Top legend and polarity/pin-1 marks. Inspect D102, D705/D706, U202, X201–X203, jacks and dense assembly regions. |
| `07_bottom_copper.svg` | Mirrored B.Cu view, useful for checking underside hand-solder access and later return routes. |
| `08_board_3d.glb` | Portable 3D assembly for an external GLB viewer; inspect connector projection and component bodies/heights. The four C631–C634 VRML body envelopes do not appear in the GLB; they do appear in KiCad's 3D Viewer. |
| `09_drc.json` | KiCad error/warning DRC report. Zero findings on this partial board do not mean all nets are routed. This JSON lists 499 missing links; the full `pcbnew` ratsnest counts 1,144. |

## Open or rasterize the output

SVG is vector artwork, so zoom in without losing pad/courtyard detail. From a terminal, open the output directory or one plot with `open /tmp/dac-hpa-review/01_body_courtyard.svg` on macOS or `xdg-open /tmp/dac-hpa-review/01_body_courtyard.svg` on Linux. Open `08_board_3d.glb` in a GLB-capable 3D viewer. The checked-in [current 2D placement PNG](DAC_HPA_FUNCTIONAL_ECO_PLACEMENT_REVIEW.png) is a quick reference; the [older 3D whole-board image](DAC_HPA_3D_review.png) and [J101 closeup](DAC_HPA_J101_3D_detail.png) predate the ECO but still show the connector model alignment.

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

## What to measure after looking

1. Mark suspicious locations by reference and **PCB x/y in mm**, side and layer in [Review findings template](REVIEW_FINDINGS_TEMPLATE.md). Use KiCad's PCB Editor for exact coordinates/pad numbers; plots are a fast visual screen.
2. Compare the SVGs with the actual board and [placement review guide](PLACEMENT_REVIEW_GUIDE.md). A 2D plot cannot prove simultaneous headphone routes with local 0.25 mm VSON escapes, 90 Ω USB impedance, <5 mm² I/V feedback loops or the jack return.
3. For physical fit, print [G-3 overlay sheets](G3_OVERLAY_INDEX.md) at 100% and verify the 10 mm bars, then check real samples or calibrated CAD. The CLI SVGs and GLB do not close G-3 or G-4.

Run the script again after any PCB edit and compare the same view names between revisions. Keep the exported files with the reviewed commit SHA; they are inspection aids, not Gerbers, stencil files or PCBA order data.
