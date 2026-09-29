#!/usr/bin/env python3
"""Replay the engineer-selected integrated audio board; no placement search.

INTEGRATED_AUDIO_MANUAL_DELTA.json is a frozen record extracted from the
reviewed hand placement and copper. This script applies those exact moves and
segments to the schematic-aligned ECO board, then refills L2 GND. The output
is still review-only and has no fabrication approval.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "INTEGRATED_AUDIO_MANUAL_DELTA.json"


def xy(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))


def copper_item(item: pcbnew.BOARD_CONNECTED_ITEM) -> tuple:
    """Identify source copper exactly before replacing hand-picked bends."""
    if isinstance(item, pcbnew.PCB_VIA):
        at = item.GetPosition()
        return ("via", item.GetNetname(), round(pcbnew.ToMM(at.x), 4),
                round(pcbnew.ToMM(at.y), 4),
                round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 4),
                round(pcbnew.ToMM(item.GetDrillValue()), 4),
                bool(item.GetPrimaryDrillFilledFlag()),
                bool(item.GetPrimaryDrillCappedFlag()))
    a, b = item.GetStart(), item.GetEnd()
    return ("track", item.GetNetname(), item.GetLayerName(),
            round(pcbnew.ToMM(a.x), 4), round(pcbnew.ToMM(a.y), 4),
            round(pcbnew.ToMM(b.x), 4), round(pcbnew.ToMM(b.y), 4),
            round(pcbnew.ToMM(item.GetWidth()), 4))


def manifest_item(item: dict) -> tuple:
    if item["kind"] == "via":
        return ("via", item["net"], *item["at_mm"],
                item["diameter_mm"], item["drill_mm"],
                bool(item.get("filled", False)), bool(item.get("capped", False)))
    return ("track", item["net"], item["layer"],
            *item["start_mm"], *item["end_mm"], item["width_mm"])


def build(output_path: Path) -> None:
    record = json.loads(MANIFEST.read_text())
    source = HERE / record["source_board"]
    board = pcbnew.LoadBoard(str(source))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    if (len(footprints) != record["source_footprints"]
            or len(board.GetTracks()) != record["source_track_and_via_items"]
            or len(board.Zones()) != 1):
        raise AssertionError("ECO source geometry changed; review the manual delta before replay")
    source_tracks = board.GetTracks()
    to_remove = []
    for removed in record.get("removed_source_copper", []):
        wanted = manifest_item(removed)
        matches = [item for item in source_tracks
                   if copper_item(item) == wanted]
        if len(matches) != 1:
            raise AssertionError(f"Source copper to replace changed: {removed}")
        source_tracks.remove(matches[0])
        to_remove.append(matches[0])
    for item in to_remove:
        board.Remove(item)
    for ref, (x_mm, y_mm, angle) in record["moved_footprints"].items():
        footprint = footprints[ref]
        footprint.SetPosition(xy(x_mm, y_mm))
        footprint.SetOrientationDegrees(angle)
    for item in record["added_copper"]:
        net = board.FindNet(item["net"])
        if net is None:
            raise AssertionError(f"Missing ECO net {item['net']}")
        if item["kind"] == "track":
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(xy(*item["start_mm"]))
            track.SetEnd(xy(*item["end_mm"]))
            track.SetWidth(pcbnew.FromMM(item["width_mm"]))
            track.SetLayer(board.GetLayerID(item["layer"]))
            track.SetNet(net)
            board.Add(track)
        elif item["kind"] == "via":
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(xy(*item["at_mm"]))
            via.SetWidth(pcbnew.FromMM(item["diameter_mm"]))
            via.SetDrill(pcbnew.FromMM(item["drill_mm"]))
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(net)
            via.SetPrimaryDrillFilledFlag(bool(item.get("filled", False)))
            via.SetPrimaryDrillCappedFlag(bool(item.get("capped", False)))
            board.Add(via)
        else:
            raise AssertionError(f"Unsupported manual item: {item['kind']}")
    for drawing in board.GetDrawings():
        if (isinstance(drawing, pcbnew.PCB_TEXT)
                and drawing.GetText().startswith("FUNCTIONAL ECO / MANUAL PLACEMENT")):
            drawing.SetText("INTEGRATED AUDIO + DAC CORE / MANUAL ROUTE STUDY — NO PCBA RELEASE")
    title = board.GetTitleBlock()
    title.SetTitle("DAC-HPA — 120 × 100 mm integrated audio study")
    title.SetComment(0, "DAC/CPLD clocks, LDO loops, I/V, amplifiers and jacks under study")
    title.SetComment(1, "Main feeds, via process, returns, stability and R-15 HOLD")
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise RuntimeError("Could not refill continuous L2 GND around the signal vias")
    pcbnew.SaveBoard(str(output_path), board)
    print(f"Saved {output_path.name}: {len(record['moved_footprints'])} explicit moves, "
          f"{len(record['added_copper'])} explicit copper items")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=HERE / "DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb")
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
