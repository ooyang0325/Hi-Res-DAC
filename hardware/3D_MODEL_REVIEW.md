# PCB 3D model review

The editable **120 × 100 mm** primary board is `DAC_HPA.kicad_pcb`. Open it in
KiCad 10 and choose **View → 3D Viewer**. The 100 × 80 mm comparison board and
the other saved placement studies have the same model links. GitLab CI also
exports a `DAC_HPA_3D_REVIEW_ONLY.glb` assembly in the review artifact.

## Coverage and sources

`audit_3d_models.py` checks model paths, file headers, and the JLC file hashes
on all five boards. Each has 536 footprints: **470 component bodies resolve**
(466 STEP and four VRML), while 66 copper-only items intentionally have no
model (53 test pads, seven fiducials, four mounting holes, and J201/J202 debug
pads). Of the 470, 380 use KiCad 10 stock models and 90 use files kept in this
project. The 90 project files are 82 instances of 30 JLC package models, four
Toshiba relays, and four Panasonic body envelopes.

| Parts | 3D source and alignment | Confidence for 3D inspection |
| --- | --- | --- |
| J701, J702 and 80 other JLC footprints | STEP from the component's EasyEDA/JLC CAD entry. The 30 files, source URLs, LCSC codes, conversions, and SHA-256 hashes are in `EASYEDA_MODELS/MODEL_SOURCES.json`. | Source package bodies; the modified jack copper and slots still require G-3 sample overlay and JLC DFM. |
| J101 | KiCad 10 `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step`, with −1.295 mm local Y offset for the custom footprint origin. A J101-only STEP probe puts the shell front at x = 40.03 mm beside the x = 40.00 mm board edge. | Exact connector family body; visually aligned in KiCad 3D Viewer. The footprint and solder lands remain at the GCT PCB-edge datum. G-3 physical overlay still open. |
| K601–K604 | User-supplied Ultra Librarian `TLP3545A_LF1__TOS.step`, stored as `DAC_HPA_3D/TLP3545A_LF1_UltraLibrarian.step`. Local Z rotation is −90° to align the model's pad-1 side to the custom LF1 footprint. | Exact Toshiba LF1 body; visually aligned in KiCad 3D Viewer. Source STEP SHA-256: `3534740be81c87bf067b67926e57872bb9693455f3bbc5ab0c75e69f7ab00c74`. |
| X201–X203 | KiCad stock `Crystal_SMD_2520-4Pin_2.5x2.0mm.step`. | 2520 four-pad package approximation; maker-exact oscillator bodies remain desirable. |
| C631–C634 | `DAC_HPA_3D/ECHU1H224GX9_envelope_only.wrl`, a 6.0 × 4.1 × 2.8 mm Panasonic body envelope. | Review-only shape without terminals. It renders in KiCad 3D Viewer but is omitted from non-mesh STEP export. Maker STEP remains desirable. |
| D102 and other stock-footprint parts | KiCad 10 standard package STEP models. | Package shapes for 3D inspection; confirm exact part dimensions at G-3. |

The original user-downloaded Ultra Librarian ZIP is not required by KiCad after
extracting its STEP. Its source ZIP SHA-256 is
`9c409738e9fb11241a2306db80b8167d6a3af8ac0be0cab408640a1d2ce81f1d`.
`fetch_jlc_3d_models.py` can restore the 30 JLC STEP files from the saved
`JLC_Source/JLC_DAC_HPA.elibz` identifiers when network access is available;
it does not move footprints. `attach_3d_models.py` adds the twelve custom
model links to the five board snapshots if absent.

## Limits

The 3D view verifies that model files load and permits visual package and
clearance review. It does **not** prove pad numbering, solder-joint geometry,
height tolerance, connector mating, or routability. G-3 overlays, the JLCPCB
DFM review, and routing/ESD gates in `PRELAYOUT_GATES.md` remain open. The
primary board is a placement review with partial ESD routing, not a PCBA
release package.

KiCad's GLB exporter currently skips the four VRML film-capacitor envelopes;
use the KiCad 3D Viewer to see those bodies. The exported GLB was checked with
Assimp as a valid 480-node, 6,042-mesh model after correcting J101's offset.
