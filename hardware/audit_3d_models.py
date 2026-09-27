#!/usr/bin/env python3
"""Check that every assembled PCB footprint has a usable 3D model link.

This checks model references and files, not package-to-land alignment. The
physical G-3 overlay and assembly checks remain separate gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
BOARDS = (
    "DAC_HPA.kicad_pcb",
    "DAC_HPA_100x100_BASELINE_REVIEW_ONLY.kicad_pcb",
    "DAC_HPA_100x100_TIMER_STUDY_ONLY.kicad_pcb",
    "DAC_HPA_120x100_CLOCK_ESCAPE_STUDY_ONLY.kicad_pcb",
    "DAC_HPA_100x80_REVIEW_ONLY.kicad_pcb",
)
COPPER_ONLY = {"J201", "J202"}
STOCK_PREFIX = "${KICAD10_3DMODEL_DIR}/"
LOCAL_PREFIX = "${KIPRJMOD}/"


def stock_model_dir() -> Path | None:
    candidates = [
        os.environ.get("KICAD10_3DMODEL_DIR", ""),
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels",
        "/usr/share/kicad/3dmodels",
        "/usr/local/share/kicad/3dmodels",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_dir():
            return Path(candidate)
    return None


def model_file(board: Path, reference: str, model: str, stock: Path | None,
               errors: list[str]) -> Path | None:
    if model.startswith(LOCAL_PREFIX):
        return board.parent / model[len(LOCAL_PREFIX):]
    if model.startswith(STOCK_PREFIX):
        if stock is None:
            errors.append(f"{board.name}: {reference}: KiCad 10 3D library not found")
            return None
        return stock / model[len(STOCK_PREFIX):]
    errors.append(f"{board.name}: {reference}: unsupported model path {model}")
    return None


def check_file(path: Path, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"missing model: {path}")
        return
    header = path.open("rb").read(24)
    if path.suffix.lower() == ".step" and not header.startswith(b"ISO-10303-21;"):
        errors.append(f"invalid STEP header: {path}")
    elif path.suffix.lower() == ".wrl" and not header.startswith(b"#VRML V2.0 utf8"):
        errors.append(f"invalid VRML header: {path}")
    elif path.suffix.lower() not in {".step", ".wrl"}:
        errors.append(f"unsupported model format: {path}")


def check_jlc_manifest(errors: list[str]) -> int:
    manifest_path = HERE / "EASYEDA_MODELS/MODEL_SOURCES.json"
    if not manifest_path.is_file():
        errors.append("JLC model provenance manifest is missing")
        return 0
    records = json.loads(manifest_path.read_text())
    seen = set()
    for record in records:
        name = record["converted_file"]
        if name in seen:
            errors.append(f"duplicate JLC model manifest entry: {name}")
        seen.add(name)
        path = manifest_path.parent / name
        if not path.is_file():
            errors.append(f"missing JLC model: {path}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record["converted_sha256"]:
            errors.append(f"JLC model checksum changed: {path}")
        if record.get("warning"):
            errors.append(f"JLC model requires review: {name}: {record['warning']}")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boards", nargs="*", type=Path,
                        default=[HERE / name for name in BOARDS])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    stock = stock_model_dir()
    validated_files: set[Path] = set()
    reports = []
    required_jlc: set[str] = set()
    for board_path in args.boards:
        board_path = board_path.resolve()
        if not board_path.is_file():
            errors.append(f"missing board: {board_path}")
            continue
        board = pcbnew.LoadBoard(str(board_path))
        counts = {"footprints": 0, "modeled": 0, "copper_only": 0,
                  "stock": 0, "project_local": 0, "step": 0, "vrml": 0}
        references: set[str] = set()
        for footprint in board.GetFootprints():
            counts["footprints"] += 1
            ref = footprint.GetReference()
            if ref in references:
                errors.append(f"{board_path.name}: duplicate reference {ref}")
            references.add(ref)
            models = list(footprint.Models())
            copper_only = ref.startswith(("TP", "FID", "MH")) or ref in COPPER_ONLY
            if not models:
                if copper_only:
                    counts["copper_only"] += 1
                else:
                    errors.append(f"{board_path.name}: physical part {ref} has no 3D model")
                continue
            if copper_only:
                errors.append(f"{board_path.name}: copper-only item {ref} has a 3D model")
            if len(models) != 1:
                errors.append(f"{board_path.name}: {ref} has {len(models)} 3D models")
            if ref == "J101" and models:
                y_offset = models[0].m_Offset.y
                if abs(y_offset + 1.295) > 0.001:
                    errors.append(f"{board_path.name}: J101 model Y offset is {y_offset}, expected -1.295 mm")
            counts["modeled"] += 1
            for model in models:
                name = model.m_Filename
                if name.startswith(STOCK_PREFIX):
                    counts["stock"] += 1
                if name.startswith(LOCAL_PREFIX):
                    counts["project_local"] += 1
                if "/EASYEDA_MODELS/" in name:
                    required_jlc.add(Path(name).name)
                path = model_file(board_path, ref, name, stock, errors)
                if path is None:
                    continue
                counts["step" if path.suffix.lower() == ".step" else "vrml"] += 1
                if path not in validated_files:
                    check_file(path, errors)
                    validated_files.add(path)
        reports.append({"board": board_path.name, **counts})

    manifest_count = check_jlc_manifest(errors)
    recorded = {item["converted_file"] for item in json.loads(
        (HERE / "EASYEDA_MODELS/MODEL_SOURCES.json").read_text()
    )} if manifest_count else set()
    for filename in sorted(required_jlc - recorded):
        errors.append(f"JLC model absent from provenance manifest: {filename}")
    result = {"stock_model_dir": str(stock) if stock else None,
              "jlc_model_files": manifest_count, "boards": reports,
              "errors": errors, "ok": not errors}
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
