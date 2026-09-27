#!/usr/bin/env python3
"""Read-only check of the four hand-routed J701 TVS escapes and L2 return."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


PAIRS = {"D701": "7", "D702": "5", "D703": "6", "D704": "2"}
MAX_SIGNAL_MM = 4.2  # owner-approved provisional limit, subject to system ESD test
MAX_GND_STUB_MM = 1.1


def near(a: pcbnew.VECTOR2I, b: pcbnew.VECTOR2I) -> bool:
    return a.x == b.x and a.y == b.y


def audit(path: Path) -> dict:
    board = pcbnew.LoadBoard(str(path))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    jack = {pad.GetNumber(): pad for pad in fps["J701"].Pads()}
    tracks = [item for item in board.GetTracks()
              if isinstance(item, pcbnew.PCB_TRACK)
              and not isinstance(item, pcbnew.PCB_VIA)]
    vias = [item for item in board.GetTracks() if isinstance(item, pcbnew.PCB_VIA)]
    gnd_zone = [zone for zone in board.Zones()
                if zone.GetNetname() == "GND" and zone.GetLayer() == pcbnew.In1_Cu
                and zone.HasFilledPolysForLayer(pcbnew.In1_Cu)]
    if len(gnd_zone) != 1 or gnd_zone[0].GetFilledPolysList(pcbnew.In1_Cu).OutlineCount() != 1:
        raise SystemExit("L2 GND must contain one filled continuous polygon")

    results = {}
    for ref, jack_pin in PAIRS.items():
        pads = {pad.GetNumber(): pad for pad in fps[ref].Pads()}
        signal, ground, contact = pads["1"], pads["2"], jack[jack_pin]
        matching = [track for track in tracks
                    if track.GetNetCode() == signal.GetNetCode()
                    and {tuple(track.GetStart()), tuple(track.GetEnd())}
                    == {tuple(signal.GetPosition()), tuple(contact.GetPosition())}]
        if len(matching) != 1:
            raise SystemExit(f"Missing unique direct {ref} to J701.{jack_pin} track")
        segment = matching[0]
        length = pcbnew.ToMM(segment.GetLength())
        if length > MAX_SIGNAL_MM + 1e-6 or pcbnew.ToMM(segment.GetWidth()) < 0.5:
            raise SystemExit(f"{ref} TVS signal escape violates width/length target")

        stubs = [track for track in tracks
                 if track.GetNetname() == "GND"
                 and (near(track.GetStart(), ground.GetPosition())
                      or near(track.GetEnd(), ground.GetPosition()))]
        if len(stubs) != 1:
            raise SystemExit(f"Missing unique {ref} ground stub")
        stub = stubs[0]
        other_end = (stub.GetEnd() if near(stub.GetStart(), ground.GetPosition())
                     else stub.GetStart())
        matching_vias = [via for via in vias
                         if via.GetNetname() == "GND" and near(via.GetPosition(), other_end)]
        if (len(matching_vias) != 1
                or pcbnew.ToMM(stub.GetLength()) > MAX_GND_STUB_MM
                or pcbnew.ToMM(stub.GetWidth()) < 0.5
                or pcbnew.ToMM(matching_vias[0].GetWidth(pcbnew.F_Cu)) < 0.6
                or pcbnew.ToMM(matching_vias[0].GetDrillValue()) < 0.2):
            raise SystemExit(f"{ref} ground return violates stub/via target")
        results[ref] = {"jack_pad": jack_pin,
                        "signal_length_mm": round(length, 3),
                        "ground_stub_mm": round(pcbnew.ToMM(stub.GetLength()), 3)}

    return {"board": str(path), "esd_limit_mm": MAX_SIGNAL_MM,
            "routes": results, "track_count": len(tracks), "via_count": len(vias),
            "l2_gnd_filled_polygon_count": 1,
            "l2_gnd_filled_area_mm2": round(gnd_zone[0].GetFilledArea() / 1e12, 2),
            "release": "HOLD: system IEC ESD test and full routing pending"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.board), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
