#!/usr/bin/env python3
"""Attach reviewed standard/envelope models to embedded PCB footprints.

The matching custom .kicad_mod files carry the same model paths. This script
updates existing board files without moving pads, tracks, or components.
"""

from __future__ import annotations

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
BOARDS = [
    "DAC_HPA.kicad_pcb",
    "DAC_HPA_100x100_BASELINE_REVIEW_ONLY.kicad_pcb",
    "DAC_HPA_100x100_TIMER_STUDY_ONLY.kicad_pcb",
    "DAC_HPA_120x100_CLOCK_ESCAPE_STUDY_ONLY.kicad_pcb",
    "DAC_HPA_100x80_REVIEW_ONLY.kicad_pcb",
]

USB4105 = "${KICAD10_3DMODEL_DIR}/Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step"
CRYSTAL2520 = "${KICAD10_3DMODEL_DIR}/Crystal.3dshapes/Crystal_SMD_2520-4Pin_2.5x2.0mm.step"
FILM_ENVELOPE = "${KIPRJMOD}/DAC_HPA_3D/ECHU1H224GX9_envelope_only.wrl"
RELAY_LF1 = "${KIPRJMOD}/DAC_HPA_3D/TLP3545A_LF1_UltraLibrarian.step"

MODELS = {
    "J101": (USB4105, (0, -1.295, 0), (0, 0, 0)),
    "X201": (CRYSTAL2520, (0, 0, 0), (0, 0, 0)),
    "X202": (CRYSTAL2520, (0, 0, 0), (0, 0, 0)),
    "X203": (CRYSTAL2520, (0, 0, 0), (0, 0, 0)),
    "C631": (FILM_ENVELOPE, (0, 0, 0), (0, 0, 0)),
    "C632": (FILM_ENVELOPE, (0, 0, 0), (0, 0, 0)),
    "C633": (FILM_ENVELOPE, (0, 0, 0), (0, 0, 0)),
    "C634": (FILM_ENVELOPE, (0, 0, 0), (0, 0, 0)),
    "K601": (RELAY_LF1, (0, 0, 0), (0, 0, -90)),
    "K602": (RELAY_LF1, (0, 0, 0), (0, 0, -90)),
    "K603": (RELAY_LF1, (0, 0, 0), (0, 0, -90)),
    "K604": (RELAY_LF1, (0, 0, 0), (0, 0, -90)),
}


def main() -> None:
    for name in BOARDS:
        path = HERE / name
        if not path.is_file():
            continue
        board = pcbnew.LoadBoard(str(path))
        footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
        added = updated = 0
        for ref, (filename, offset, rotation) in MODELS.items():
            footprint = footprints[ref]
            models = footprint.Models()
            existing = next((index for index, model in enumerate(models)
                             if model.m_Filename == filename), None)
            if existing is None:
                model = pcbnew.FP_3DMODEL()
                model.m_Filename = filename
                model.m_Offset = pcbnew.VECTOR3D(*offset)
                model.m_Rotation = pcbnew.VECTOR3D(*rotation)
                footprint.Add3DModel(model)
                added += 1
                continue
            model = models[existing]
            current_offset = tuple(getattr(model.m_Offset, axis) for axis in "xyz")
            current_rotation = tuple(getattr(model.m_Rotation, axis) for axis in "xyz")
            if any(abs(a - b) > 1e-6 for a, b in zip(current_offset, offset)) or any(
                abs(a - b) > 1e-6 for a, b in zip(current_rotation, rotation)
            ):
                model.m_Offset = pcbnew.VECTOR3D(*offset)
                model.m_Rotation = pcbnew.VECTOR3D(*rotation)
                models[existing] = model
                updated += 1
        if added or updated:
            pcbnew.SaveBoard(str(path), board)
        print(f"{name}: {added} model links added, {updated} transforms updated")


if __name__ == "__main__":
    main()
