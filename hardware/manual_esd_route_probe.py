#!/usr/bin/env python3
"""Draw four explicit J701-to-TVS escape routes for the 120 x 100 review.

These hand-selected straight copper segments check the provisional 4.2 mm
signal path in real KiCad geometry. Ground vias are placed immediately behind
the four TVS pads. The rest of the board remains unrouted; a filled L2 GND
plane and system IEC ESD test are still required.
"""

from __future__ import annotations

import math
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_120x100_CLOCK_ESCAPE_STUDY_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_120x100_ESD_ROUTE_PROBE_ONLY.kicad_pcb"

# Exact contact-to-clamp pairs; placement coordinates are selected in the
# preceding manual_top_access and manual_clock_escape scripts.
PAIRS = {"D701": "7", "D702": "5", "D703": "6", "D704": "2"}


def add_track(board: pcbnew.BOARD, start: pcbnew.VECTOR2I,
              end: pcbnew.VECTOR2I, net_code: int, width_mm: float) -> float:
    segment = pcbnew.PCB_TRACK(board)
    segment.SetStart(start)
    segment.SetEnd(end)
    segment.SetWidth(pcbnew.FromMM(width_mm))
    segment.SetLayer(pcbnew.F_Cu)
    segment.SetNetCode(net_code)
    board.Add(segment)
    return math.hypot(pcbnew.ToMM(end.x - start.x),
                      pcbnew.ToMM(end.y - start.y))


def main() -> None:
    board = pcbnew.LoadBoard(str(SOURCE))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    j701 = {pad.GetNumber(): pad for pad in footprints["J701"].Pads()}
    gnd_code = board.FindNet("GND").GetNetCode()
    if board.GetTracks():
        raise SystemExit("ESD route probe requires an unrouted source board")

    for ref, jack_pin in PAIRS.items():
        diode = {pad.GetNumber(): pad for pad in footprints[ref].Pads()}
        signal = diode["1"]
        jack = j701[jack_pin]
        if signal.GetNetCode() != jack.GetNetCode():
            raise SystemExit(f"{ref} and J701.{jack_pin} are not the same net")
        length = add_track(board, signal.GetPosition(), jack.GetPosition(),
                           signal.GetNetCode(), 0.5)
        if length > 4.2 + 1e-6:
            raise SystemExit(f"{ref} signal route is {length:.3f} mm")

        ground = diode["2"]
        if ground.GetNetCode() != gnd_code:
            raise SystemExit(f"{ref} pad 2 is not GND")
        behind = -1.02 if ref in {"D701", "D702"} else 1.02
        via_at = pcbnew.VECTOR2I(ground.GetPosition().x,
                                  ground.GetPosition().y - pcbnew.FromMM(behind))
        add_track(board, ground.GetPosition(), via_at, gnd_code, 0.5)
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(via_at)
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetWidth(pcbnew.FromMM(0.6))
        via.SetDrill(pcbnew.FromMM(0.2))
        via.SetNetCode(gnd_code)
        board.Add(via)
        print(f"{ref} to J701.{jack_pin}: {length:.3f} mm signal, 1.020 mm ground stub")

    # The owner-approved layer plan uses L2 as the continuous GND reference.
    # Add its full-board polygon here so the four ground vias have a return;
    # KiCad fills the zone during the subsequent DRC/export step.
    plane = pcbnew.ZONE(board)
    plane.SetLayer(pcbnew.In1_Cu)
    plane.SetNetCode(gnd_code)
    plane.SetZoneName("continuous_L2_GND_review")
    plane.SetLocalClearance(pcbnew.FromMM(0.5))
    outline = plane.Outline()
    outline.NewOutline()
    for x, y in ((40, 40), (160, 40), (160, 140), (40, 140)):
        outline.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    board.Add(plane)

    title = board.GetTitleBlock()
    title.SetTitle("DAC-HPA — 120 × 100 mm manual layout review")
    title.SetRevision("v1.1 partial routing review")
    title.SetDate("2026-09-27")
    title.SetComment(0, "J701 TVS escapes and L2 GND only; 499 other connections open")
    for drawing in board.GetDrawings():
        if isinstance(drawing, pcbnew.PCB_TEXT) and "NO FABRICATION OUTPUT" in drawing.GetText():
            drawing.SetText("MANUAL LAYOUT REVIEW — PARTIAL ROUTE — NO FABRICATION OUTPUT")

    pcbnew.SaveBoard(str(OUTPUT), board)
    print(f"Saved {OUTPUT.name}; this is a partial route probe, not a routed PCB")


if __name__ == "__main__":
    main()
