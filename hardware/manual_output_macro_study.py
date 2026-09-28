#!/usr/bin/env python3
"""Build the explicit 270-degree output-macro route study from the ECO board.

Coordinates and copper waypoints below were selected by hand. This script
does not search, pack, place, or route automatically. The result is a separate
study board, not fabrication or PCBA release data.
"""

from __future__ import annotations

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_120x100_OUTPUT_MACRO_STUDY_ONLY.kicad_pcb"

# KiCad x/y in millimetres and counterclockwise footprint angle. Both dual
# amplifiers face the I/V stage on their input side and their local Rf/Cf on
# their output side. Links sit by the relevant relay contact.
MOVES = {
    "U401": (117.0, 79.0, 270), "U402": (129.0, 79.0, 270),
    "R417": (132.0, 97.2, 0), "R418": (129.4, 64.9, 0),
    "R419": (144.0, 83.4, 0), "R420": (144.2, 68.9, 0),
    "R402": (120.5, 76.5, 270), "C401": (122.2, 76.5, 270),
    "R406": (120.5, 81.5, 90), "C403": (122.2, 81.5, 90),
    "R410": (132.5, 76.5, 270), "C405": (134.2, 76.5, 270),
    "R414": (132.5, 81.5, 90), "C407": (134.2, 81.5, 90),
    "C402": (113.0, 78.0, 0), "R441": (113.0, 76.0, 0),
    "C433": (109.0, 84.0, 0), "C434": (112.5, 80.0, 0),
    "C435": (130.0, 73.0, 90), "R407": (112.5, 84.5, 90),
    "C413": (110.0, 89.5, 0), "C415": (128.0, 93.5, 0),
}

# Each pair uses a 0.932 mm, 0.25 mm-wide VSON output escape. All other
# feedback tracks are 0.20 mm. The load branch leaves the escape elbow;
# headphone current does not pass through the 0.20 mm Rf/Cf network.
FEEDBACK = {
    "N4_LP_INN": ((118.468, 78.0), (119.0, 78.0), (120.5, 75.675), (122.2, 75.725)),
    "N4_LP_OUT": ((118.468, 78.5), (119.4, 78.5), (120.5, 77.325), (122.2, 77.275)),
    "N4_LN_OUT": ((118.468, 79.5), (119.4, 79.5), (120.5, 80.675), (122.2, 80.725)),
    "N4_LN_INN": ((118.468, 80.0), (119.0, 80.0), (120.5, 82.325), (122.2, 82.275)),
    "N4_RP_INN": ((130.468, 78.0), (131.0, 78.0), (132.5, 75.675), (134.2, 75.725)),
    "N4_RP_OUT": ((130.468, 78.5), (131.4, 78.5), (132.5, 77.325), (134.2, 77.275)),
    "N4_RN_OUT": ((130.468, 79.5), (131.4, 79.5), (132.5, 80.675), (134.2, 80.725)),
    "N4_RN_INN": ((130.468, 80.0), (131.0, 80.0), (132.5, 82.325), (134.2, 82.275)),
}

RELAY_LEGS = {
    "LEG_LP": ((132.51, 97.2), (137.46, 97.2)),
    "LEG_LN": ((129.91, 64.9), (134.46, 64.9)),
    "LEG_RP": ((144.51, 83.4), (146.1, 83.4), (146.1, 97.2), (149.66, 97.2)),
    "LEG_RN": ((144.71, 68.9), (144.71, 66.8), (147.76, 63.9)),
}

# Layer, width in millimetres, and manually drawn waypoints. The L4 routes
# remain outside J701's underside keepout. L3 return and the complete output
# impedance/crosstalk budgets must be reviewed before they can be released.
LOAD_PATHS = (
    ("N4_LP_OUT", pcbnew.F_Cu, 0.5, ((119.4, 78.5), (120.0, 78.65))),
    ("N4_LP_OUT", pcbnew.B_Cu, 1.0, ((120.0, 78.65), (130.0, 99.5))),
    ("N4_LP_OUT", pcbnew.F_Cu, 0.5, ((130.0, 99.5), (131.49, 97.2))),
    ("N4_LN_OUT", pcbnew.F_Cu, 0.5, ((119.4, 79.5), (122.2, 79.5))),
    ("N4_LN_OUT", pcbnew.B_Cu, 1.0, ((122.2, 79.5), (127.0, 64.9))),
    ("N4_LN_OUT", pcbnew.F_Cu, 0.5, ((127.0, 64.9), (128.89, 64.9))),
    ("N4_RP_OUT", pcbnew.F_Cu, 0.5,
     ((131.4, 78.5), (135.7, 78.5), (135.7, 85.1),
      (142.0, 85.1), (143.49, 83.4))),
    ("N4_RN_OUT", pcbnew.F_Cu, 0.5, ((131.4, 79.5), (134.8, 79.5))),
    ("N4_RN_OUT", pcbnew.B_Cu, 1.0,
     ((134.8, 79.5), (136.5, 79.5), (136.5, 69.0), (142.5, 67.8))),
    ("N4_RN_OUT", pcbnew.F_Cu, 0.5, ((142.5, 67.8), (143.69, 68.9))),
)

SIGNAL_VIAS = (
    ("N4_LP_OUT", (120.0, 78.65)), ("N4_LP_OUT", (130.0, 99.5)),
    ("N4_LN_OUT", (122.2, 79.5)), ("N4_LN_OUT", (127.0, 64.9)),
    ("N4_RN_OUT", (134.8, 79.5)), ("N4_RN_OUT", (142.5, 67.8)),
)


def xy(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))


def draw(board: pcbnew.BOARD, net: str, points: tuple, layer: int,
         width_mm: float, first_width_mm: float | None = None) -> None:
    for index, (start, end) in enumerate(zip(points, points[1:])):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(xy(*start))
        track.SetEnd(xy(*end))
        track.SetWidth(pcbnew.FromMM(first_width_mm if index == 0 and first_width_mm else width_mm))
        track.SetLayer(layer)
        track.SetNet(board.FindNet(net))
        board.Add(track)


def main() -> None:
    board = pcbnew.LoadBoard(str(SOURCE))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if len(footprints) != 544 or len(board.GetTracks()) != 35 or len(board.Zones()) != 1:
        raise AssertionError("Source ECO board changed; review the manual macro study before regenerating")
    if any(t.GetNetname().startswith("LEG_") or t.GetNetname() in FEEDBACK
           for t in board.GetTracks()):
        raise AssertionError("Source already contains output-macro copper")
    for ref, (x_mm, y_mm, angle) in MOVES.items():
        footprint = footprints[ref]
        footprint.SetPosition(xy(x_mm, y_mm))
        footprint.SetOrientationDegrees(angle)
    for net, points in FEEDBACK.items():
        draw(board, net, points, pcbnew.F_Cu, 0.2,
             first_width_mm=0.25 if net.endswith("_OUT") else None)
    for net, points in RELAY_LEGS.items():
        draw(board, net, points, pcbnew.F_Cu, 1.0)
    for net, layer, width, points in LOAD_PATHS:
        draw(board, net, points, layer, width)
    for net, at in SIGNAL_VIAS:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(xy(*at))
        via.SetWidth(pcbnew.FromMM(0.6))
        via.SetDrill(pcbnew.FromMM(0.2))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(board.FindNet(net))
        board.Add(via)
    for drawing in board.GetDrawings():
        if (isinstance(drawing, pcbnew.PCB_TEXT)
                and drawing.GetText().startswith("FUNCTIONAL ECO / MANUAL PLACEMENT")):
            drawing.SetText("OUTPUT MACRO / MANUAL ROUTE STUDY — NO PCBA RELEASE")
    title = board.GetTitleBlock()
    title.SetTitle("DAC-HPA — 120 × 100 mm output macro study")
    title.SetComment(0, "Four amplifier-to-relay inputs and Rf/Cf only; jack/power routes open")
    title.SetComment(1, "Explicit manual coordinates; L4 return and audio budgets on hold")
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise RuntimeError("Could not refill continuous L2 GND around signal vias")
    pcbnew.SaveBoard(str(OUTPUT), board)
    print(f"Saved {OUTPUT.name}: {len(MOVES)} hand-moved footprints, four amplifier legs")


if __name__ == "__main__":
    main()
