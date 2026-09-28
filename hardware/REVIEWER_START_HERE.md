# DAC-HPA peer review: start here

**Review snapshot:** schematic capture **v1.1-ECO1** and the newest [manually routed 120 × 100 mm integrated-audio study](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb). Record the Git commit SHA you review; use the PDF, board and documents from that revision. The study keeps 544 footprints and 250 named nets, routes four amplifier legs through the relays to J701/J702, and keeps one continuous filled L2 GND polygon. **Routing release is on hold:** DRC has zero violations on its partial copper, while the full ratsnest still counts 1,101 missing links. The [functional-ECO board](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb) is the earlier schematic-aligned placement baseline.

For a repository checkout, run `git rev-parse HEAD` and record the result in the findings template. The CI artifact's `REVIEW_COMMIT.txt` names its exact source revision; the source ZIP contains committed files from that revision. If a KiCad installation lacks its stock 3D library, set `KICAD10_3DMODEL_DIR` to this checkout's `hardware/KICAD_STOCK_MODELS` directory before opening the board.

## Open the design in five minutes

| Need | Open |
| --- | --- |
| Read the circuit without KiCad | [Nine-page schematic PDF](DAC_HPA_review_only.pdf), or the PDF regenerated in the GitLab `deliver_review_package` artifact for the reviewed commit. |
| Edit or inspect the schematic | [KiCad project](DAC_HPA.kicad_pro) → [root schematic](DAC_HPA.kicad_sch), with eight linked sheets. |
| Inspect the newest audio placement and partial copper | [Integrated-audio board](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb), [route study and margin note](INTEGRATED_AUDIO_ROUTE_STUDY.md), [routing constraints](CONSTRAINT_DISPOSITION_V2.md), and its zoomable SVG/GLB from the `deliver_review_package` CI artifact. |
| Compare the capture baseline and intermediate macro | [Functional-ECO board](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb), [2D baseline preview](DAC_HPA_FUNCTIONAL_ECO_PLACEMENT_REVIEW.png), [layout review](FUNCTIONAL_ECO_LAYOUT_REVIEW.md), and the [earlier output-macro study](OUTPUT_MACRO_ROUTE_STUDY.md). All share the same schematic pad map. |
| Compare the earlier placement | [Former primary PCB](DAC_HPA.kicad_pcb) and [macro-placement study](DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb). Both have 536 footprints and predate the new schematic ECO. |
| Export zoomable PCB layer views from a terminal | Follow [CLI visual inspection](PCB_CLI_VISUAL_REVIEW.md) to generate courtyard, copper, mask, paste, legend, 3D and DRC views from the reviewed commit. |
| Inspect J101 at the mating edge | [USB-C 3D closeup](DAC_HPA_J101_3D_detail.png). Its model offset was corrected; the copper footprint stayed at the maker's PCB-edge datum. |
| Obtain a portable snapshot | Use the `deliver_review_package` artifact for the reviewed GitLab pipeline. It contains a current PDF, GLB 3D view, key audits and a ZIP of the committed source. The editable KiCad project is also in the Git repository. |

The signal chain is USB-C input → USB audio bridge/CPLD and clocks → ES9018K2M DAC → I/V and output legs → protection/output switching → 4.4 mm balanced and 3.5 mm single-ended jacks. The power and protection sheets cross these blocks. The 3.5 mm output supports **TRS only**.

## Choose a review path

1. **Circuit and pin mapping:** follow [Schematic review guide](SCHEMATIC_REVIEW_GUIDE.md). Check datasheet pin functions, signal paths, power sequencing, protection fail states, and the explicit source-document corrections. ERC and workbook agreement are already checked, but do not establish electrical correctness.
2. **Placement, routing feasibility, audio/EMI and PCBA:** follow [Placement review guide](PLACEMENT_REVIEW_GUIDE.md). Inspect the current ECO board for physical access and realistic simultaneous routes, especially clocks, DAC/I/V, headphone outputs, return paths and JLCPCB assembly exceptions. D707/D708 at J702 are now in the schematic/BOM; the [older board-only trial](J702_LOCAL_TVS_OPTION.md) is a historical geometry comparison.
3. **Physical samples:** use the [G-3 overlay checklist](G3_OVERLAY_CHECKLIST.md) and [G-4 polarity checklist](G4_POLARITY_CHECKLIST.md). The two-sample connector results for G-1/G-2 were reported by the owner and accepted for layout planning with the raw log waived; G-3/G-4 are still open.

Put each actionable issue in [Review findings template](REVIEW_FINDINGS_TEMPLATE.md). State the reference/net or board coordinate and layer, the expected condition, what you found, the evidence, and whether it blocks routing, fabrication or assembly. A review can conclude “conditional” when a physical measurement or JLCPCB answer is still required.

## Baseline and decision record

The pin-level baseline is [Parts List v0.9](../doc/DAC_HPA_Parts_List_v0.9.xlsx) and [Calculation Package v1.1](../doc/DAC_HPA_Calculation_Package_v1.1.zip); functional requirements also come from [Design Spec v1.1](../doc/DAC_HPA_Design_Spec_v1.1.docx), [Schematic Design Notes v1.0](../doc/DAC_HPA_Schematic_Design_Notes_v1.0.docx) and [Capture Update Note v1.0](../doc/DAC_HPA_Capture_Update_Note_v1.0.docx). The current KiCad capture applies the explicit [functional ECO](FUNCTIONAL_ECO_2026-09-28.md) after asserting that baseline. Use [Source reconciliation](SOURCE_RECONCILIATION.md) and [Pre-layout gates](PRELAYOUT_GATES.md) to distinguish a controlled change from a new defect.

The controlled changes include VSSOP OPA2210IDGKR at U403/U404 with a **provisional** 7 mm DAC-to-I/V route target, a **provisional** 4.2 mm J701 TVS path, no J703 PCB pads, enlarged J701/J702 slot copper, the D705/D706 polarity correction, the buffered U605 readbacks and D707/D708 local J702 TVS. The CH32V307 I²S limit and [proposed SPI2 capture path](MCU_SPI2_CAPTURE_ECO.md) remain a functional hold. The [attach-charge reconciliation](ATTACH_CHARGE_RECONCILIATION.json) is a planning bound pending measurement.

## What the existing checks establish

The GitLab pipeline checks schematic regeneration, the exact 26-pin/net ECO delta, 978 selected design-note assertions, critical footprints, 3V3M charge arithmetic, the SPI2 rate/framing contract, pad/net identity, placement geometry, JLC spacing/fabrication proxies, local TVS and clock copper, 3D model paths and KiCad DRC. The new integrated-audio job additionally checks the frozen manual move/copper record, four feedback loops, amplifier-to-relay-to-jack connectivity, input-shunt returns and the conditional output-impedance budget. A successful pipeline does not close F01's physical WS fault coverage, G-3/G-4, the 1,101 remaining ratsnest gaps, bypass/power and L3 return routing, measured R-15, or JLCPCB's order-specific DFM and soldering process.

**Review decision requested:** identify defects and required changes before routing proceeds, and mark each open physical or manufacturing condition with the evidence needed to close it. The current source is not a Gerber/CPL/PCBA release.
