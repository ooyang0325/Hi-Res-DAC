"""Build a DC resistive network from the copper of a net and solve it.

This is the engine behind the IR-drop gate.  Rather than rasterising copper,
the copper is treated as what it physically is -- a graph of conductors:

  * every track segment is a resistor, R = rho * L / (w * t_layer);
  * every via barrel is a resistor, R = rho * h / (pi * d * t_plating);
  * every pad shorts together the copper landing inside it;
  * every filled zone island shorts together the copper inside it.

Nodal analysis then gives the DC potential at every pad for a stated load
distribution, and the effective source-to-pad resistance for each pad.
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from . import geom
from .rules import RHO_CU_20C, VIA_BARREL_PLATING_MM

#: Coordinates are snapped to this grid before nodes are identified, so that
#: endpoints KiCad stored as exactly coincident become the same node.
SNAP_MM = 0.001

#: Resistance used for an ideal short (a pad or a zone island joining copper).
SHORT_OHM = 1e-9

#: Copper landing this far outside a pad's nominal land is still treated as
#: connected.  KiCad's own connectivity engine joins a track whose end touches
#: the pad; half a minimum track width is the matching allowance here.
PAD_MERGE_TOL_MM = 0.075

#: Effective resistance above which a node is treated as having no DC path at
#: all.  Real copper paths on this board are milliohms, so anything beyond a
#: kilohm is an open circuit rather than a resistive connection.
OPEN_OHM = 1e3

#: Extra centreline allowance when deciding whether copper lands on a track.
#: Half of the 0.15 mm minimum track width: the thinnest branch that can
#: legally T into another track still overlaps its copper by this much.
TRACK_JUNCTION_TOL_MM = 0.075


class LayerStack:
    """Copper thickness and z position of each copper layer."""

    def __init__(self, layer_names, board_thickness_mm=1.6,
                 outer_oz=1.0, inner_oz=0.5, assumed=True):
        self.names = list(layer_names)
        self.assumed = assumed
        self.board_thickness_mm = board_thickness_mm
        n = len(self.names)
        self.thickness_mm = {}
        for i, name in enumerate(self.names):
            outer = (i == 0 or i == n - 1)
            self.thickness_mm[name] = (outer_oz if outer else inner_oz) * 0.0347222
        # Distribute the copper layers evenly through the board thickness.
        self.z_mm = {}
        if n == 1:
            self.z_mm[self.names[0]] = 0.0
        else:
            for i, name in enumerate(self.names):
                self.z_mm[name] = board_thickness_mm * i / (n - 1)

    def separation_mm(self, a, b) -> float:
        return abs(self.z_mm.get(a, 0.0) - self.z_mm.get(b, 0.0))

    def is_outer(self, name) -> bool:
        return name in (self.names[0], self.names[-1]) if self.names else False


def _snap(value: float) -> int:
    return int(round(value / SNAP_MM))


def track_resistance_ohm(length_mm, width_mm, thickness_mm, rho=RHO_CU_20C) -> float:
    if width_mm <= 0 or thickness_mm <= 0:
        return float("inf")
    area_m2 = (width_mm * 1e-3) * (thickness_mm * 1e-3)
    return rho * (length_mm * 1e-3) / area_m2


def via_resistance_ohm(length_mm, drill_mm, plating_mm=VIA_BARREL_PLATING_MM,
                       rho=RHO_CU_20C) -> float:
    if drill_mm <= 0 or length_mm <= 0:
        return SHORT_OHM
    area_m2 = math.pi * (drill_mm * 1e-3) * (plating_mm * 1e-3)
    return rho * (length_mm * 1e-3) / area_m2


class NetNetwork:
    """Resistive network for one net."""

    def __init__(self, net: str, stack: LayerStack):
        self.net = net
        self.stack = stack
        self._index = {}
        self._coords = []
        self._edges = []            # (i, j, resistance)
        self._tracks = []           # deferred until connect_tracks()
        self.pad_nodes = defaultdict(list)   # "REF.PAD" -> [node index]

    # -- node bookkeeping -------------------------------------------------
    def node(self, layer: str, x: float, y: float) -> int:
        key = (layer, _snap(x), _snap(y))
        idx = self._index.get(key)
        if idx is None:
            idx = len(self._coords)
            self._index[key] = idx
            self._coords.append((layer, x, y))
        return idx

    @property
    def node_count(self) -> int:
        return len(self._coords)

    def coord(self, idx):
        return self._coords[idx]

    def add_edge(self, i: int, j: int, resistance: float):
        if i != j:
            self._edges.append((i, j, max(resistance, SHORT_OHM)))

    # -- construction -----------------------------------------------------
    def add_track(self, track):
        """Register a track's endpoints.

        No edge is created yet: a track may have other copper landing part way
        along it (a T-junction), and those junctions are only known once every
        node exists.  :meth:`connect_tracks` builds the edges.
        """
        layer = track["layer"]
        t = self.stack.thickness_mm.get(layer)
        if t is None:
            return
        self.node(layer, *track["start_mm"])
        self.node(layer, *track["end_mm"])
        self._tracks.append(track)

    def connect_tracks(self):
        """Wire up every track, splitting it at copper that lands mid-span.

        KiCad connects a track whose copper overlaps another track anywhere
        along its length, not only at a shared endpoint.  Modelling a track as
        a single endpoint-to-endpoint edge therefore invents open circuits at
        every T-junction, so each track is split at the nodes lying on it and
        the pieces are chained with their share of the resistance.
        """
        by_layer = defaultdict(list)
        for idx, (layer, x, y) in enumerate(self._coords):
            by_layer[layer].append((x, y, idx))
        grids = {}
        for layer, items in by_layer.items():
            g = geom.GridIndex(2.0)
            for x, y, idx in items:
                g.insert((x, y, x, y), (x, y, idx))
            grids[layer] = g

        for track in self._tracks:
            layer = track["layer"]
            thick = self.stack.thickness_mm.get(layer)
            grid = grids.get(layer)
            if thick is None or grid is None:
                continue
            s = tuple(track["start_mm"])
            e = tuple(track["end_mm"])
            width = track["width_mm"]
            length = track.get("length_mm") or geom.dist(s, e)
            if length <= 0:
                continue
            # Copper overlaps when the centreline gap is under half of each
            # width; the thinnest routed track stands in for the branch.
            tol = width / 2.0 + TRACK_JUNCTION_TOL_MM
            x1, x2 = sorted((s[0], e[0]))
            y1, y2 = sorted((s[1], e[1]))
            dx, dy = e[0] - s[0], e[1] - s[1]
            denom = dx * dx + dy * dy

            on_track = []
            for px, py, idx in grid.query((x1, y1, x2, y2), tol):
                if geom.seg_point_distance((px, py), s, e) > tol:
                    continue
                t_par = 0.0 if denom <= 1e-18 else \
                    ((px - s[0]) * dx + (py - s[1]) * dy) / denom
                on_track.append((min(max(t_par, 0.0), 1.0), idx))

            if not on_track:
                continue
            on_track.sort()
            deduped = [on_track[0]]
            for t_par, idx in on_track[1:]:
                if idx != deduped[-1][1]:
                    deduped.append((t_par, idx))
            for (t0, i0), (t1, i1) in zip(deduped, deduped[1:]):
                seg_len = abs(t1 - t0) * length
                self.add_edge(i0, i1, track_resistance_ohm(seg_len, width, thick))

    def add_via(self, via, layer_order):
        x, y = via["pos_mm"]
        try:
            i0 = layer_order.index(via["top_layer"])
            i1 = layer_order.index(via["bottom_layer"])
        except ValueError:
            return
        lo, hi = min(i0, i1), max(i0, i1)
        spanned = layer_order[lo:hi + 1]
        for a, b in zip(spanned, spanned[1:]):
            na = self.node(a, x, y)
            nb = self.node(b, x, y)
            h = self.stack.separation_mm(a, b)
            self.add_edge(na, nb, via_resistance_ohm(h, via["drill_mm"]))

    def add_pad(self, pad):
        """A pad is a lump of copper: short everything that lands in it."""
        x, y = pad["pos_mm"]
        layers = [l for l in pad.get("on_copper", []) if l in self.stack.thickness_mm]
        if not layers:
            return
        nodes = [self.node(l, x, y) for l in layers]
        key = "{}.{}".format(pad["ref"], pad["pad"])
        for n in nodes:
            self.pad_nodes[key].append(n)
        for a, b in zip(nodes, nodes[1:]):
            self.add_edge(a, b, SHORT_OHM)

    def short_nodes_under_pads(self, pads):
        """Join copper nodes that physically sit inside a pad's land."""
        index = defaultdict(list)
        for idx, (layer, x, y) in enumerate(self._coords):
            index[layer].append((x, y, idx))
        grids = {}
        for layer, items in index.items():
            g = geom.GridIndex(2.0)
            for x, y, idx in items:
                g.insert((x, y, x, y), (x, y, idx))
            grids[layer] = g

        for pad in pads:
            x, y = pad["pos_mm"]
            reach = geom.pad_reach_mm(pad)
            key = "{}.{}".format(pad["ref"], pad["pad"])
            for layer in pad.get("on_copper", []):
                g = grids.get(layer)
                if g is None:
                    continue
                anchor = self.node(layer, x, y)
                self.pad_nodes[key].append(anchor)
                for px, py, idx in g.query_point((x, y), reach):
                    if idx == anchor:
                        continue
                    # PAD_MERGE_TOL_MM absorbs the track-end/pad-edge rounding
                    # that KiCad itself treats as a connection.
                    if geom.point_in_pad((px, py), pad, grow_mm=PAD_MERGE_TOL_MM):
                        self.add_edge(anchor, idx, SHORT_OHM)

    def short_nodes_in_zones(self, zone_polys):
        """Join copper nodes sitting inside the same filled zone island."""
        for layer, polys in zone_polys.items():
            if layer not in self.stack.thickness_mm:
                continue
            members = [(idx, x, y) for idx, (lay, x, y) in enumerate(self._coords)
                       if lay == layer]
            if not members:
                continue
            for poly in polys:
                if len(poly) < 3:
                    continue
                x1, y1, x2, y2 = geom.polygon_bbox(poly)
                inside = [idx for idx, x, y in members
                          if x1 <= x <= x2 and y1 <= y <= y2
                          and geom.point_in_polygon((x, y), poly)]
                for a, b in zip(inside, inside[1:]):
                    self.add_edge(a, b, SHORT_OHM)

    # -- analysis ---------------------------------------------------------
    def connected_components(self):
        uf = geom.UnionFind()
        for i in range(self.node_count):
            uf.find(i)
        for i, j, _ in self._edges:
            uf.union(i, j)
        return uf.groups()

    def shortest_copper_path_mm(self, source_nodes, target_nodes):
        """Shortest physical path along copper between two node sets, in mm.

        Edge weight is the geometric distance between node coordinates, so the
        result is the length a current actually travels through the drawn
        copper rather than a straight line through air.  Returns ``None`` when
        no path exists.
        """
        import heapq

        if not source_nodes or not target_nodes:
            return None
        adj = defaultdict(list)
        for i, j, _ in self._edges:
            li, xi, yi = self._coords[i]
            lj, xj, yj = self._coords[j]
            # A via or pad short joins layers at one xy; it adds no planar length.
            w = 0.0 if li != lj else math.hypot(xi - xj, yi - yj)
            adj[i].append((j, w))
            adj[j].append((i, w))

        targets = set(target_nodes)
        dist = {n: 0.0 for n in source_nodes}
        pq = [(0.0, n) for n in set(source_nodes)]
        heapq.heapify(pq)
        while pq:
            d, n = heapq.heappop(pq)
            if d > dist.get(n, float("inf")) + 1e-12:
                continue
            if n in targets:
                return d
            for m, w in adj[n]:
                nd = d + w
                if nd < dist.get(m, float("inf")) - 1e-12:
                    dist[m] = nd
                    heapq.heappush(pq, (nd, m))
        return None

    def solve(self, source_nodes, load_currents):
        """Solve G v = i with the source held at 0 V.

        ``load_currents`` maps node index -> current drawn (A).  Returns the
        node potential array (volts below the source).
        """
        n = self.node_count
        if n == 0:
            return None
        G = np.zeros((n, n), dtype=float)
        for i, j, r in self._edges:
            g = 1.0 / max(r, SHORT_OHM)
            G[i, i] += g
            G[j, j] += g
            G[i, j] -= g
            G[j, i] -= g
        rhs = np.zeros(n, dtype=float)
        for node, amps in load_currents.items():
            rhs[node] += amps
        # Ground the source nodes by replacing their equations.
        for s in source_nodes:
            G[s, :] = 0.0
            G[:, s] = 0.0
            G[s, s] = 1.0
            rhs[s] = 0.0
        # Any node not connected to a source would make the matrix singular;
        # pin those to zero so the solve stays well posed and report them.
        diag = np.abs(np.diag(G))
        isolated = np.where(diag < 1e-15)[0]
        for idx in isolated:
            G[idx, idx] = 1.0
            rhs[idx] = 0.0
        try:
            v = np.linalg.solve(G, rhs)
        except np.linalg.LinAlgError:
            v, *_ = np.linalg.lstsq(G, rhs, rcond=None)
        return v

    def effective_resistances(self, source_nodes, probe_nodes):
        """R_eff from the (shorted) source to each probe node, in ohms."""
        n = self.node_count
        if n == 0 or not probe_nodes:
            return {}
        G = np.zeros((n, n), dtype=float)
        for i, j, r in self._edges:
            g = 1.0 / max(r, SHORT_OHM)
            G[i, i] += g
            G[j, j] += g
            G[i, j] -= g
            G[j, i] -= g
        for s in source_nodes:
            G[s, :] = 0.0
            G[:, s] = 0.0
            G[s, s] = 1.0
        diag = np.abs(np.diag(G))
        for idx in np.where(diag < 1e-15)[0]:
            G[idx, idx] = 1.0
        probes = sorted(set(probe_nodes) - set(source_nodes))
        if not probes:
            return {}
        rhs = np.zeros((n, len(probes)), dtype=float)
        for col, node in enumerate(probes):
            rhs[node, col] = 1.0
        for s in source_nodes:
            rhs[s, :] = 0.0
        try:
            sol = np.linalg.solve(G, rhs)
        except np.linalg.LinAlgError:
            sol, *_ = np.linalg.lstsq(G, rhs, rcond=None)
        return {node: float(sol[node, col]) for col, node in enumerate(probes)}


def build_for_net(net: str, model, stack: LayerStack, *, include_zones=True) -> NetNetwork:
    """Assemble the resistive network for one net from the extracted model."""
    layer_order = [l["name"] for l in model["copper_layers"]]
    nn = NetNetwork(net, stack)

    for tr in model["tracks"]:
        if tr["net"] == net:
            nn.add_track(tr)
    for via in model["vias"]:
        if via["net"] == net:
            nn.add_via(via, layer_order)

    pads = [p for p in model["pads"] if p["net"] == net]
    for pad in pads:
        nn.add_pad(pad)
    nn.short_nodes_under_pads(pads)

    # Every node now exists, so tracks can be split at their T-junctions.
    nn.connect_tracks()

    if include_zones:
        zp = defaultdict(list)
        for z in model["zones"]:
            if z["net"] == net and not z["is_rule_area"]:
                zp[z["layer"]].extend(z["filled_polygons"])
        if zp:
            nn.short_nodes_in_zones(zp)

    return nn
