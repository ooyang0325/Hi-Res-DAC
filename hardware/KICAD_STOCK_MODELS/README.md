# Bundled KiCad package models

These 14 unchanged STEP models come from the installed KiCad 10 3D library,
whose upstream source is the [official KiCad Packages3D repository](https://gitlab.com/kicad/libraries/kicad-packages3D).
The KiCad community is credited as the library author. The files retain their
original library-relative names and directories. `MODEL_SOURCES.json` lists
each file and SHA-256 digest.

These models are distributed under KiCad's CC BY-SA 4.0 library license and
design exception, reproduced in [LICENSE.md](LICENSE.md). The project copies
only the shapes referenced by the current PCB and the discharge-fit option so
a fresh GitLab runner can resolve them while exporting review-only GLBs. The
2512 resistor body was added for the three-part power fit study, and the two SMD
pin-header bodies for the J201/J202 programming headers (ECO F05) on the integrated board. No 3D
geometry was changed.

To refresh this directory from an installed KiCad 10 library, run
`vendor_kicad_stock_3d_models.py` with KiCad's Python interpreter. By default
it scans the primary, integrated and discharge-fit boards; pass board paths
to restrict the scan. Set
`KICAD_STOCK_3D_SOURCE` if the installed 3D library is not in a standard
location. Review upstream revisions and license details before replacing the
copied files.
