# PCB 3D model review

The current **120 × 100 mm** schematic-aligned board is
`DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb`. Open it in KiCad 10 and
choose **View → 3D Viewer**. GitLab CI exports
`DAC_HPA_INTEGRATED_AUDIO_REVIEW.glb` for this candidate; the functional-ECO,
output-macro, macro-study and primary GLBs are earlier comparisons. A separate
[discharge fit option](DAC_HPA_120x100_DISCHARGE_FIT_OPTION_ONLY.kicad_pcb)
exports `DAC_HPA_DISCHARGE_FIT_OPTION_REVIEW.glb` with three provisional 2512
resistor bodies; it is not schematic/BOM aligned. Its GLB uses the bundled
KiCad stock 2512 STEP, while the separately retained [exact JLC R2512 STEP](EASYEDA_MODELS/R2512_L6.3-W3.2-H0.6.step)
and [CAD audit](DISCHARGE_JLC_CAD_AUDIT.json) support a later land/model
comparison. The prior
[full-board preview](DAC_HPA_3D_review.png) and [J101 closeup](DAC_HPA_J101_3D_detail.png)
show the historical primary after the USB-C model alignment correction.

The [manual macro-placement study](MACRO_PLACEMENT_REVIEW.md) has the older 536-footprint population. The [functional-ECO placement baseline](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb) added D707/D708 with the existing SOD-523 model and U621 with a new exact-JLC C507231 SC70-6 body; the integrated board retains that 544-footprint population. These models remain subject to G-3 fit and JLC order checks.

## Coverage and sources

`audit_3d_models.py` checks model paths, file headers, and the JLC file hashes.
On the current integrated-audio board, **478 component bodies resolve**
(474 STEP and four VRML), while 66 copper-only items intentionally have no
model. Of the 478, 385 use KiCad stock models and 93 use project-local files.
The five historical review boards each have 536 footprints: **470 component bodies resolve**
(466 STEP and four VRML), while 66 copper-only items intentionally have no
model (53 test pads, seven fiducials, four mounting holes, and J201/J202 debug
pads). Of the 470, 380 use KiCad 10 stock models and 90 use files kept in this
project. The 90 project-file instances are 82 instances of 30 JLC package
models, four Toshiba relays, and four Panasonic body envelopes. The 380 stock
instances use only 11 distinct KiCad STEP files; unchanged copies are bundled
in `KICAD_STOCK_MODELS` for headless CI, with KiCad's license and hashes. The
fit option adds a twelfth distinct stock STEP shape for 2512 resistors; its
CI artifact includes the 3D audit, which resolves 478 populated bodies.

| Parts | 3D source and alignment | Confidence for 3D inspection |
| --- | --- | --- |
| J701, J702 and the imported JLC footprints | STEP from the component's EasyEDA/JLC CAD entry. The 31 files, source URLs, LCSC codes, conversions, and SHA-256 hashes are in `EASYEDA_MODELS/MODEL_SOURCES.json`. | Source package bodies; the modified jack copper and slots still require G-3 sample overlay and JLC DFM. |
| U621 | Exact C507231 JLC SC70-6 body and native pad geometry, normalized to STEP. | Model and pads match the JLC CAD entry, but TI's DCK example land has a wider pad-row span. Resolve the physical G-3/JLC DFM discrepancy before order. |
| J101 | KiCad 10 `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step`, with −1.295 mm local Y offset for the custom footprint origin. A J101-only STEP probe puts the shell front at x = 40.03 mm beside the x = 40.00 mm board edge. | Exact connector family body; visually aligned in KiCad 3D Viewer. The footprint and solder lands remain at the GCT PCB-edge datum. G-3 physical overlay still open. |
| K601–K604 | User-supplied Ultra Librarian `TLP3545A_LF1__TOS.step`, stored as `DAC_HPA_3D/TLP3545A_LF1_UltraLibrarian.step`. Local Z rotation is −90° to align the model's pad-1 side to the custom LF1 footprint. | Exact Toshiba LF1 body; visually aligned in KiCad 3D Viewer. Source STEP SHA-256: `3534740be81c87bf067b67926e57872bb9693455f3bbc5ab0c75e69f7ab00c74`. |
| X201–X203 | KiCad stock `Crystal_SMD_2520-4Pin_2.5x2.0mm.step`. | 2520 four-pad package approximation; maker-exact oscillator bodies remain desirable. |
| C631–C634 | `DAC_HPA_3D/ECHU1H224GX9_envelope_only.wrl`, a 6.0 × 4.1 × 2.8 mm Panasonic body envelope. | Review-only shape without terminals. It renders in KiCad 3D Viewer but is omitted from non-mesh STEP export. Maker STEP remains desirable. |
| D102 and other stock-footprint parts | KiCad 10 standard package STEP models. | Package shapes for 3D inspection; confirm exact part dimensions at G-3. |

The original user-downloaded Ultra Librarian ZIP is not required by KiCad after
extracting its STEP. Its source ZIP SHA-256 is
`9c409738e9fb11241a2306db80b8167d6a3af8ac0be0cab408640a1d2ce81f1d`.
`fetch_jlc_3d_models.py` can restore the original 30 JLC STEP files from the saved
`JLC_Source/JLC_DAC_HPA.elibz` identifiers when network access is available;
it does not move footprints. `attach_3d_models.py` adds the twelve custom
model links to the five board snapshots if absent. GitLab CI sets
`KICAD10_3DMODEL_DIR` to the bundled stock library so its GLB includes the
same package shapes as the KiCad desktop installation, including the option's
new 2512 model.

## Limits

The 3D view verifies that model files load and permits visual package and
clearance review. It does **not** prove pad numbering, solder-joint geometry,
height tolerance, connector mating, or routability. G-3 overlays, the JLCPCB
DFM review, and routing/ESD gates in `PRELAYOUT_GATES.md` remain open. The
current integrated-audio board is a partial-route review, not a PCBA
release package.

KiCad's GLB exporter currently skips the four VRML film-capacitor envelopes;
use the KiCad 3D Viewer to see those bodies. An earlier primary-board GLB was
checked with Assimp as a valid 480-node, 6,042-mesh model after correcting
J101's offset.
