#!/usr/bin/env python3
"""Normalize fetched JLC STEP files with KiCad's OpenCascade model utility."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pcbnew


def size(box) -> list[float]:
    vector = box.GetSize()
    return [round(vector.x, 4), round(vector.y, 4), round(vector.z, 4)]


def main() -> None:
    manifest = json.loads(Path(sys.argv[1]).read_text())
    outdir = Path(sys.argv[2])
    outdir.mkdir(exist_ok=True)
    records = []
    for entry in sorted(manifest, key=lambda item: item["title"]):
        title = entry["title"]
        model = pcbnew.UTILS_STEP_MODEL.LoadSTEP(entry["raw_path"])
        if not model:
            raise RuntimeError(f"KiCad could not load STEP for {title}")
        original = model.GetBoundingBox()
        actual = original.GetSize()
        transform = [float(value) for value in entry["transform"].split(",")]
        expected_x, expected_y = transform[0] / 39.37, transform[1] / 39.37
        factor_x, factor_y = expected_x / actual.x, expected_y / actual.y
        factor = (factor_x + factor_y) / 2
        warning = None
        if abs(factor_x - factor_y) > 0.1:
            warning = "JLC target X/Y scales disagree; original model scale retained"
            factor = 1.0
        elif abs(factor - 1.0) > 0.01:
            model.Scale(factor)
        else:
            factor = 1.0
        newbox = model.GetBoundingBox()
        center = newbox.GetCenter()
        model.Translate(-center.x, -center.y, -newbox.Min().z)
        destination = outdir / f"{title}.step"
        if not model.SaveSTEP(str(destination)) or destination.stat().st_size < 1000:
            raise RuntimeError(f"KiCad could not save normalized STEP for {title}")
        record = {key: value for key, value in entry.items() if key != "raw_path"}
        record.update({
            "converted_file": destination.name,
            "converted_bytes": destination.stat().st_size,
            "converted_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "raw_bbox_mm": size(original),
            "converted_bbox_mm": size(newbox),
            "applied_scale": round(factor, 6),
            "warning": warning,
        })
        records.append(record)
        print(f"Normalized {title}: {record['converted_bbox_mm']} mm"
              + (f" ({warning})" if warning else ""), flush=True)
    (outdir / "MODEL_SOURCES.json").write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
