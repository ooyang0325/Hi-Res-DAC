# Hi-Res DAC + balanced headphone amplifier

The current deliverable is an editable [KiCad schematic capture](hardware/README.md) based on Design Spec v1.0, Schematic Design Notes v0.9, and Parts List v0.8. It remains **review only** while connector continuity, footprint overlay, polarity, and JLCPCB soldering-process gates are open. No PCB manufacturing or PCBA order files are released.

## GitLab CI/CD

`.gitlab-ci.yml` uses the fixed official KiCad 10.0.1 container. Every pipeline regenerates the schematic and review BOM, checks that generated files match the commit, compares the exported KiCad netlist with the workbook and calculation package, runs ERC, checks selected design-note rules, and inspects critical footprint pads. A successful pipeline delivers a nine-page review PDF and separated JLCPCB/owner-fitted/DNF CSV lists as downloadable artifacts for 30 days.

The GitLab review package is **not** a manufacturing release. The connector and physical gates are tracked in [connector review](hardware/CONNECTOR_REVIEW.md) and [PCBA process review](hardware/PCBA_PROCESS_REVIEW.md). A routed PCB and CPL would be required for a PCBA upload.
