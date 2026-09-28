# DAC-HPA KiCad schematic and placement

**Sending this design for peer review?** Begin with [REVIEWER_START_HERE.md](REVIEWER_START_HERE.md), then use the [schematic](SCHEMATIC_REVIEW_GUIDE.md), [placement](PLACEMENT_REVIEW_GUIDE.md), and [command-line visual inspection](PCB_CLI_VISUAL_REVIEW.md) guides. The [findings template](REVIEW_FINDINGS_TEMPLATE.md) records actionable review results against one Git commit.

The [current functional-ECO placement candidate](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb) is a separate 120 × 100 mm review board made from explicit hand-selected coordinates. It includes the [readback and J702 TVS schematic ECO](FUNCTIONAL_ECO_2026-09-28.md), a tighter DAC bypass row and the local J702 TVS branches. [Layout review](FUNCTIONAL_ECO_LAYOUT_REVIEW.md) and [constraint disposition](CONSTRAINT_DISPOSITION_V2.md) state the remaining route work. `DAC_HPA.kicad_pcb` and the [prior macro study](MACRO_PLACEMENT_REVIEW.md) are historical comparisons; they predate the eight added parts.

Open `DAC_HPA.kicad_pro` or `DAC_HPA.kicad_sch` in KiCad 10. The root page links eight circuit sheets following Design Spec v1.1, Schematic Design Notes v1.0, Parts List v0.9, and Capture Update Note v1.0.

`DAC_HPA_review_only.pdf` is a nine-page visual export of the current provisional capture. The expanded protection sheet uses A1; smaller blocks use A2/A3/A4. Each sheet title block identifies v1.1-ECO1 and the open F01/F03/G-1–G-4 holds. The KiCad project is the editable source.

## Current status

- The v0.9 workbook has 526 netlisted designators and 1,445 pin rows; those rows still match Calculation Package v1.1. The [asserted functional ECO](FUNCTIONAL_ECO_2026-09-28.md) adds eight parts. KiCad now has **534 netlisted designators, 1,465 pins, 1,422 connected pins, 43 no-connect pins and 250 named nets**, plus four grounded mounting holes and seven fiducials. The exact 26 workbook-to-capture pin/net differences are checked; they include the earlier D705/D706 polarity fix. J702 pins 5/6 remain no-connect break contacts.
- Per-part MPN, LCSC code, fit class, package, and rating/tolerance properties are included for later [JLCPCB BOM preparation](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad). The owner approved changing U403/U404 from workbook OPA2210IDR SOIC-8 to OPA2210IDGKR VSSOP-8, C2876414. `generate_schematic.py` asserts the old workbook entry and applies this explicit override; `IV_7MM_RECHECK.md` records the provisional 7 mm input-route reassessment and sourcing/footprint limitations.
- The review-only JLCPCB BOM contains **463 placed parts**, seven owner-fitted and nine DNF parts. Fourteen placed parts have no LCSC code and need the documented global-sourcing process. The three CSVs are **not** an order package; a routed PCB and CPL are still required.
- The schematic-aligned four-layer **120 × 100 mm functional-ECO baseline** has **544 footprints and 250 named nets**; J703 remains a schematic DNF option with no PCB pads. Its partial copper comprises J701/J702 local TVS branches and the hand-routed X201→R203→U301 MCLK trunk, R227 return and R665→U607 monitor input: **28 F.Cu tracks, seven vias** and one filled L2 GND zone. It has zero geometry DRC violations and 1,144 full ratsnest gaps. The old 536-footprint primary and 100 × 80/100 × 100 mm boards are historical comparisons.
- The [separate 270° output-macro study](OUTPUT_MACRO_ROUTE_STUDY.md) keeps the same schematic/pad map and manually connects all four U401/U402 amplifier outputs and local feedback to K601–K604 relay inputs. Its partial copper passes custom-rule DRC, but the jack outputs, input/T networks, supply returns and L3/L4 audio return remain on hold; it is a comparison, not the primary order board.
- The newest [integrated-audio routing study](INTEGRATED_AUDIO_ROUTE_STUDY.md) extends that hand placement through all four relays to J701/J702 and adds local input-shunt and jack ground returns. It passes custom-rule DRC and JLC geometry screens; 1,101 full ratsnest gaps, local VPOS/VNEG/EP power and bypass, L3/L4 return, output-impedance measurement and physical/JLC gates still hold any fabrication release.
- Every current footprint/pad net matches the ECO schematic. The new DAC high-frequency capacitors are 1.86–2.30 mm by pad distance from their supply pins; the U621 high-impedance input stubs are 1.69/1.86 mm by pad distance. The J702 TVS signal branches are 3.861/3.250 mm. The custom J701/J702 enlarged slot lands retain ≥0.31 mm worst calculated copper ring under the stated JLC slot tolerance. Physical G-3 overlays and JLC DFM remain open.
- All **478 component bodies** on the current candidate have resolvable 3D models; 66 test/debug/mechanical copper items intentionally have none. `3D_MODEL_REVIEW.md` distinguishes exact JLC/Toshiba sources from approximate oscillator and film-capacitor bodies. Open the current candidate in **View → 3D Viewer**.
- `verify_critical_footprints.py` checks 56 critical pad dimensions, pad types and hole/paste properties, including U202's exposed pad, the new TI DGK and onsemi SOT-23 lands, and J101/J701/J702 slots and locating holes. Physical G-3 overlays are still open.
- `G3_CONNECTOR_OVERLAY_REVIEW_ONLY.svg` and `G3_PART_OVERLAY_REVIEW_ONLY.svg` are printable A4 1:1 overlays for 30 unique footprint patterns, including U621 and the J702 TVS package; first measure each 10 mm reference bar. `G3_OVERLAY_INDEX.md` identifies the patterns and `G3_OVERLAY_CHECKLIST.md` holds editable physical sample results. The two-sample DMM and polarity templates are `G1_G2_CONTINUITY_RECORD.md` and `G4_POLARITY_CHECKLIST.md`.
- KiCad ERC reports zero violations. Confirmed power, logic, oscillator and open-collector outputs are typed; most other generated pins remain passive, so ERC does **not** substitute for a datasheet-level electrical review.
- `verify_design_notes.py` checks 978 selected circuit and approved-correction assertions. `SOURCE_RECONCILIATION.md` and the [ECO note](FUNCTIONAL_ECO_2026-09-28.md) record controlled changes from the source set.
- The v1.1 design documents mark schematic capture and provisional placement GO and originally hold routing until G-1–G-4 pass. The owner reports both J101 samples match the USB-C map, both J701 samples match the intended audio and 9/10 switch maps, and both J702 samples match the TRS and break map. On 27 September 2026 the owner waived the G-1/G-2 raw measurement log; these reported results are accepted for layout planning without independent evidence. G-3 overlays and G-4 polarity still hold routing, as do the new routability and audio/EMI placement conflicts. J702 supports TRS plugs only. `PRELAYOUT_GATES.md` tracks the gate evidence and later G-5/G-6 holds. See `CONNECTOR_REVIEW.md` for connector maps and copper-ring decision, `POLARITY_REVIEW.md` for the D705/D706 correction, and `CAD_models_to_upload.md` for exact 3D models still desired.
- `PCBA_PROCESS_REVIEW.md` records the J101/J702 plated slots with no paste apertures and the exact JLCPCB process question to resolve before assembly release. The output-impedance estimates remain 0.251 Ω (3.5 mm) and 0.383 Ω (4.4 mm); 50 mΩ per jack contact and 0 Ω link is an engineering estimate until bring-up measures each jack against ≤ 0.5 Ω.

The included JLCPCB library data came from LCSC codes through `dsa-t/jlc-kicad-lib-loader` 1.0.11. `JLC_Source/JLC_DAC_HPA.elibz` now keeps **42 source CAD entries**, including exact C507231 for U621; `JLC_Imported.pretty` contains native KiCad footprints, and `jlc_footprints.json` records pad comparisons. The TI DCK example land and JLC C507231 land differ, so U621 remains a G-3 overlay item. The project footprints are in `DAC_HPA.pretty`; custom land sources are in `FOOTPRINT_SOURCES.md`.

## Regenerate and verify

With Python 3, `openpyxl`, and KiCad 10 installed:

```sh
python3 hardware/audit_jlc_library.py
python3 hardware/derive_connector_footprints.py
python3 hardware/generate_schematic.py
python3 hardware/verify_schematic.py
python3 hardware/verify_design_notes.py
python3 hardware/export_assembly_review.py
python3 hardware/check_attach_charge.py
python3 hardware/check_spi2_capture_contract.py
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 hardware/verify_critical_footprints.py
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 hardware/audit_placement.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb --height 100 > /tmp/dac-eco-placement.json
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 hardware/audit_dfa_dfm.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb > /tmp/dac-eco-dfa.json
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 hardware/audit_jlc_fab.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb > /tmp/dac-eco-fab.json
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --format json --severity-error --severity-warning -o /tmp/dac-eco-drc.json hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 hardware/check_functional_eco_layout.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb /tmp/dac-eco-placement.json /tmp/dac-eco-dfa.json /tmp/dac-eco-fab.json /tmp/dac-eco-drc.json
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 hardware/audit_3d_models.py hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export pdf -o hardware/DAC_HPA_review_only.pdf hardware/DAC_HPA.kicad_sch
```

`generate_schematic.py` reads `doc/DAC_HPA_Parts_List_v0.9.xlsx`, asserts the source pin maps, applies the ECO and rewrites the generated sheets/symbol library. Run the CAD audits before regeneration when source data changes. Manual KiCad edits to generated schematic files are replaced on regeneration; edit the generator's asserted ECO or make a controlled new workbook revision. `manual_functional_eco_layout.py` records all additional hand-selected positions and local J702 tracks; its UUIDs may differ on reproduction, while `check_functional_eco_layout.py` checks the committed geometry and schematic pad map. `place_board.py --force` is only for historical automatic comparisons.
