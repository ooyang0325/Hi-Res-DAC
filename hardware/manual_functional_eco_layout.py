#!/usr/bin/env python3
"""Hand-place the functional ECO on the 120 x 100 mm macro study.

Every new position and copper waypoint in this file is selected explicitly.
The code only copies approved schematic pin/net data to the named footprints;
it does not search for, optimize, or automatically route a placement. The old
macro board stays as a historical comparison, not current order data.
"""

from __future__ import annotations

from pathlib import Path

import pcbnew

import place_board


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb"
STOCK_FOOTPRINTS = Path(
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
    if Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints").exists()
    else "/usr/share/kicad/footprints"
)

# Explicit KiCad-coordinate positions, in millimetres. The U621 high-impedance
# inputs sit by U605; buffered outputs can travel back to the MCU. D707/D708
# reuse the previously DRC-screened local J702 protection positions.
NEW_POSITIONS: dict[str, tuple[float, float, int]] = {
    "U621": (68.0, 87.5, 0),
    "C667": (70.2, 87.5, 270),
    "R952": (64.0, 86.5, 0),
    "R953": (64.0, 88.5, 0),
    "R954": (62.0, 75.0, 0),
    "R955": (66.0, 75.0, 0),
    "D707": (152.0, 102.3, 180),
    "D708": (148.31, 117.1, 270),
}

# Two existing input isolators are moved beside the corresponding supervisor
# output/gate region. Their changed pad-2 nets are the only old-pad changes in
# this ECO; every other old footprint keeps its approved pin-to-net mapping.
EXISTING_MOVES: dict[str, tuple[float, float, int]] = {
    "R688": (67.0, 90.5, 90),
    "R689": (69.5, 90.5, 90),
    # Five DAC high-frequency bypasses form a short row at their actual rail
    # pins; bulk parts stay one row behind rather than blocking the escape.
    "C309": (87.7, 76.2, 90),
    "C308": (89.1, 76.2, 90),
    "C307": (90.5, 76.2, 90),
    "C306": (91.9, 76.2, 90),
    "C305": (93.3, 76.2, 90),
    "C303": (91.9, 72.5, 90),
    "C304": (89.2, 72.5, 90),
    "R301": (93.0, 67.5, 90),
    # Relocate the I/V hold-up reservoirs and isolating diodes south-east,
    # leaving a copper passage below K601 for the J702 audio trunk.
    "C442": (139.0, 120.5, 180),
    "C443": (141.5, 129.5, 0),
    "D411": (138.0, 116.0, 0),
    "D412": (140.0, 125.0, 180),
}
EXPECTED_RENET = {("R688", "2"), ("R689", "2")}

# Explicit L1 local TVS copper. This is the previously reviewed J702 option's
# short jack branches, plus one RP relay-to-jack probe. The LP relay route,
# other audio legs and complete sleeve current return remain undrawn.
RP_TVS_WAYPOINTS = (
    (154.74, 97.2), (154.74, 99.7), (152.75, 101.69),
    (152.75, 102.3), (152.75, 105.27), (152.12, 105.9),
)
LP_TVS_WAYPOINTS = ((148.31, 113.1), (148.31, 116.35))
GROUND_TVS_WAYPOINTS = (
    ((151.25, 102.3), (150.2, 102.3)),
    ((148.31, 117.85), (148.31, 119.0)),
)
GROUND_TVS_VIAS = ((150.2, 102.3), (148.31, 119.0))


def pos(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))


def ensure_net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    existing = board.FindNet(name)
    if existing is not None:
        return existing
    created = pcbnew.NETINFO_ITEM(board, name)
    board.Add(created)
    return created


def load_footprint(identifier: str) -> pcbnew.FOOTPRINT:
    nickname, name = identifier.split(":", 1)
    folder = (HERE / f"{nickname}.pretty"
              if nickname in {"DAC_HPA", "JLC_Imported"}
              else STOCK_FOOTPRINTS / f"{nickname}.pretty")
    loaded = pcbnew.FootprintLoad(str(folder), name)
    if loaded is None:
        raise FileNotFoundError(f"Missing footprint {identifier} in {folder}")
    loaded.SetFPID(pcbnew.LIB_ID(nickname, name))
    return loaded


def main() -> None:
    board = pcbnew.LoadBoard(str(SOURCE))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if len(footprints) != 536:
        raise AssertionError(f"Historical macro source changed: {len(footprints)} footprints")
    root = place_board.netlist_xml()
    components = {component.get("ref"): component
                  for component in root.findall("./components/comp")}
    expected_board_refs = {
        ref for ref, component in components.items()
        if component.find("property[@name='exclude_from_board']") is None
    }
    desired_pad_nets = {
        (node.get("ref"), node.get("pin")): net.get("name")
        for net in root.findall("./nets/net")
        if not (net.get("name") or "").startswith("unconnected-")
        for node in net.findall("node")
    }
    actual_new = expected_board_refs - set(footprints)
    if actual_new != set(NEW_POSITIONS):
        raise AssertionError(f"Functional ECO footprint set differs: {sorted(actual_new ^ set(NEW_POSITIONS))}")
    if set(footprints) - expected_board_refs:
        raise AssertionError("Historical macro has footprints absent from current schematic")

    changed: set[tuple[str, str]] = set()
    for ref, fp in footprints.items():
        for pad in fp.Pads():
            pad_number = pad.GetNumber()
            wanted = desired_pad_nets.get((ref, pad_number))
            if not pad_number or wanted is None:
                continue
            if pad.GetNetname() != wanted:
                changed.add((ref, pad_number))
                pad.SetNet(ensure_net(board, wanted))
    if changed != EXPECTED_RENET:
        raise AssertionError(f"Unexpected existing-pad net changes: {sorted(changed ^ EXPECTED_RENET)}")

    for ref, (x_mm, y_mm, angle) in EXISTING_MOVES.items():
        fp = footprints[ref]
        fp.SetOrientationDegrees(angle)
        fp.SetPosition(pos(x_mm, y_mm))

    for ref, (x_mm, y_mm, angle) in NEW_POSITIONS.items():
        component = components[ref]
        identifier = component.findtext("footprint") or ""
        if not identifier:
            raise AssertionError(f"Schematic has no footprint for {ref}")
        fp = load_footprint(identifier)
        fp.SetReference(ref)
        fp.SetValue(component.findtext("value") or "")
        fp.SetOrientationDegrees(angle)
        fp.SetPosition(pos(x_mm, y_mm))
        # These small parts sit beside the MCU/supervisor and jack body.
        # Keep their reference text in F.Fab for assembly review without
        # clipping nearby solder masks or another package's silkscreen.
        fp.Reference().SetLayer(pcbnew.F_Fab)
        expected = {pin: net for (node_ref, pin), net in desired_pad_nets.items()
                    if node_ref == ref}
        numbered_pads = {pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}
        if numbered_pads != set(expected):
            raise AssertionError(f"{ref} {identifier} pad numbers differ: {numbered_pads ^ set(expected)}")
        for pad in fp.Pads():
            if pad.GetNumber() and pad.GetNumber() in expected:
                pad.SetNet(ensure_net(board, expected[pad.GetNumber()]))
        board.Add(fp)

    for net_name, points in (
        ("JACK_RP", RP_TVS_WAYPOINTS),
        ("JACK_LP", LP_TVS_WAYPOINTS),
        *(("GND", points) for points in GROUND_TVS_WAYPOINTS),
    ):
        for start, end in zip(points, points[1:]):
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(pos(*start))
            track.SetEnd(pos(*end))
            track.SetWidth(pcbnew.FromMM(0.5))
            track.SetLayer(pcbnew.F_Cu)
            track.SetNet(ensure_net(board, net_name))
            board.Add(track)
    for x_mm, y_mm in GROUND_TVS_VIAS:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pos(x_mm, y_mm))
        via.SetWidth(pcbnew.FromMM(0.6))
        via.SetDrill(pcbnew.FromMM(0.2))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(ensure_net(board, "GND"))
        board.Add(via)

    for drawing in board.GetDrawings():
        if (isinstance(drawing, pcbnew.PCB_TEXT)
                and drawing.GetText().startswith("MACRO PLACEMENT V2")):
            drawing.SetText("FUNCTIONAL ECO / MANUAL PLACEMENT — REVIEW ONLY")
    pcbnew.SaveBoard(str(OUTPUT), board)
    print(f"Saved {OUTPUT.name}: {len(board.GetFootprints())} footprints, "
          f"{len(NEW_POSITIONS)} manually located ECO parts")


if __name__ == "__main__":
    main()
