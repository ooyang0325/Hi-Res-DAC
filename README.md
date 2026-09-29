# Hi-Res DAC + balanced headphone amplifier

The current layout review candidate is the editable [120 × 100 mm integrated-audio KiCad board](hardware/DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb), with manual placement and partial routing, paired with the [schematic](hardware/DAC_HPA.kicad_sch). Parts List v0.9 and Calculation Package v1.1 remain the baseline; the [captured ECO](hardware/FUNCTIONAL_ECO_2026-09-28.md) adds buffered supervisor readbacks and local J702 TVS parts. Start a peer review with the [layout handover report](hardware/LAYOUT_HANDOVER_REPORT.md), then use the [reviewer guide](hardware/REVIEWER_START_HERE.md). The full-rate MCU capture guard, physical overlays, output routability and JLCPCB process gates remain open. No PCB manufacturing or PCBA order files are released.

## GitLab CI/CD

`.gitlab-ci.yml` uses the fixed official KiCad 10.0.1 container. Every pipeline checks schematic regeneration, netlist/ERC, the exact ECO delta, attach-charge arithmetic, placement geometry, JLC fabrication/assembly proxies, DRC and 3D model paths. A successful pipeline delivers the nine-page review PDF, the integrated-audio board's 3D GLB and top/L2/L3/bottom SVGs, earlier board GLBs for comparison, reviewer guides, BOM CSVs and a ZIP of the committed source as downloadable artifacts for 30 days.

The GitLab review package is **not** a manufacturing release. The connector and physical gates are tracked in [connector review](hardware/CONNECTOR_REVIEW.md) and [PCBA process review](hardware/PCBA_PROCESS_REVIEW.md). A routed PCB and CPL would be required for a PCBA upload.

The [integrated-audio route study](hardware/INTEGRATED_AUDIO_ROUTE_STUDY.md) documents the current board's partial DAC/I/V, amplifier-input, U501 and amplifier-to-jack copper. The [functional-ECO board](hardware/DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb) is its preceding placement baseline; the former primary and [macro study](hardware/MACRO_PLACEMENT_REVIEW.md) are earlier comparisons. [Routing constraints](hardware/CONSTRAINT_DISPOSITION_V2.md) and the route study record the remaining critical route work.
