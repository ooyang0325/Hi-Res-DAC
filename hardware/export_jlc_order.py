#!/usr/bin/env python3
"""JLCPCB order files for the integrated board: Gerber + drill zip, BOM and placement (CPL) files.

    python3 hardware/export_jlc_order.py OUT_DIR

Writes OUT_DIR/DAC_HPA_gerber.zip (6 copper layers, paste, silk, mask, outline, PTH/NPTH Excellon in mm
with slots as G85), OUT_DIR/DAC_HPA_BOM.csv (the reviewed JLC BOM) and OUT_DIR/DAC_HPA_CPL.csv (JLC
columns, top side). The CPL comes from KiCad's position export, so the board attributes decide it:
DNF and owner-fitted parts are already excluded; fiducials are dropped here. Fails unless the CPL
designators equal the BOM designators. Regenerate from the frozen commit for the real order.
"""
import csv
import math
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = HERE / "DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb"
BOM = HERE / "JLCPCB_BOM_REVIEW_ONLY.csv"
LAYERS = "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
CLI = shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
# Footprints whose origin is pin 1, not the body centre JLCPCB places by: footprint-local offset
# (mm, KiCad axes) from the origin to the pad centre. Found in the JLCDFM placement preview, 19 Oct 2026.
CENTRE_OFFSETS = {
    "PinHeader_1x08_P2.54mm_SMD_XKB_X6511WVS-08H-C60D48R1": (8.89, 0.0),
    "PinHeader_1x05_P2.54mm_SMD_XKB_X6511WVS-05H-C60D48R1": (5.08, 0.0),
}


def body_centre(row):
    """Position-file X/Y moved from the footprint origin to the body centre (position files have Y up)."""
    x, y = float(row["PosX"]), float(row["PosY"])
    dx, dy = CENTRE_OFFSETS.get(row["Package"], (0.0, 0.0))
    a = math.radians(float(row["Rot"]))
    return x + dx * math.cos(a) + dy * math.sin(a), y + dx * math.sin(a) - dy * math.cos(a)


def cli(*args):
    subprocess.run([CLI, "pcb", "export", *args, str(BOARD)], check=True, capture_output=True)


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        fab = Path(tmp)
        cli("gerbers", "--layers", LAYERS, "--subtract-soldermask", "-o", str(fab))
        cli("drill", "--format", "excellon", "--excellon-units", "mm", "--excellon-oval-format", "alternate",
            "--excellon-separate-th", "--drill-origin", "absolute", "-o", str(fab))
        files = sorted(p for p in fab.iterdir() if p.is_file())
        with zipfile.ZipFile(out / "DAC_HPA_gerber.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p in files:
                z.write(p, p.name)
        pos = fab / "pos.csv"
        cli("pos", "--format", "csv", "--units", "mm", "--side", "front", "--exclude-dnp", "-o", str(pos))
        rows = [r for r in csv.DictReader(pos.open()) if not r["Ref"].startswith("FID")]
    unused = set(CENTRE_OFFSETS) - {r["Package"] for r in rows}
    if unused:
        raise SystemExit(f"CENTRE_OFFSETS footprints not on the board (renamed?): {sorted(unused)}")
    with (out / "DAC_HPA_CPL.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            x, y = body_centre(r)
            w.writerow([r["Ref"], f"{x:.4f}mm", f"{y:.4f}mm", "Top", f"{float(r['Rot']):g}"])
    shutil.copy(BOM, out / "DAC_HPA_BOM.csv")
    with BOM.open(encoding="utf-8-sig") as f:
        bom = {ref.strip() for row in csv.DictReader(f) for ref in row["Designator"].split(",")}
    cpl = {r["Ref"] for r in rows}
    if cpl != bom:
        raise SystemExit(f"CPL and BOM designators differ: {sorted(cpl ^ bom)}")
    print(f"{out}: {len(files)} Gerber/drill files, {len(cpl)} placements = BOM designators")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
