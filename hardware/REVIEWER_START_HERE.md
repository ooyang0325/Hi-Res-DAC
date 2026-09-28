# DAC-HPA peer review: start here

**Review snapshot:** schematic capture v1.1 and the manually placed **120 × 100 mm, four-layer** primary PCB. Record the Git commit SHA you review; use the PDF, board and documents from that same revision. The board is a placement review with four J701 TVS signal escapes, four GND returns and one filled L2 GND zone. **Routing release is on hold.** KiCad reports zero error/warning DRC findings on this partial board and 499 unconnected items; that DRC result is not a routing sign-off.

For a repository checkout, run `git rev-parse HEAD` and record the result in the findings template. The CI artifact's `REVIEW_COMMIT.txt` names its exact source revision; the source ZIP contains committed files from that revision. If a KiCad installation lacks its stock 3D library, set `KICAD10_3DMODEL_DIR` to this checkout's `hardware/KICAD_STOCK_MODELS` directory before opening the board.

## Open the design in five minutes

| Need | Open |
| --- | --- |
| Read the circuit without KiCad | [Nine-page schematic PDF](DAC_HPA_review_only.pdf), or the PDF regenerated in the GitLab `deliver_review_package` artifact for the reviewed commit. |
| Edit or inspect the schematic | [KiCad project](DAC_HPA.kicad_pro) → [root schematic](DAC_HPA.kicad_sch), with eight linked sheets. |
| Inspect the current placement and partial copper | [Primary PCB](DAC_HPA.kicad_pcb), [2D whole-board preview](DAC_HPA_120x100_manual_preview.png), [3D whole-board preview](DAC_HPA_3D_review.png). |
| Inspect the new regrouped placement | [Manual macro-placement candidate](MACRO_PLACEMENT_REVIEW.md) → [candidate PCB](DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb), plus the [constraint disposition](CONSTRAINT_DISPOSITION_V2.md). It is a separate review study. |
| Export zoomable PCB layer views from a terminal | Follow [CLI visual inspection](PCB_CLI_VISUAL_REVIEW.md) to generate courtyard, copper, mask, paste, legend, 3D and DRC views from the reviewed commit. |
| Inspect J101 at the mating edge | [USB-C 3D closeup](DAC_HPA_J101_3D_detail.png). Its model offset was corrected; the copper footprint stayed at the maker's PCB-edge datum. |
| Obtain a portable snapshot | Use the `deliver_review_package` artifact for the reviewed GitLab pipeline. It contains a current PDF, GLB 3D view, key audits and a ZIP of the committed source. The editable KiCad project is also in the Git repository. |

The signal chain is USB-C input → USB audio bridge/CPLD and clocks → ES9018K2M DAC → I/V and output legs → protection/output switching → 4.4 mm balanced and 3.5 mm single-ended jacks. The power and protection sheets cross these blocks. The 3.5 mm output supports **TRS only**.

## Choose a review path

1. **Circuit and pin mapping:** follow [Schematic review guide](SCHEMATIC_REVIEW_GUIDE.md). Check datasheet pin functions, signal paths, power sequencing, protection fail states, and the explicit source-document corrections. ERC and workbook agreement are already checked, but do not establish electrical correctness.
2. **Placement, routing feasibility, audio/EMI and PCBA:** follow [Placement review guide](PLACEMENT_REVIEW_GUIDE.md). Check physical access and realistic simultaneous routes, especially clocks, DAC/I/V, headphone outputs, return paths and JLCPCB assembly exceptions.
   Compare the primary with the [macro-placement candidate](MACRO_PLACEMENT_REVIEW.md); the [J702 two-TVS option](J702_LOCAL_TVS_OPTION.md) is a board-only electrical ECO study, not the captured schematic.
3. **Physical samples:** use the [G-3 overlay checklist](G3_OVERLAY_CHECKLIST.md) and [G-4 polarity checklist](G4_POLARITY_CHECKLIST.md). The two-sample connector results for G-1/G-2 were reported by the owner and accepted for layout planning with the raw log waived; G-3/G-4 are still open.

Put each actionable issue in [Review findings template](REVIEW_FINDINGS_TEMPLATE.md). State the reference/net or board coordinate and layer, the expected condition, what you found, the evidence, and whether it blocks routing, fabrication or assembly. A review can conclude “conditional” when a physical measurement or JLCPCB answer is still required.

## Baseline and decision record

The pin-level connection source is [Parts List v0.9](../doc/DAC_HPA_Parts_List_v0.9.xlsx). Functional requirements come from [Design Spec v1.1](../doc/DAC_HPA_Design_Spec_v1.1.docx), [Schematic Design Notes v1.0](../doc/DAC_HPA_Schematic_Design_Notes_v1.0.docx), [Capture Update Note v1.0](../doc/DAC_HPA_Capture_Update_Note_v1.0.docx), and [Calculation Package v1.1](../doc/DAC_HPA_Calculation_Package_v1.1.zip). These versioned files predate several owner-approved capture and placement changes. Use [Source reconciliation](SOURCE_RECONCILIATION.md) and [Pre-layout gates](PRELAYOUT_GATES.md) to distinguish an approved deviation from a new defect; report any other conflict.

The main approved changes after those source documents are the 120 × 100 mm primary outline, VSSOP OPA2210IDGKR at U403/U404 with a **provisional** 7 mm DAC-to-I/V route target, a **provisional** 4.2 mm J701 TVS signal path with ESD testing, removal of physical J703 pads while keeping its schematic DNF option, enlarged copper around unchanged J701/J702 slots, and the D705/D706 pad-1-anode correction. [Manual placement review](MANUAL_PLACEMENT_REVIEW.md), [Connector review](CONNECTOR_REVIEW.md), [Polarity review](POLARITY_REVIEW.md) and [I/V recheck](IV_7MM_RECHECK.md) hold the detail.

## What the existing checks establish

The GitLab pipeline checks regeneration, the workbook netlist, 947 selected design-note assertions, critical footprints, placement geometry, JLC spacing/fabrication proxies, the four J701 ESD routes, 3D model paths and KiCad DRC. The primary has 536 footprints, 246 named PCB nets, 470 modeled component bodies, eight routed tracks, four vias and one filled zone. The [3D model review](3D_MODEL_REVIEW.md) identifies exact and approximate bodies. A successful pipeline does not close G-3/G-4, the 499 unconnected items, route-length/impedance/return-path checks, or JLCPCB's order-specific DFM and soldering-process review.

**Review decision requested:** identify defects and required changes before routing proceeds, and mark each open physical or manufacturing condition with the evidence needed to close it. The current source is not a Gerber/CPL/PCBA release.
