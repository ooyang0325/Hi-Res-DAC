"""2-D quasi-static field solver for outer-layer microstrip over the first plane.

Same method as ``hardware/sim/signoff/tline_fd.m`` (validated there against
Hammerstad-Jensen): solve div(eps grad phi) = 0 by finite differences, once
with the dielectrics and once in air, take the per-line capacitance from the
field energy, and Z = 1 / (c0 sqrt(C Cair)).  A conformal solder-mask layer
is included because it lowers a fine pair by a few ohms.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

C0 = 299792458.0
E0 = 8.854187817e-12


def _capacitance(w, s, t, h, er, tm, erm, d, volts, dielectric):
    d = h / round(h / d)                 # grid rows land exactly on the dielectric top
    t = max(1, round(t / d)) * d         # and on the copper top
    width = 2 * w + s + 12 * h + 1.0
    height = h + t + 1.2
    nx, ny = int(round(width / d)) + 1, int(round(height / d)) + 1
    x = np.arange(nx) * d - width / 2
    y = np.arange(ny) * d
    X, Y = np.meshgrid(x, y, indexing="ij")
    centres = [-(s + w) / 2, (s + w) / 2] if s > 0 else [0.0]
    fixed = np.zeros((nx, ny), bool)
    value = np.zeros((nx, ny))
    for xc, v in zip(centres, volts):
        m = (np.abs(X - xc) <= w / 2 + 1e-9) & (Y >= h - 1e-9) & (Y <= h + t + 1e-9)
        fixed[m] = True
        value[m] = v
    fixed[0, :] = fixed[-1, :] = fixed[:, 0] = fixed[:, -1] = True
    xm, ym = (X[:-1, :-1] + X[1:, 1:]) / 2, (Y[:-1, :-1] + Y[1:, 1:]) / 2
    eps = np.ones((nx - 1, ny - 1))
    if dielectric:
        eps[ym < h] = er
        if tm > 0:
            near = (ym >= h) & (ym <= h + tm)
            for xc in centres:
                near |= (np.abs(xm - xc) <= w / 2 + tm) & (ym >= h) & (ym <= h + t + tm)
            eps[near] = erm
    pad = np.zeros((nx + 1, ny + 1))
    pad[1:-1, 1:-1] = eps
    e_x = (pad[1:, 1:] + pad[1:, :-1]) / 2          # face (i,j)-(i+1,j)
    e_y = (pad[1:, 1:] + pad[:-1, 1:]) / 2          # face (i,j)-(i,j+1)
    idx = np.arange(nx * ny).reshape(nx, ny)
    rows, cols, vals = [], [], []
    for a, b, wgt in ((idx[:-1, :], idx[1:, :], e_x[:-1, :]), (idx[:, :-1], idx[:, 1:], e_y[:, :-1])):
        a, b, wgt = a.ravel(), b.ravel(), wgt.ravel()
        rows += [a, a, b, b]
        cols += [a, b, b, a]
        vals += [wgt, -wgt, wgt, -wgt]
    A = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                   shape=(nx * ny, nx * ny)).tocsr()
    free = ~fixed.ravel()
    phi = value.ravel().copy()
    phi[free] = spsolve(A[free][:, free], -A[free][:, ~free] @ phi[~free])
    P = phi.reshape(nx, ny)
    dm = d * 1e-3
    ex, ey = np.diff(P, axis=0) / dm, np.diff(P, axis=1) / dm
    energy = 0.5 * E0 * (np.sum(e_x[:-1, :] * ex ** 2) + np.sum(e_y[:, :-1] * ey ** 2)) * dm * dm
    return 2 * energy / sum(v * v for v in volts)


def microstrip(w, t, h, er, *, s=0.0, tm=0.015, erm=3.8, d=0.004):
    """Z0 (s == 0) or {'zdiff', 'zodd', 'zeven', 'eeff_odd'} for an edge gap s (mm)."""
    modes = [(1.0, 1.0), (1.0, -1.0)] if s > 0 else [(1.0,)]
    out = []
    for volts in modes:
        c = _capacitance(w, s, t, h, er, tm, erm, d, volts, True)
        ca = _capacitance(w, s, t, h, er, tm, erm, d, volts, False)
        out.append((1.0 / (C0 * math.sqrt(c * ca)), c / ca))
    if s <= 0:
        return {"z0": out[0][0], "eeff": out[0][1]}
    (ze, _), (zo, eo) = out
    return {"zdiff": 2 * zo, "zodd": zo, "zeven": ze, "eeff_odd": eo}
