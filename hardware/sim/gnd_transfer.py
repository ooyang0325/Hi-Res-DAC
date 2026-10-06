"""gnd_transfer.py [BOARD_DUMP.json] : resistive solve of the GND copper (all 6 layers + vias) on a grid.

Dump the board first with KiCad python: board_dump.py BOARD.kicad_pcb board.json. Each scenario injects 1 A at the
source pads, removes it at the sink pads and prints probe-pad potentials against each jack sleeve (ohms = V per A). Sheet R: outer 1 oz 0.49 mOhm/sq,
inner 0.5 oz 0.98 mOhm/sq; via barrel 20 um plating, 0.3 mm span per layer gap.
ponytail: rasterised at H mm, pads snap to one cell; accuracy ~ +-30 % on transfer resistances."""
import json, sys, numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
from matplotlib.path import Path
H = 0.3
LAYERS = ["F.Cu", "GND", "PWR", "SIG", "GND5", "B.Cu"]
RS = {"F.Cu": 0.49e-3, "B.Cu": 0.49e-3}  # others 0.98e-3
RHO = 1.72e-8
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "board.json"))
x0, y0, x1, y1 = d["edge"]
nx, ny = int((x1 - x0) / H) + 1, int((y1 - y0) / H) + 1
gx, gy = np.meshgrid(x0 + H * (np.arange(nx) + .5), y0 + H * (np.arange(ny) + .5))
pts = np.c_[gx.ravel(), gy.ravel()]
masks = {}
for L in LAYERS:
    m = np.zeros(nx * ny, bool); holes = np.zeros(nx * ny, bool)
    for z in d["zone"]:
        if z["l"] != L or z["net"] != "GND": continue
        for p in z["polys"]:
            hole = p[-1] == "hole"; poly = np.array(p[:-1] if hole else p)
            lo, hi = poly.min(0), poly.max(0)
            sel = (pts[:, 0] >= lo[0]) & (pts[:, 0] <= hi[0]) & (pts[:, 1] >= lo[1]) & (pts[:, 1] <= hi[1])
            inside = Path(poly).contains_points(pts[sel])
            (holes if hole else m)[np.flatnonzero(sel)[inside]] = True
    m &= ~holes
    for t in d["trk"]:  # GND tracks
        if t["net"] != "GND" or t["l"] != L: continue
        a, b = np.array(t["a"]), np.array(t["b"]); n = max(2, int(np.hypot(*(b - a)) / (H / 2)) + 1)
        for s in np.linspace(0, 1, n):
            p = a + s * (b - a); r = max(t["w"] / 2, H / 2)
            i0, i1 = int((p[0] - r - x0) / H), int((p[0] + r - x0) / H); j0, j1 = int((p[1] - r - y0) / H), int((p[1] + r - y0) / H)
            for j in range(j0, j1 + 1):
                m[j * nx + i0:j * nx + i1 + 1] = True
    masks[L] = m
def cell(x, y): return int((y - y0) / H) * nx + int((x - x0) / H)
padlist = []
for f in d["fp"]:
    for p in f["pads"]:
        if p["net"] != "GND": continue
        padlist.append((f["ref"], p["n"], p))
        for L in (LAYERS if p["th"] else [l for l in p["lay"] if l in LAYERS]):
            i0, i1 = int((p["x"] - p["sx"] / 2 - x0) / H), int((p["x"] + p["sx"] / 2 - x0) / H)
            j0, j1 = int((p["y"] - p["sy"] / 2 - y0) / H), int((p["y"] + p["sy"] / 2 - y0) / H)
            for j in range(j0, j1 + 1): masks[L][j * nx + i0:j * nx + i1 + 1] = True
N = nx * ny; NL = len(LAYERS)
rows, cols, vals = [], [], []
def add(a, b, g):
    rows.extend([a, b, a, b]); cols.extend([a, b, b, a]); vals.extend([g, g, -g, -g])
for k, L in enumerate(LAYERS):
    g = 1.0 / RS.get(L, 0.98e-3); m = masks[L].reshape(ny, nx); base = k * N
    idx = np.arange(N).reshape(ny, nx)
    h = m[:, :-1] & m[:, 1:]; v = m[:-1, :] & m[1:, :]
    for a, b in ((idx[:, :-1][h], idx[:, 1:][h]), (idx[:-1, :][v], idx[1:, :][v])):
        rows += list(base + a) + list(base + b) + list(base + a) + list(base + b)
        cols += list(base + a) + list(base + b) + list(base + b) + list(base + a)
        vals += [g] * (2 * len(a)) + [-g] * (2 * len(a))
vias = [(v["x"], v["y"], v["drill"]) for v in d["via"] if v["net"] == "GND"]
vias += [(p["x"], p["y"], max(p["sx"], p["sy"]) * .6) for _, _, p in padlist if p["th"]]
for x, y, dr in vias:
    c = cell(x, y); gv = np.pi * dr * 1e-3 * 20e-6 / (RHO * 0.3e-3)
    for k in range(NL - 1):
        if masks[LAYERS[k]][c] and masks[LAYERS[k + 1]][c]: add(k * N + c, (k + 1) * N + c, gv)
        elif masks[LAYERS[k]][c]:  # skip a void layer: connect to next filled one
            for k2 in range(k + 2, NL):
                if masks[LAYERS[k2]][c]: add(k * N + c, k2 * N + c, gv / (k2 - k)); break
G = sp.csr_matrix((vals, (rows, cols)), shape=(NL * N, NL * N)) + sp.identity(NL * N) * 1e-6
print("grid", nx, ny, "nodes", NL * N, "GND vias+PTH", len(vias), file=sys.stderr)
_LU = []
P = {(r, n): p for r, n, p in padlist}
def node(ref, n):
    p = P[(ref, n)]; L = "F.Cu" if (p["th"] or "F.Cu" in p["lay"]) else "B.Cu"
    return LAYERS.index(L) * N + cell(p["x"], p["y"])
def solve(src, snk):
    b = np.zeros(NL * N)
    for s in src: b[node(*s)] += 1 / len(src)
    for s in snk: b[node(*s)] -= 1 / len(snk)
    if not _LU: _LU.append(sla.splu(G.tocsc(), permc_spec="COLAMD"))
    return _LU[0].solve(b)
def pads(ref): return [(ref, n) for (r, n) in P if r == ref]


if __name__ == "__main__":
    probes = {"R404 (L+ ref)": ("R404", "2"), "R408 (L- ref)": ("R408", "2"), "R412 (R+ ref)": ("R412", "2"), "R416 (R- ref)": ("R416", "2"),
              "R432 (VREF div)": ("R432", "2"), "U301 EP": ("U301", "EP"), "U401.3": ("U401", "3"), "J702 sleeve": ("J702", "1"),
              "J701 sleeve": ("J701", "1"), "J101 GND": ("J101", "A1/B12")}
    sc = {
     "A SE load return J702->U501": (pads("J702"), pads("U501")),
     "A' SE return J702->VPOS/VNEG bulk(C413,C415,C414,C416)": (pads("J702"), [("C413","2"),("C415","2"),("C414","2"),("C416","2")]),
     "B MCU+CPLD supply return ->J101": (pads("U201") + pads("U202"), pads("J101")),
     "C charge pump input ->J101": (pads("U501"), pads("J101")),
     "D ground loop J101->J702 sleeve": (pads("J101"), pads("J702")),
     "E DAC digital (U301) ->J101": (pads("U301"), pads("J101")),
    }
    for name, (s, k) in sc.items():
        v = solve(s, k); sl = v[node("J702", "1")]; sl1 = v[node("J701", "1")]
        print(f"\n{name}")
        for lab, pn in probes.items():
            if pn not in P: continue  # ECO F10: R404/R408/R412/R416 are on N4_GSENSE, not GND
            x = v[node(*pn)]
            print(f"  {lab:18s} vs J702 sleeve {1e6*(x-sl):9.1f} uOhm   vs J701 sleeve {1e6*(x-sl1):9.1f} uOhm")
    # self-check: reciprocity of the assembled network (drive A->B, sense C-D == drive C->D, sense A-B)
    a, b, c, e = pads("J101"), pads("J702"), [("R432", "2")], [("U501", "PAD")]
    v1, v2 = solve(a, b), solve(c, e)
    t1 = v1[node("R432", "2")] - v1[node("U501", "PAD")]
    t2 = np.mean([v2[node(*p)] for p in a]) - np.mean([v2[node(*p)] for p in b])
    assert abs(t1 - t2) < 0.02 * max(abs(t1), abs(t2)) + 1e-9, (t1, t2)
    print(f"\nreciprocity check ok: {1e6*t1:.1f} / {1e6*t2:.1f} uOhm")
