"""Independent PCB sign-off gate suite.

The package is deliberately split so that only :mod:`extract` depends on
KiCad.  Every gate runs against the tool-independent JSON model that
:mod:`extract` emits, which means the acceptance criteria can be reviewed,
re-run and argued with without a PCB tool installed.
"""

__all__ = [
    "rules",
    "geom",
    "design_intent",
    "netgraph",
    "framework",
]
