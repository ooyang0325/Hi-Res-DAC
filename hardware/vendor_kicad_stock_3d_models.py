#!/usr/bin/env python3
"""Copy the KiCad stock STEP files used by this board into the project.

The project copy allows headless CI to resolve models without installing the
much larger full KiCad 3D package. Source files are copied unchanged and keep
their original KiCad library paths under KICAD_STOCK_MODELS.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
PREFIX = "${KICAD10_3DMODEL_DIR}/"
UPSTREAM = "https://gitlab.com/kicad/libraries/kicad-packages3D"


def source_dir() -> Path:
    candidates = [
        os.environ.get("KICAD_STOCK_3D_SOURCE", ""),
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels",
        "/usr/share/kicad/3dmodels",
        "/usr/local/share/kicad/3dmodels",
    ]
    for name in candidates:
        if name and Path(name).is_dir():
            return Path(name)
    raise SystemExit("Set KICAD_STOCK_3D_SOURCE to an installed KiCad 10 3dmodels directory")


def main() -> None:
    board = pcbnew.LoadBoard(str(HERE / "DAC_HPA.kicad_pcb"))
    names = sorted({model.m_Filename[len(PREFIX):]
                    for fp in board.GetFootprints() for model in fp.Models()
                    if model.m_Filename.startswith(PREFIX)})
    source = source_dir()
    output = HERE / "KICAD_STOCK_MODELS"
    records = []
    for name in names:
        src = source / name
        if not src.is_file():
            raise FileNotFoundError(src)
        dst = output / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        records.append({"path": name, "bytes": dst.stat().st_size,
                        "sha256": hashlib.sha256(dst.read_bytes()).hexdigest()})
    manifest = {"upstream": UPSTREAM, "license": "CC-BY-SA-4.0 with KiCad design exception",
                "source": "KiCad 10 installed stock 3D library, files copied without modification",
                "models": records}
    (output / "MODEL_SOURCES.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Copied {len(records)} KiCad stock models ({sum(r['bytes'] for r in records):,} bytes)")


if __name__ == "__main__":
    main()
