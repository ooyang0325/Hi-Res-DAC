# Hi-Res DAC + balanced headphone amplifier

The current deliverable is an editable [KiCad schematic and manually placed 120 × 100 mm functional-ECO PCB candidate](hardware/README.md). Parts List v0.9 and Calculation Package v1.1 remain the baseline; the [captured ECO](hardware/FUNCTIONAL_ECO_2026-09-28.md) adds buffered supervisor readbacks and local J702 TVS parts. Start a peer review with the [reviewer handoff](hardware/REVIEWER_START_HERE.md). The full-rate MCU capture guard, physical overlays, output routability and JLCPCB process gates remain open. No PCB manufacturing or PCBA order files are released.

## GitLab CI/CD

`.gitlab-ci.yml` uses the fixed official KiCad 10.0.1 container. Every pipeline checks schematic regeneration, netlist/ERC, the exact ECO delta, attach-charge arithmetic, placement geometry, JLC fabrication/assembly proxies, DRC and 3D model paths. A successful pipeline delivers the nine-page review PDF, the current candidate's 3D GLB and SVG, reviewer guides, BOM CSVs and a ZIP of the committed source as downloadable artifacts for 30 days.

The GitLab review package is **not** a manufacturing release. The connector and physical gates are tracked in [connector review](hardware/CONNECTOR_REVIEW.md) and [PCBA process review](hardware/PCBA_PROCESS_REVIEW.md). A routed PCB and CPL would be required for a PCBA upload.

The [current manual functional-ECO candidate](hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb) incorporates that macro regrouping, the added components, shorter DAC bypass placement and J702 local ESD branches. The former primary and [macro study](hardware/MACRO_PLACEMENT_REVIEW.md) are historical comparisons. [Routing constraints](hardware/CONSTRAINT_DISPOSITION_V2.md) and the [layout review](hardware/FUNCTIONAL_ECO_LAYOUT_REVIEW.md) record the remaining critical route work.
