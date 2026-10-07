"""Plain-Python computational geometry used by the sign-off gates.

No KiCad dependency: everything operates on the millimetre coordinates in the
extracted model so the gates stay reviewable and testable on their own.
"""

from __future__ import annotations

import math
from collections import defaultdict


# ---------------------------------------------------------------------------
# Point / segment primitives
# ---------------------------------------------------------------------------

def dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def seg_point_distance(p, a, b) -> float:
    """Shortest distance from point p to segment ab."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-18:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / denom
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg_distance(a1, a2, b1, b2) -> float:
    """Shortest distance between two segments."""
    if _segments_intersect(a1, a2, b1, b2):
        return 0.0
    return min(
        seg_point_distance(a1, b1, b2),
        seg_point_distance(a2, b1, b2),
        seg_point_distance(b1, a1, a2),
        seg_point_distance(b2, a1, a2),
    )


def _orient(p, q, r) -> float:
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def _on_segment(p, q, r) -> bool:
    return (min(p[0], r[0]) - 1e-12 <= q[0] <= max(p[0], r[0]) + 1e-12
            and min(p[1], r[1]) - 1e-12 <= q[1] <= max(p[1], r[1]) + 1e-12)


def _segments_intersect(p1, p2, p3, p4) -> bool:
    d1 = _orient(p3, p4, p1)
    d2 = _orient(p3, p4, p2)
    d3 = _orient(p1, p2, p3)
    d4 = _orient(p1, p2, p4)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    if abs(d1) < 1e-12 and _on_segment(p3, p1, p4):
        return True
    if abs(d2) < 1e-12 and _on_segment(p3, p2, p4):
        return True
    if abs(d3) < 1e-12 and _on_segment(p1, p3, p2):
        return True
    if abs(d4) < 1e-12 and _on_segment(p1, p4, p2):
        return True
    return False


def segment_length(seg) -> float:
    return dist(seg[0], seg[1])


# ---------------------------------------------------------------------------
# Polygons
# ---------------------------------------------------------------------------

def polygon_area(poly) -> float:
    """Signed shoelace area; absolute value is the enclosed area."""
    n = len(poly)
    if n < 3:
        return 0.0
    acc = 0.0
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        acc += x1 * y2 - x2 * y1
    return acc / 2.0


def polygon_bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))


def point_in_polygon(pt, poly) -> bool:
    """Ray-casting containment test (boundary counts as inside)."""
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi + 1e-300) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def bbox_overlap_area(a, b) -> float:
    """Overlap area of two (x1, y1, x2, y2) boxes."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    return w * h


def bbox_distance(a, b) -> float:
    """Gap between two axis-aligned boxes; 0 if they touch or overlap."""
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def convex_hull(points):
    """Monotone-chain convex hull; used for loop-area estimates."""
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in points))
    if len(pts) <= 2:
        return pts
    lower = []
    for p in pts:
        while len(lower) >= 2 and _orient(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and _orient(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


# ---------------------------------------------------------------------------
# Uniform-grid spatial index
# ---------------------------------------------------------------------------

def _drill_xy(pad):
    drill = pad.get("drill_mm") or (0.0, 0.0)
    if isinstance(drill, (int, float)):
        return float(drill), float(drill)
    if len(drill) == 1:
        return float(drill[0]), float(drill[0])
    return float(drill[0]), float(drill[1])


def drill_slot(pad):
    """Describe a drilled hole as a capsule: ``(p1, p2, radius)``.

    A round hole is a zero-length segment.  An oval (slotted) hole is a
    segment of length ``|dx - dy|`` capped by semicircles, rotated with the
    pad.  Treating a slot as a circle of its major axis -- which is what
    ``max(drill)`` does -- overstates the hole in its narrow direction and
    manufactures clearance violations that do not exist.
    """
    dx, dy = _drill_xy(pad)
    if dx <= 0 or dy <= 0:
        return None
    radius = min(dx, dy) / 2.0
    half = abs(dx - dy) / 2.0
    cx, cy = pad["pos_mm"]
    if half <= 1e-9:
        return (cx, cy), (cx, cy), radius
    ang = math.radians(pad.get("orientation_deg") or 0.0)
    ux, uy = (1.0, 0.0) if dx > dy else (0.0, 1.0)
    ca, sa = math.cos(ang), math.sin(ang)
    rx, ry = ux * ca - uy * sa, ux * sa + uy * ca
    return ((cx - rx * half, cy - ry * half),
            (cx + rx * half, cy + ry * half),
            radius)


def hole_gap_mm(pad_a, pad_b) -> float:
    """Copper-free gap between two drilled holes, slot aware."""
    sa = drill_slot(pad_a)
    sb = drill_slot(pad_b)
    if sa is None or sb is None:
        return float("inf")
    a1, a2, ra = sa
    b1, b2, rb = sb
    return seg_seg_distance(a1, a2, b1, b2) - ra - rb


def seg_pad_distance(p1, p2, pad) -> float:
    """Distance from segment ``p1-p2`` to a pad's copper land.

    The segment is transformed into the pad's own frame so the land can be
    treated as an axis-aligned rectangle; oval and circular lands are handled
    as capsules in that frame.
    """
    cx, cy = pad["pos_mm"]
    ang = math.radians(pad.get("orientation_deg") or 0.0)
    ca, sa = math.cos(-ang), math.sin(-ang)

    def to_local(p):
        dx, dy = p[0] - cx, p[1] - cy
        return (dx * ca - dy * sa, dx * sa + dy * ca)

    a, b = to_local(p1), to_local(p2)
    sx, sy = pad.get("size_mm", (0.0, 0.0))
    hx, hy = sx / 2.0, sy / 2.0
    shape = (pad.get("shape") or "").lower()

    if shape in ("circle", "oval"):
        r = min(hx, hy)
        if hx >= hy:
            c1, c2 = (-(hx - r), 0.0), (hx - r, 0.0)
        else:
            c1, c2 = (0.0, -(hy - r)), (0.0, hy - r)
        return max(seg_seg_distance(a, b, c1, c2) - r, 0.0)

    # A rounded or chamfered rectangle is the rectangle inset by the corner
    # radius, grown back by that radius.  Measuring to the sharp rectangle
    # instead understates the corner gap and invents clearance violations.
    rc = float(pad.get("corner_radius_mm") or 0.0)
    rc = max(0.0, min(rc, min(hx, hy)))
    ix, iy = hx - rc, hy - rc
    corners = [(-ix, -iy), (ix, -iy), (ix, iy), (-ix, iy)]
    if any(abs(p[0]) <= ix and abs(p[1]) <= iy for p in (a, b)):
        return 0.0
    d = min(seg_seg_distance(a, b, corners[i], corners[(i + 1) % 4])
            for i in range(4))
    return max(d - rc, 0.0)


def pad_annular_ring_mm(pad):
    """Smallest annular ring of a drilled pad, measured per axis.

    The pad land and its drill share the pad's local frame, so the ring is
    the smaller of the two per-axis margins.  Comparing ``min(size)`` against
    ``max(drill)`` mixes the narrow pad axis with the long drill axis and
    reports a negative ring for a perfectly good slotted pad.
    """
    dx, dy = _drill_xy(pad)
    if dx <= 0 and dy <= 0:
        return None
    size = pad.get("size_mm") or (0.0, 0.0)
    return min((size[0] - dx) / 2.0, (size[1] - dy) / 2.0)


def pad_reach_mm(pad) -> float:
    """Radius that certainly encloses the pad land, including its drill."""
    sx, sy = pad.get("size_mm", (0.0, 0.0))
    reach = 0.5 * math.hypot(sx, sy)
    drill = pad.get("drill_mm") or (0.0, 0.0)
    if drill and max(drill) > 0:
        reach = max(reach, 0.5 * math.hypot(drill[0], drill[1]))
    return max(reach, 0.05)


def point_in_pad(pt, pad, grow_mm: float = 0.0) -> bool:
    """True when ``pt`` lies on the pad's copper land.

    Honours the pad's rotation and its shape family.  Rounded, chamfered and
    trapezoidal rectangles are treated as their bounding rectangle, and custom
    shapes as their bounding circle: both are deliberate over-estimates, since
    for connectivity an over-estimate merges copper that really is one lump,
    while an under-estimate invents an open circuit that does not exist.
    """
    px, py = pt
    cx, cy = pad["pos_mm"]
    dx, dy = px - cx, py - cy
    ang = math.radians(pad.get("orientation_deg") or 0.0)
    if ang:
        ca, sa = math.cos(-ang), math.sin(-ang)
        dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
    sx, sy = pad.get("size_mm", (0.0, 0.0))
    hx, hy = sx / 2.0 + grow_mm, sy / 2.0 + grow_mm
    shape = (pad.get("shape") or "").lower()

    if shape == "circle":
        return math.hypot(dx, dy) <= max(hx, hy) + 1e-9
    if shape == "oval":
        if hx <= 0 or hy <= 0:
            return False
        # Stadium: rectangle of length |sx-sy| capped by semicircles.
        r = min(hx, hy)
        if hx >= hy:
            flat = hx - r
            return abs(dx) <= flat + 1e-9 and abs(dy) <= r + 1e-9 or \
                math.hypot(max(abs(dx) - flat, 0.0), dy) <= r + 1e-9
        flat = hy - r
        return abs(dy) <= flat + 1e-9 and abs(dx) <= r + 1e-9 or \
            math.hypot(dx, max(abs(dy) - flat, 0.0)) <= r + 1e-9
    if shape == "custom":
        return math.hypot(dx, dy) <= 0.5 * math.hypot(sx, sy) + grow_mm + 1e-9
    if shape in ("roundrect", "chamfered_rect"):
        rc = float(pad.get("corner_radius_mm") or 0.0)
        rc = max(0.0, min(rc, min(hx, hy)))
        ix, iy = hx - rc, hy - rc
        qx, qy = abs(dx) - ix, abs(dy) - iy
        if qx <= 0 or qy <= 0:
            return abs(dx) <= hx + 1e-9 and abs(dy) <= hy + 1e-9
        return math.hypot(qx, qy) <= rc + 1e-9
    # rect, trapezoid and anything unrecognised
    return abs(dx) <= hx + 1e-9 and abs(dy) <= hy + 1e-9


class GridIndex:
    """Bucket objects by their bounding box for cheap neighbourhood queries."""

    def __init__(self, cell_mm: float = 5.0):
        self.cell = float(cell_mm)
        self._buckets = defaultdict(list)

    def _keys(self, bbox):
        x1, y1, x2, y2 = bbox
        c = self.cell
        for ix in range(int(math.floor(x1 / c)), int(math.floor(x2 / c)) + 1):
            for iy in range(int(math.floor(y1 / c)), int(math.floor(y2 / c)) + 1):
                yield (ix, iy)

    def insert(self, bbox, payload):
        for key in self._keys(bbox):
            self._buckets[key].append(payload)

    def query(self, bbox, radius_mm: float = 0.0):
        x1, y1, x2, y2 = bbox
        expanded = (x1 - radius_mm, y1 - radius_mm, x2 + radius_mm, y2 + radius_mm)
        seen = set()
        out = []
        for key in self._keys(expanded):
            for payload in self._buckets.get(key, ()):
                pid = id(payload)
                if pid not in seen:
                    seen.add(pid)
                    out.append(payload)
        return out

    def query_point(self, pt, radius_mm: float):
        return self.query((pt[0], pt[1], pt[0], pt[1]), radius_mm)


# ---------------------------------------------------------------------------
# Union-find, for netlist-free connectivity on copper
# ---------------------------------------------------------------------------

class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        p = self.parent.setdefault(x, x)
        while p != x:
            self.parent[x] = self.parent.setdefault(p, p)
            x = self.parent[x]
            p = self.parent.setdefault(x, x)
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

    def groups(self):
        out = defaultdict(list)
        for key in list(self.parent):
            out[self.find(key)].append(key)
        return out


# ---------------------------------------------------------------------------
# Pad geometry helpers
# ---------------------------------------------------------------------------

def pad_bbox(pad) -> tuple:
    """Axis-aligned bounding box of a pad, accounting for its rotation."""
    cx, cy = pad["pos_mm"]
    sx, sy = pad["size_mm"]
    ang = math.radians(pad.get("orientation_deg", 0.0) or 0.0)
    ca, sa = abs(math.cos(ang)), abs(math.sin(ang))
    w = sx * ca + sy * sa
    h = sx * sa + sy * ca
    return (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)


def pad_effective_radius(pad) -> float:
    sx, sy = pad["size_mm"]
    return math.hypot(sx, sy) / 2.0


def track_bbox(track) -> tuple:
    (x1, y1), (x2, y2) = track["start_mm"], track["end_mm"]
    hw = track["width_mm"] / 2.0
    return (min(x1, x2) - hw, min(y1, y2) - hw, max(x1, x2) + hw, max(y1, y2) + hw)


def polyline_length(points) -> float:
    return sum(dist(points[i], points[i + 1]) for i in range(len(points) - 1))
