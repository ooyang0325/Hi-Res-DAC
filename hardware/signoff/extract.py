"""Extract a tool-independent geometry model from a KiCad 10 board.

This is the only module that imports ``pcbnew``.  Everything downstream works
on the plain dictionary it produces, so the gates can be reviewed, re-run and
unit-tested without KiCad in the loop.

Usage:
    <kicad>/bin/python extract.py <board.kicad_pcb> -o model.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import pcbnew

NM = 1e-6  # nanometres -> millimetres


def mm(value: int) -> float:
    return round(value * NM, 6)


def pt(vec) -> list:
    return [round(vec.x * NM, 6), round(vec.y * NM, 6)]


PAD_SHAPES = {
    0: "circle",
    1: "rect",
    2: "oval",
    3: "trapezoid",
    4: "roundrect",
    5: "chamfered_rect",
    6: "custom",
}
PAD_ATTRS = {0: "pth", 1: "smd", 2: "conn", 3: "npth"}
VIA_TYPES = {0: "undefined", 1: "microvia", 2: "blind", 3: "buried", 4: "through"}


def corner_radius_mm(pad) -> float:
    """Corner radius of a rounded/chamfered rectangular pad, in mm.

    Needed so clearance is measured to the pad's real outline: treating a
    roundrect as a sharp rectangle understates the corner gap and reports
    clearance violations that the fabricator would not see.
    """
    try:
        if int(pad.GetShape()) not in (4, 5):
            return 0.0
        return round(pad.GetRoundRectCornerRadius() * NM, 6)
    except Exception:
        return 0.0


def layer_names(board, layer_set) -> list:
    return [board.GetLayerName(l) for l in layer_set.Seq()]


def extract_stackup(board) -> dict:
    """Read the physical stackup if the designer defined one.

    KiCad only writes a ``(stackup ...)`` block when the board setup dialog has
    been used.  Its absence is itself a reportable condition, because without
    it the fabricator picks the dielectric heights and no impedance target can
    be held.
    """
    ds = board.GetDesignSettings()
    info = {
        "board_thickness_mm": mm(ds.GetBoardThickness()),
        "defined": False,
        "layers": [],
    }
    try:
        su = ds.GetStackupDescriptor()
        rows = []
        for item in su.GetList():
            rows.append(
                {
                    "type": int(item.GetType()),
                    "layer": board.GetLayerName(item.GetBrdLayerId())
                    if item.GetBrdLayerId() >= 0
                    else None,
                    "thickness_mm": mm(item.GetThickness()),
                    "epsilon_r": item.GetEpsilonR(),
                    "loss_tangent": item.GetLossTangent(),
                    "material": item.GetMaterial(),
                }
            )
        if rows:
            info["defined"] = True
            info["layers"] = rows
    except Exception as exc:  # noqa: BLE001 - SWIG surface varies by build
        info["probe_error"] = repr(exc)
    return info


def extract_project(pcb_path: str) -> dict:
    """Pull netclasses and design rules out of the sibling .kicad_pro."""
    pro = os.path.splitext(pcb_path)[0] + ".kicad_pro"
    if not os.path.exists(pro):
        return {"present": False}
    with open(pro, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    board = data.get("board", {})
    nets = data.get("net_settings", {})
    return {
        "present": True,
        "path": os.path.basename(pro),
        "design_rules": board.get("design_settings", {}).get("rules", {}),
        "stackup": board.get("design_settings", {}).get("stackup"),
        "netclasses": nets.get("classes", []),
        "netclass_patterns": nets.get("netclass_patterns", []),
    }


def extract(pcb_path: str) -> dict:
    board = pcbnew.LoadBoard(pcb_path)

    cu_layers = []
    for lid in board.GetEnabledLayers().CuStack():
        cu_layers.append({"id": int(lid), "name": board.GetLayerName(lid)})

    model = {
        "schema": 1,
        "source": os.path.basename(pcb_path),
        "kicad_version": pcbnew.GetBuildVersion(),
        "copper_layers": cu_layers,
        "copper_layer_count": board.GetCopperLayerCount(),
        "stackup": extract_stackup(board),
        "project": extract_project(pcb_path),
    }

    bb = board.GetBoardEdgesBoundingBox()
    model["outline"] = {
        "bbox_mm": [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())],
        "width_mm": mm(bb.GetWidth()),
        "height_mm": mm(bb.GetHeight()),
        "polygons": [],
    }
    try:
        sps = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(sps, False)
        for i in range(sps.OutlineCount()):
            o = sps.Outline(i)
            model["outline"]["polygons"].append(
                [[round(o.CPoint(j).x * NM, 6), round(o.CPoint(j).y * NM, 6)]
                 for j in range(o.PointCount())]
            )
    except Exception as exc:  # noqa: BLE001
        model["outline"]["probe_error"] = repr(exc)

    # ---- nets -------------------------------------------------------------
    nets = {}
    for code, ni in board.GetNetsByNetcode().items():
        nets[int(code)] = ni.GetNetname()
    model["nets"] = {str(k): v for k, v in sorted(nets.items())}

    # ---- footprints and pads ---------------------------------------------
    fps = []
    pads = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        attrs = int(fp.GetAttributes())
        fbb = fp.GetBoundingBox(False, False)
        entry = {
            "ref": ref,
            "value": fp.GetValue(),
            "library": fp.GetFPIDAsString(),
            "layer": board.GetLayerName(fp.GetLayer()),
            "pos_mm": pt(fp.GetPosition()),
            "orientation_deg": fp.GetOrientationDegrees(),
            "attributes": attrs,
            "is_smd": bool(attrs & pcbnew.FP_SMD),
            "is_tht": bool(attrs & pcbnew.FP_THROUGH_HOLE),
            "dnp": bool(attrs & pcbnew.FP_DNP),
            "exclude_from_bom": bool(attrs & pcbnew.FP_EXCLUDE_FROM_BOM),
            "exclude_from_pos": bool(attrs & pcbnew.FP_EXCLUDE_FROM_POS_FILES),
            "bbox_mm": [mm(fbb.GetLeft()), mm(fbb.GetTop()),
                        mm(fbb.GetRight()), mm(fbb.GetBottom())],
            "sheetname": fp.GetSheetname(),
            "courtyard": {},
        }
        for side, lay in (("front", pcbnew.F_CrtYd), ("back", pcbnew.B_CrtYd)):
            try:
                poly = fp.GetCourtyard(lay)
                rings = []
                for i in range(poly.OutlineCount()):
                    o = poly.Outline(i)
                    rings.append([[round(o.CPoint(j).x * NM, 6),
                                   round(o.CPoint(j).y * NM, 6)]
                                  for j in range(o.PointCount())])
                if rings:
                    entry["courtyard"][side] = rings
            except Exception:  # noqa: BLE001
                pass
        fps.append(entry)

        for pad in fp.Pads():
            size = pad.GetSize()
            drill_x = pad.GetDrillSizeX()
            drill_y = pad.GetDrillSizeY()
            pads.append(
                {
                    "ref": ref,
                    "pad": pad.GetNumber(),
                    "net": pad.GetNetname(),
                    "net_code": int(pad.GetNetCode()),
                    "pos_mm": pt(pad.GetPosition()),
                    "size_mm": [mm(size.x), mm(size.y)],
                    "shape": PAD_SHAPES.get(int(pad.GetShape()), "other"),
                    "attr": PAD_ATTRS.get(int(pad.GetAttribute()), "other"),
                    "corner_radius_mm": corner_radius_mm(pad),
                    "orientation_deg": pad.GetOrientationDegrees(),
                    "drill_mm": [mm(drill_x), mm(drill_y)],
                    "layers": layer_names(board, pad.GetLayerSet()),
                    "on_copper": [l for l in layer_names(board, pad.GetLayerSet())
                                  if l in {c["name"] for c in cu_layers}],
                }
            )
    model["footprints"] = fps
    model["pads"] = pads

    # ---- tracks and vias --------------------------------------------------
    tracks = []
    vias = []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            top, bottom = t.TopLayer(), t.BottomLayer()
            vias.append(
                {
                    "net": t.GetNetname(),
                    "net_code": int(t.GetNetCode()),
                    "pos_mm": pt(t.GetPosition()),
                    "diameter_mm": mm(t.GetWidth(top)),
                    "drill_mm": mm(t.GetDrillValue()),
                    "type": VIA_TYPES.get(int(t.GetViaType()), "other"),
                    "top_layer": board.GetLayerName(top),
                    "bottom_layer": board.GetLayerName(bottom),
                    "tented": bool(t.IsTented(pcbnew.F_Mask))
                    if hasattr(t, "IsTented") else None,
                }
            )
        else:
            tracks.append(
                {
                    "net": t.GetNetname(),
                    "net_code": int(t.GetNetCode()),
                    "layer": board.GetLayerName(t.GetLayer()),
                    "width_mm": mm(t.GetWidth()),
                    "start_mm": pt(t.GetStart()),
                    "end_mm": pt(t.GetEnd()),
                    "length_mm": round(t.GetLength() * NM, 6),
                }
            )
    model["tracks"] = tracks
    model["vias"] = vias

    # ---- zones ------------------------------------------------------------
    zones = []
    for z in board.Zones():
        for lid in z.GetLayerSet().Seq():
            entry = {
                "net": z.GetNetname(),
                "layer": board.GetLayerName(lid),
                "is_rule_area": bool(z.GetIsRuleArea()),
                "filled_polygons": [],
            }
            try:
                sps = z.GetFilledPolysList(lid)
                for i in range(sps.OutlineCount()):
                    o = sps.Outline(i)
                    entry["filled_polygons"].append(
                        [[round(o.CPoint(j).x * NM, 4), round(o.CPoint(j).y * NM, 4)]
                         for j in range(o.PointCount())]
                    )
            except Exception as exc:  # noqa: BLE001
                entry["probe_error"] = repr(exc)
            zones.append(entry)
    model["zones"] = zones

    # ---- silkscreen -------------------------------------------------------
    # KiCad 10 renamed these layers to "F.Silkscreen"/"B.Silkscreen", so match
    # on the layer id rather than the display name.
    silk_ids = {int(pcbnew.F_SilkS), int(pcbnew.B_SilkS)}
    text_classes = {"PCB_TEXT", "FP_TEXT", "PCB_TEXTBOX", "FP_TEXTBOX"}
    silk = []

    def add_silk(item_obj, ref=None):
        lid = int(item_obj.GetLayer())
        if lid not in silk_ids:
            return
        cls = item_obj.GetClass()
        entry = {"layer": board.GetLayerName(lid), "class": cls}
        if ref:
            entry["ref"] = ref
        if cls in text_classes:
            try:
                entry["text"] = item_obj.GetText()
                entry["height_mm"] = mm(item_obj.GetTextHeight())
                entry["thickness_mm"] = mm(item_obj.GetTextThickness())
                entry["visible"] = bool(item_obj.IsVisible())
            except Exception:  # noqa: BLE001
                pass
        else:
            try:
                entry["stroke_mm"] = mm(item_obj.GetWidth())
            except Exception:  # noqa: BLE001
                pass
        bb = item_obj.GetBoundingBox()
        entry["bbox_mm"] = [mm(bb.GetLeft()), mm(bb.GetTop()),
                            mm(bb.GetRight()), mm(bb.GetBottom())]
        silk.append(entry)

    for d in board.GetDrawings():
        add_silk(d)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for d in fp.GraphicalItems():
            add_silk(d, ref)
        for fld in fp.GetFields():
            if fld.IsVisible():
                add_silk(fld, ref)
    model["silkscreen"] = silk

    # ---- connectivity -----------------------------------------------------
    try:
        conn = board.GetConnectivity()
        conn.RecalculateRatsnest()
        model["ratsnest_unconnected"] = int(conn.GetUnconnectedCount(True))
    except Exception as exc:  # noqa: BLE001
        model["ratsnest_probe_error"] = repr(exc)

    return model


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("board")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()

    model = extract(args.board)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(model, fh, separators=(",", ":"))
    sys.stderr.write(
        "extracted {} footprints, {} pads, {} tracks, {} vias, {} zone layers\n".format(
            len(model["footprints"]), len(model["pads"]), len(model["tracks"]),
            len(model["vias"]), len(model["zones"]),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
