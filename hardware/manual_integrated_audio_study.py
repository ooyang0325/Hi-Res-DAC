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
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
MAC_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
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


def load_footprint(path: Path) -> pcbnew.FOOTPRINT:
    """Library footprint via a one-footprint wrapper board (FootprintLoad is unusable in KiCad 10 SWIG)."""
    wrapper = ('(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0") '
               '(general (thickness 1.6)) (paper "A4") (layers (0 "F.Cu" signal) (2 "B.Cu" signal) '
               '(13 "F.Paste" user) (1 "F.Mask" user) (5 "F.SilkS" user) (31 "F.CrtYd" user) '
               '(35 "F.Fab" user) (25 "Edge.Cuts" user)) (setup) (net 0 "")\n'
               + path.read_text() + ')\n')
    with tempfile.TemporaryDirectory() as tmp:
        board_path = Path(tmp) / "fp.kicad_pcb"
        board_path.write_text(wrapper)
        footprints = list(pcbnew.LoadBoard(str(board_path)).GetFootprints())
    if len(footprints) != 1:
        raise AssertionError(f"Could not load footprint {path}")
    return pcbnew.FOOTPRINT(footprints[0])


def build(output_path: Path) -> None:
    record = json.loads(MANIFEST.read_text())
    source = HERE / record["source_board"]
    board = pcbnew.LoadBoard(str(source))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    if (len(footprints) != record["source_footprints"]
            or len(board.GetTracks()) != record["source_track_and_via_items"]
            or len(board.Zones()) != 1):
        raise AssertionError("ECO source geometry changed; review the manual delta before replay")
    if record.get("copper_layers", 4) == 6:
        # 6-layer stack: L4 signal (In3 "SIG") and L5 solid GND plane (In4 "GND5") under the
        # unchanged L1 signal / L2 GND / L3 PWR layers; L4 and B.Cu both reference L5.
        board.SetCopperLayerCount(6)
        board.SetLayerName(pcbnew.In3_Cu, "SIG")
        board.SetLayerName(pcbnew.In4_Cu, "GND5")
        board.SetLayerType(pcbnew.In4_Cu, pcbnew.LT_POWER)
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
    for ref, spec in record.get("swapped_footprints", {}).items():
        # Footprint replaced by a reviewed part (same pad numbers and nets).
        old = footprints[ref]
        lib, name = spec["footprint"].split(":")
        new = load_footprint(HERE / f"{lib}.pretty" / f"{name}.kicad_mod")
        nets = {pad.GetNumber(): pad.GetNet() for pad in old.Pads()}
        if sorted(nets) != sorted(pad.GetNumber() for pad in new.Pads()):
            raise AssertionError(f"{ref}: pad numbers differ from {spec['footprint']}")
        new.SetFPID(pcbnew.LIB_ID(lib, name))
        new.SetReference(ref)
        new.SetValue(spec["value"])
        for field, text in spec.get("fields", {}).items():
            new.SetField(field, text)
        new.SetPath(old.GetPath())
        new.SetPosition(old.GetPosition())
        new.SetOrientation(old.GetOrientation())
        for pad in new.Pads():
            pad.SetNet(nets[pad.GetNumber()])
        board.Remove(old)
        board.Add(new)
        footprints[ref] = new
    for ref, pad_nets in record.get("renamed_pads", {}).items():
        # Layout-driven pin swaps captured in the schematic ECO overlay.
        pads = {pad.GetNumber(): pad for pad in footprints[ref].Pads()}
        for number, net_name in pad_nets.items():
            if net_name:
                net = board.FindNet(net_name)
                if net is None:
                    raise AssertionError(f"Missing pin-swap net {net_name}")
                pads[number].SetNet(net)
            else:
                pads[number].SetNetCode(0)
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
    if "l2_clearance_mm" in record:
        # Smaller L2 antipads keep the single GND plane less perforated.
        board.Zones()[0].SetLocalClearance(pcbnew.FromMM(record["l2_clearance_mm"]))
    for item in record.get("added_zones", []):
        # GND pours on L1/L3/L4; L2 remains the single source plane.
        zone = pcbnew.ZONE(board)
        zone.SetLayer(board.GetLayerID(item["layer"]))
        zone.SetNet(board.FindNet(item["net"]))
        outline = zone.Outline()
        outline.NewOutline()
        for x_mm, y_mm in item["outline_mm"]:
            outline.Append(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))
        zone.SetLocalClearance(pcbnew.FromMM(item["clearance_mm"]))
        zone.SetMinThickness(pcbnew.FromMM(item["min_width_mm"]))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        zone.SetThermalReliefGap(pcbnew.FromMM(item.get("thermal_gap_mm", 0.3)))
        zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(item.get("spoke_mm", 0.4)))
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        zone.SetAssignedPriority(item.get("priority", 0))
        board.Add(zone)
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
    refill_with_custom_rules(output_path)
    print(f"Saved {output_path.name}: {len(record['moved_footprints'])} explicit moves, "
          f"{len(record['added_copper'])} explicit copper items")


def refill_with_custom_rules(path: Path) -> None:
    """Refill every pour with kicad-cli, whose filler honours the .kicad_dru pour
    clearances (high-impedance nodes and the USB pair to GND pour); the pcbnew
    scripting filler used above does not load the custom rules."""
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or MAC_CLI
    if not Path(cli).exists() and not shutil.which(cli):
        raise RuntimeError("kicad-cli is required to refill the pours with the custom rules")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([cli, "pcb", "drc", "--refill-zones", "--save-board", "--format", "json",
                        "-o", str(Path(tmp) / "fill.json"), str(path)], check=True, capture_output=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=HERE / "DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb")
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
