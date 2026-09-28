#!/usr/bin/env python3
"""Make a board-only, unapproved two-TVS J702 fit and access study.

The schematic, BOM and primary PCB are not changed. The two added pads test
physical room for local RP/LP protection before an electrical ECO is accepted.
"""

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_J702_ESD_OPTION_ONLY.kicad_pcb"
FOOTPRINT_DIR = HERE / "JLC_Imported.pretty"
FOOTPRINT_NAME = "SOD-523_L1.2-W0.8-LS1.6-BI"

# (reference, signal net, x mm, y mm, orientation). D707 fits between K603
# and J702 with >1.5 mm body access to each; D708 fits below J702.
POSITIONS = (
    ("D707", "JACK_RP", 152.0, 102.3, 180),
    ("D708", "JACK_LP", 148.31, 117.1, 270),
)

# Hand-selected 0.5 mm L1 option traces. This is an exploratory RP relay
# path plus both short jack-to-TVS signals, not completed output routing.
RP_WAYPOINTS = (
    (154.74, 97.2), (154.74, 99.7), (152.75, 101.69),
    (152.75, 102.3), (152.75, 105.27), (152.12, 105.9),
)
LP_WAYPOINTS = ((148.31, 113.1), (148.31, 116.35))


def main() -> None:
    board = pcbnew.LoadBoard(str(SOURCE))
    if len(board.GetFootprints()) != 536:
        raise SystemExit("The placement source has changed")
    for ref, signal, x_mm, y_mm, angle in POSITIONS:
        fp = pcbnew.FootprintLoad(str(FOOTPRINT_DIR), FOOTPRINT_NAME)
        if fp is None:
            raise SystemExit(f"Missing {FOOTPRINT_NAME}")
        fp.SetReference(ref)
        fp.SetValue("LESD5D5.0CT1G — OPTION ONLY")
        fp.SetOrientationDegrees(angle)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
        for pad in fp.Pads():
            pad.SetNet(board.FindNet(signal if pad.GetNumber() == "1" else "GND"))
        board.Add(fp)
    for net_name, points in (("JACK_RP", RP_WAYPOINTS),
                             ("JACK_LP", LP_WAYPOINTS),
                             ("GND", ((151.25, 102.3), (150.2, 102.3))),
                             ("GND", ((148.31, 117.85), (148.31, 119.0)))):
        for start, end in zip(points, points[1:]):
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(start[0]), pcbnew.FromMM(start[1])))
            track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(end[0]), pcbnew.FromMM(end[1])))
            track.SetWidth(pcbnew.FromMM(0.5))
            track.SetLayer(pcbnew.F_Cu)
            track.SetNet(board.FindNet(net_name))
            board.Add(track)
    for x_mm, y_mm in ((150.2, 102.3), (148.31, 119.0)):
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
        via.SetWidth(pcbnew.FromMM(0.6))
        via.SetDrill(pcbnew.FromMM(0.2))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(board.FindNet("GND"))
        board.Add(via)
    for drawing in board.GetDrawings():
        if (isinstance(drawing, pcbnew.PCB_TEXT)
                and drawing.GetText().startswith("MACRO PLACEMENT V2")):
            drawing.SetText("J702 TWO-TVS OPTION — NO SCHEMATIC/BOM ECO")
    pcbnew.SaveBoard(str(OUTPUT), board)
    print(f"Saved {OUTPUT.name} with two unapproved J702 TVS fit/route options")


if __name__ == "__main__":
    main()
