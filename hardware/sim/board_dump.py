"""board_dump.py BOARD.kicad_pcb OUT.json : copper geometry in mm for gnd_transfer.py / coupling_screen.py (KiCad python)."""
import json, sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); M = pcbnew.ToMM
L = lambda l: b.GetLayerName(l)
out = {"fp": [], "trk": [], "via": [], "zone": []}
for f in b.GetFootprints():
    bb = f.GetBoundingBox(False)
    out["fp"].append({"ref": f.GetReference(), "val": f.GetValue(), "x": M(f.GetPosition().x), "y": M(f.GetPosition().y),
        "side": L(f.GetLayer()), "bb": [M(bb.GetLeft()), M(bb.GetTop()), M(bb.GetRight()), M(bb.GetBottom())],
        "pads": [{"n": p.GetNumber(), "net": p.GetNetname(), "x": M(p.GetPosition().x), "y": M(p.GetPosition().y),
                  "sx": M(p.GetBoundingBox().GetWidth()), "sy": M(p.GetBoundingBox().GetHeight()),
                  "th": p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH, "lay": [L(x) for x in p.GetLayerSet().CuStack()]} for p in f.Pads()]})
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        out["via"].append({"net": t.GetNetname(), "x": M(t.GetPosition().x), "y": M(t.GetPosition().y), "d": M(t.GetWidth(pcbnew.F_Cu)), "drill": M(t.GetDrill())})
    elif t.GetClass() == "PCB_TRACK":
        out["trk"].append({"net": t.GetNetname(), "l": L(t.GetLayer()), "a": [M(t.GetStart().x), M(t.GetStart().y)], "b": [M(t.GetEnd().x), M(t.GetEnd().y)], "w": M(t.GetWidth())})
    else:
        out["trk"].append({"net": t.GetNetname(), "l": L(t.GetLayer()), "a": [M(t.GetStart().x), M(t.GetStart().y)], "b": [M(t.GetEnd().x), M(t.GetEnd().y)], "w": M(t.GetWidth()), "arc": 1})
for z in b.Zones():
    for lid in z.GetLayerSet().CuStack():
        ps = z.GetFilledPolysList(lid)
        polys = []
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i); polys.append([[M(o.CPoint(k).x), M(o.CPoint(k).y)] for k in range(o.PointCount())])
            for h in range(ps.HoleCount(i)):
                hh = ps.Hole(i, h); polys.append([[M(hh.CPoint(k).x), M(hh.CPoint(k).y)] for k in range(hh.PointCount())] + ["hole"])
        out["zone"].append({"net": z.GetNetname(), "l": L(lid), "pri": z.GetAssignedPriority(), "polys": polys})
ec = b.GetBoardEdgesBoundingBox(); out["edge"] = [M(ec.GetLeft()), M(ec.GetTop()), M(ec.GetRight()), M(ec.GetBottom())]
json.dump(out, open(sys.argv[2], "w"))
print(len(out["fp"]), len(out["trk"]), len(out["via"]), len(out["zone"]), out["edge"])
