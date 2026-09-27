# DAC-HPA KiCad schematic capture

Open `DAC_HPA.kicad_pro` or `DAC_HPA.kicad_sch` in KiCad 10. The root page links eight circuit sheets following Design Spec v1.1, Schematic Design Notes v1.0, Parts List v0.9, and Capture Update Note v1.0.

`DAC_HPA_review_only.pdf` is a nine-page visual export of the current provisional capture. The expanded protection sheet uses A1; smaller blocks use A2/A3/A4. Each sheet title block names the v1.1 design set and marks the open G-1–G-4 hold. The KiCad project is the editable source.

## Current status

- 526 designators from the workbook netlist (474 parts and 52 one-pin test pads), plus four grounded mounting holes and seven fiducials. Sheet 6 removes 22 retired parts and adds 65 new over-range, low-level persistence, and self-test parts. Q623–Q626 use onsemi MMBT3904LT1G; U201 pin 4 drives `N6_ORTEST`.
- The 1,445 workbook pin rows match Calculation Package v1.1. The KiCad capture has 1,402 connected and 43 no-connect pins across 247 workbook nets including NC. Only four pin/net entries differ from the workbook: the owner-approved D705/D706 LED pad-polarity corrections in `POLARITY_REVIEW.md`. J701 and J702 follow Parts List v0.9 directly; J702 pins 5/6 are no-connect break contacts and never GND.
- Per-part MPN, LCSC code, fit class, package, and rating/tolerance properties are included for later [JLCPCB BOM preparation](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad). CPL positions will come from the later PCB layout.
- The review-only JLCPCB BOM contains 455 placed parts and excludes seven owner-fitted and nine DNF parts. Fourteen placed parts have no LCSC code and need the documented global-sourcing process. The three CSVs are **not** an order package; a routed PCB and CPL are still required.
- All 537 PCB items have assigned footprints with pad-number sets matching their schematic symbols. The custom J701/J702 footprints add real Ø1.20 mm NPTH locating holes. The owner chose to enlarge copper only around the unchanged maker slots and pad centres: the revised pads provide a 0.30 mm worst copper ring. G-3 sample overlays and JLCPCB DFM acceptance of the enlarged lands remain open.
- `verify_critical_footprints.py` checks 56 critical pad dimensions, pad types and hole/paste properties, including U202's exposed pad, the new TI DGK and onsemi SOT-23 lands, and J101/J701/J702 slots and locating holes. Physical G-3 overlays are still open.
- KiCad ERC reports zero violations. Confirmed power, logic, oscillator and open-collector outputs are typed; most other generated pins remain passive, so ERC does **not** substitute for a datasheet-level electrical review.
- `verify_design_notes.py` checks 947 selected circuit and approved-correction assertions. `SOURCE_RECONCILIATION.md` records stale checklist entries and the owner's correction of the workbook's D705 row.
- The design documents mark schematic capture and provisional placement GO, but schematic freeze and routing HOLD until G-1–G-4 pass. The owner reports both J101 samples match the USB-C map, both J701 samples match the intended 4.4 mm audio contacts, and both J702 samples match the maker's TRS contact and break map; signed gate records remain open. J702 supports TRS plugs only. `PRELAYOUT_GATES.md` tracks the gate evidence and later G-5/G-6 holds. See `CONNECTOR_REVIEW.md` for the connector maps and copper-ring decision, `POLARITY_REVIEW.md` for the approved D705/D706 correction, and `CAD_models_to_upload.md` for optional 3D models.
- `PCBA_PROCESS_REVIEW.md` records the J101/J702 plated slots with no paste apertures and the exact JLCPCB process question to resolve before assembly release. The output-impedance estimates remain 0.251 Ω (3.5 mm) and 0.383 Ω (4.4 mm); 50 mΩ per jack contact and 0 Ω link is an engineering estimate until bring-up measures each jack against ≤ 0.5 Ω.

The included JLCPCB library data came from LCSC codes through `dsa-t/jlc-kicad-lib-loader` 1.0.11, updated on 27 September 2026 for C140314 and C81464. `JLC_Source/JLC_DAC_HPA.elibz` keeps 41 source CAD entries, `JLC_Imported.pretty` contains the native KiCad footprint copies, and `jlc_footprints.json` records pad-set comparisons. The project's own footprints are in `DAC_HPA.pretty`; custom land-pattern sources are in `FOOTPRINT_SOURCES.md`. All imported and custom physical lands remain subject to G-1–G-4 sample and drawing checks.

## Regenerate and verify

With Python 3, `openpyxl`, and KiCad 10 installed:

```sh
python3 hardware/audit_jlc_library.py
python3 hardware/derive_connector_footprints.py
python3 hardware/generate_schematic.py
python3 hardware/verify_schematic.py
python3 hardware/verify_design_notes.py
python3 hardware/export_assembly_review.py
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 hardware/verify_critical_footprints.py
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export pdf -o hardware/DAC_HPA_review_only.pdf hardware/DAC_HPA.kicad_sch
```

`generate_schematic.py` reads `doc/DAC_HPA_Parts_List_v0.9.xlsx` and rewrites the generated schematic sheets and custom symbol library. Run `audit_jlc_library.py` and `derive_connector_footprints.py` before generation when their source CAD data changes, and `alias_exposed_pads.py` if the imported exposed-pad footprints change. Manual KiCad edits to generated schematic files will be replaced by regeneration; edit the generator or resolve changes back into the workbook first.
