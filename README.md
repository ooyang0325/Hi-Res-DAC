# Hi-Res DAC + balanced headphone amplifier

The current deliverable is an editable [KiCad schematic and manually placed 120 × 100 mm PCB](hardware/README.md) based on Design Spec v1.1, Schematic Design Notes v1.0, Parts List v0.9, and Capture Update Note v1.0. Start a peer review with the [reviewer handoff](hardware/REVIEWER_START_HERE.md). The owner accepted the reported connector continuity results for layout planning and waived their raw log; footprint overlay, polarity, route feasibility and JLCPCB soldering-process gates remain open. No PCB manufacturing or PCBA order files are released.

## GitLab CI/CD

`.gitlab-ci.yml` uses the fixed official KiCad 10.0.1 container. Every pipeline audits the JLC CAD source, checks schematic regeneration, netlist, ERC, selected design-note rules and critical footprints, then checks placement geometry, JLC fabrication/assembly proxies, KiCad DRC and 3D model paths. A successful pipeline delivers the nine-page review PDF, 3D GLB, reviewer guides, separated JLCPCB/owner-fitted/DNF CSVs and a ZIP of the committed source as downloadable artifacts for 30 days.

The GitLab review package is **not** a manufacturing release. The connector and physical gates are tracked in [connector review](hardware/CONNECTOR_REVIEW.md) and [PCBA process review](hardware/PCBA_PROCESS_REVIEW.md). A routed PCB and CPL would be required for a PCBA upload.
