# DAC-HPA KiCad schematic capture

Open `DAC_HPA.kicad_pro` or `DAC_HPA.kicad_sch` in KiCad 10. The root page links eight circuit sheets following the blocks in Design Spec v1.0, Schematic Design Notes v0.9, and Parts List v0.8.

`DAC_HPA_review_only.pdf` is a nine-page visual export of the current provisional capture. Smaller blocks use A3/A4 pages for legibility, and each sheet title block marks the open G-1–G-4 hold. The KiCad project is the editable source.

## Current status

- 483 designators from the workbook netlist, plus four grounded mounting holes and seven fiducials.
- 1,305 workbook pin rows match the merged netlist in Calculation Package v1.0. The approved KiCad schematic has 1,310 pins and 1,268 connected assignments. Exactly 16 pin/net entries differ from the workbook through the owner-approved D705/D706 and J701 corrections recorded in `POLARITY_REVIEW.md` and `CONNECTOR_REVIEW.md`.
- Per-part MPN, LCSC code, fit class, package, and rating/tolerance properties are included for later [JLCPCB BOM preparation](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad). CPL positions will come from the later PCB layout.
- The review-only JLCPCB BOM contains 412 placed parts and excludes seven owner-fitted and nine DNF parts. Fourteen placed parts have no LCSC code and need the documented global-sourcing process. The three CSVs are **not** an order package; a routed PCB and CPL are still required.
- All 494 PCB items have assigned footprints with pad-number sets matching their schematic symbols. J701 uses the 12-pad JLCPCB candidate footprint, subject to G-2/G-3 physical checks.
- `verify_critical_footprints.py` checks 30 critical pad dimensions, pad types and hole/paste properties against the recorded drawings, including U202's exposed pad and the J101/J701/J702 plated slots. Physical G-3 overlays are still open.
- KiCad ERC reports zero violations. Confirmed power, logic, oscillator and open-collector outputs are typed; most other generated pins remain passive, so ERC does **not** substitute for a datasheet-level electrical review.
- `verify_design_notes.py` checks 623 selected circuit and approved-correction assertions. `SOURCE_RECONCILIATION.md` records stale checklist entries where the detailed notes, specification, and workbook agree on a different value or connection.
- The design documents mark schematic capture GO and schematic freeze HOLD. See `CONNECTOR_REVIEW.md` for the J101/J701/J702 issues, `POLARITY_REVIEW.md` for the approved D705/D706 correction, and `CAD_models_to_upload.md` for optional 3D models.
- `PCBA_PROCESS_REVIEW.md` records the J101/J702 plated slots with no paste apertures and the exact JLCPCB process question to resolve before assembly release.

The included JLCPCB library data came from LCSC codes through `dsa-t/jlc-kicad-lib-loader` 1.0.11 on 26 September 2026. `JLC_Source/JLC_DAC_HPA.elibz` keeps the source models, `JLC_Imported.pretty` contains the native KiCad footprint copies, and `jlc_footprints.json` records pad-set comparisons. The project's own footprints are in `DAC_HPA.pretty`; custom land-pattern sources are in `FOOTPRINT_SOURCES.md`. All imported and custom physical lands remain subject to G-1–G-4 sample and drawing checks.

## Regenerate and verify

With Python 3, `openpyxl`, and KiCad 10 installed:

```sh
python3 hardware/generate_schematic.py
python3 hardware/verify_schematic.py
python3 hardware/verify_design_notes.py
python3 hardware/export_assembly_review.py
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 hardware/verify_critical_footprints.py
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export pdf -o hardware/DAC_HPA_review_only.pdf hardware/DAC_HPA.kicad_sch
```

`generate_schematic.py` reads `doc/DAC_HPA_Parts_List_v0.8.xlsx` and rewrites the generated schematic sheets and custom symbol library. Run `audit_jlc_library.py` if the JLC source library changes, and `alias_exposed_pads.py` if the imported exposed-pad footprints change. Manual KiCad edits to generated schematic files will be replaced by regeneration; edit the generator or resolve changes back into the workbook first.
