#!/usr/bin/env python3
"""Build the hand-placed, schematic-divergent discharge resistor fit option.

This is a package and routing feasibility study. The main integrated board,
schematic and BOM retain the current 0603 parts pending a controlled ECO.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb"
DEFAULT_OUTPUT = HERE / "DAC_HPA_120x100_DISCHARGE_FIT_OPTION_ONLY.kicad_pcb"


def resistor_library() -> Path:
    candidates = []
    if os.environ.get("KICAD10_FOOTPRINT_DIR"):
        candidates.append(Path(os.environ["KICAD10_FOOTPRINT_DIR"]))
    candidates.extend((
        Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"),
        Path("/usr/share/kicad/footprints"),
    ))
    for root in candidates:
        library = root / "Resistor_SMD.pretty"
        if library.is_dir():
            return library
    raise FileNotFoundError("KiCad's stock Resistor_SMD.pretty library is unavailable")

# Every coordinate was chosen by inspection of the power corner, not by a
# placement search. The two new routes end at actual pad centres.
REPLACEMENTS = {
    "R527": ("R_2512_6332Metric", 44.4, 113.0, 270.0),
    "R529": ("R_2512_6332Metric", 44.4, 125.5, 90.0),
    "R530": ("R_2512_6332Metric", 57.3, 135.8, 180.0),
}
MOVES = {
    "R512": (48.5, 118.0),
    "C514": (49.0, 120.5),
    "R531": (49.0, 127.5),
    "TP738": (45.5, 130.5),
    "Q506": (57.95, 131.7),
    "R535": (60.5, 129.4),
}
LOCAL_ROUTES = (
    ("R527", "2", "Q503", "3", 0.50),
    ("Q506", "3", "R530", "2", 0.30),
)


def position(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))


def pad(fp: pcbnew.FOOTPRINT, number: str) -> pcbnew.PAD:
    matches = [item for item in fp.Pads() if item.GetNumber() == number]
    if len(matches) != 1:
        raise AssertionError(f"{fp.GetReference()}.{number} pad changed")
    return matches[0]


def build(output: Path) -> None:
    board = pcbnew.LoadBoard(str(SOURCE))
    library = resistor_library()
    if len(board.GetFootprints()) != 544 or len(board.GetTracks()) != 855:
        raise AssertionError("Integrated source changed; recheck the hand fit option")
    source_footprints = {item.GetReference(): item for item in board.GetFootprints()}
    source_metadata = {
        ref: (source_footprints[ref].GetFPIDAsString(),
              source_footprints[ref].GetValue(),
              {item.GetNumber(): item.GetNetname()
               for item in source_footprints[ref].Pads()})
        for ref in REPLACEMENTS
    }
    for ref, (model, x_mm, y_mm, angle) in REPLACEMENTS.items():
        old = source_footprints[ref]
        old_id, old_value, original_nets = source_metadata[ref]
        if old_id != "Resistor_SMD:R_0603_1608Metric":
            raise AssertionError(f"{ref} is no longer the 0603 source package")
        expected = {"R527": ("3V3A", "N5_DIS_A_R"),
                    "R529": ("3V3D", "N5_DIS_D_R"),
                    "R530": ("1V3", "N5_DIS_13_R")}[ref]
        if tuple(original_nets[number] for number in ("1", "2")) != expected:
            raise AssertionError(f"{ref} source pad nets changed")
        new = pcbnew.FootprintLoad(str(library), model)
        if new is None:
            raise RuntimeError(f"KiCad stock footprint missing: {model}")
        new.SetReference(ref)
        new.SetValue(old_value)
        new.SetPosition(position(x_mm, y_mm))
        new.SetOrientationDegrees(angle)
        for item in new.Pads():
            item.SetNet(board.FindNet(original_nets[item.GetNumber()]))
        board.Remove(old)
        board.Add(new)
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for ref, (x_mm, y_mm) in MOVES.items():
        footprints[ref].SetPosition(position(x_mm, y_mm))
    for source_ref, source_pin, target_ref, target_pin, width_mm in LOCAL_ROUTES:
        first = pad(footprints[source_ref], source_pin)
        last = pad(footprints[target_ref], target_pin)
        if first.GetNetname() != last.GetNetname():
            raise AssertionError(f"Fit route net changed: {source_ref} to {target_ref}")
        if any(item.GetNetname() == first.GetNetname() for item in board.GetTracks()):
            raise AssertionError(f"Fit route {first.GetNetname()} is no longer open")
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(first.GetPosition())
        track.SetEnd(last.GetPosition())
        track.SetWidth(pcbnew.FromMM(width_mm))
        track.SetLayer(pcbnew.F_Cu)
        track.SetNet(first.GetNet())
        board.Add(track)
    for item in board.GetDrawings():
        if (isinstance(item, pcbnew.PCB_TEXT)
                and "INTEGRATED AUDIO + DAC CORE / MANUAL ROUTE STUDY" in item.GetText()):
            item.SetText("DISCHARGE RESISTOR FIT OPTION — NOT CAPTURE/BOM ALIGNED")
    title = board.GetTitleBlock()
    title.SetTitle("DAC-HPA — 120 × 100 mm discharge resistor fit option")
    title.SetComment(0, "R527/R529/R530 provisional 2512 body and lands")
    title.SetComment(1, "Not a captured BOM, routed power net or PCBA release")
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise RuntimeError("Could not refill L2 GND in the fit option")
    pcbnew.SaveBoard(str(output), board)
    print(f"Saved {output}: three hand-placed 2512 candidates and two local routes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
