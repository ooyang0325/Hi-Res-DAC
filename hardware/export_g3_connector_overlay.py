#!/usr/bin/env python3
"""Export an actual-size, review-only SVG of the three connector footprints.

Print at 100% / Actual Size and measure the 10 mm reference before using it
for G-3. The drawing is evidence for a physical overlay, not fabrication data.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
LIBRARY = HERE / "DAC_HPA.pretty"
OUTPUT = HERE / "G3_CONNECTOR_OVERLAY_REVIEW_ONLY.svg"


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def n(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def pad_svg(pad) -> str:
    x, y = mm(pad.GetPosition().x), mm(pad.GetPosition().y)
    width, height = mm(pad.GetSize().x), mm(pad.GetSize().y)
    drill_x, drill_y = mm(pad.GetDrillSize().x), mm(pad.GetDrillSize().y)
    angle = pad.GetOrientationDegrees()
    number = escape(pad.GetNumber())
    lines = [f'<g transform="translate({n(x)} {n(y)}) rotate({n(angle)})">']
    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
        assert not number and abs(width - height) < 0.02
        assert abs(width - drill_x) < 0.02 and abs(height - drill_y) < 0.02
        lines.append(f'<circle r="{n(width/2)}" fill="white" stroke="#111" stroke-width="0.13"/>')
    else:
        shape = pad.GetShape()
        if shape == pcbnew.PAD_SHAPE_CIRCLE:
            assert abs(width - height) < 0.02
            lines.append(f'<circle r="{n(width/2)}" fill="#dedede" stroke="#111" stroke-width="0.13"/>')
        else:
            assert shape in (pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_OVAL, pcbnew.PAD_SHAPE_ROUNDRECT), shape
            radius = min(width, height) / 2 if shape == pcbnew.PAD_SHAPE_OVAL else (
                mm(pad.GetRoundRectCornerRadius()) if shape == pcbnew.PAD_SHAPE_ROUNDRECT else 0
            )
            lines.append(
                f'<rect x="{n(-width/2)}" y="{n(-height/2)}" width="{n(width)}" '
                f'height="{n(height)}" rx="{n(radius)}" fill="#dedede" '
                'stroke="#111" stroke-width="0.13"/>'
            )
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            if pad.GetDrillShape() == pcbnew.PAD_DRILL_SHAPE_CIRCLE:
                assert abs(drill_x - drill_y) < 0.02
                lines.append(f'<circle r="{n(drill_x/2)}" fill="white" stroke="#111" stroke-width="0.1"/>')
            else:
                assert pad.GetDrillShape() == pcbnew.PAD_DRILL_SHAPE_OBLONG
                drill_radius = min(drill_x, drill_y) / 2
                lines.append(
                    f'<rect x="{n(-drill_x/2)}" y="{n(-drill_y/2)}" '
                    f'width="{n(drill_x)}" height="{n(drill_y)}" rx="{n(drill_radius)}" '
                    'fill="white" stroke="#111" stroke-width="0.1"/>'
                )
        lines.append(f'<text x="0" y="0.21" text-anchor="middle" font-size="0.7" fill="#111">{number}</text>')
    lines.append('</g>')
    return "\n".join(lines)


def fab_svg(item) -> str:
    if item.GetLayerName() != "F.Fab" or not hasattr(item, "GetShape"):
        return ""
    kind = item.GetShape()
    x1, y1 = mm(item.GetStart().x), mm(item.GetStart().y)
    x2, y2 = mm(item.GetEnd().x), mm(item.GetEnd().y)
    if kind == pcbnew.S_SEGMENT:
        return f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" class="body"/>'
    if kind == pcbnew.S_RECT:
        return f'<rect x="{n(min(x1,x2))}" y="{n(min(y1,y2))}" width="{n(abs(x2-x1))}" height="{n(abs(y2-y1))}" class="body"/>'
    return ""


def footprint_svg(ref: str, name: str, index: int, part: str, x: float, y: float) -> str:
    item = pcbnew.FootprintLoad(str(LIBRARY), name)
    assert item is not None, name
    graphics = "\n".join(filter(None, (fab_svg(shape) for shape in item.GraphicalItems())))
    pads = "\n".join(pad_svg(pad) for pad in sorted(item.Pads(), key=lambda p: (p.GetNumber() == "", p.GetNumber())))
    return (
        f'<text x="{n(x)}" y="{n(y-15)}" class="label">{index:02d} · {escape(ref)} — {escape(part)}</text>\n'
        f'<g transform="translate({n(x)} {n(y)})">\n{graphics}\n{pads}\n</g>'
    )


def main() -> None:
    drawings = [
        footprint_svg("J101", "J101_USB4105-GF-A_12lands_4stakes_NPTH030", 1, "USB4105-GF-A", 60, 57),
        footprint_svg("J701", "J701_GT-3321667P-01_maker_slots", 2, "GT-3321667P-01", 60, 112),
        footprint_svg("J702", "J702_PJ-332A-6A_peg_holes", 3, "PJ-332A-6A", 60, 167),
    ]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">
<style>
  .body {{ fill: none; stroke: #666; stroke-width: 0.13; }}
  .label {{ font: 3px sans-serif; fill: #111; }}
  .note {{ font: 2.7px sans-serif; fill: #111; }}
</style>
<rect x="0" y="0" width="210" height="297" fill="white"/>
<text x="15" y="17" style="font: 5px sans-serif">G-3 connector overlay — REVIEW ONLY — actual size</text>
<text x="15" y="25" class="note">Print at 100% / Actual Size. Measure the 10 mm bar before overlaying samples.</text>
<line x1="165" y1="33" x2="175" y2="33" stroke="#111" stroke-width="0.4"/>
<line x1="165" y1="31" x2="165" y2="35" stroke="#111" stroke-width="0.2"/>
<line x1="175" y1="31" x2="175" y2="35" stroke="#111" stroke-width="0.2"/>
<text x="165" y="39" class="note">10 mm reference</text>
{chr(10).join(drawings)}
<text x="15" y="207" class="note">J101: verify 12 composite lands, S1–S4 slots and two Ø0.65 mm locating holes.</text>
<text x="15" y="214" class="note">J701: verify 12 slots, two Ø1.20 mm peg holes and enlarged copper pads.</text>
<text x="15" y="221" class="note">J702: verify pads 1/2 slots, pads 3–6, two Ø1.20 mm peg holes and enlarged copper.</text>
<text x="15" y="234" class="note">Sample IDs / date / reviewer: __________________________________________________________</text>
<text x="15" y="241" class="note">Overlay result and any measured mismatch: ____________________________________________</text>
<text x="15" y="248" class="note">KiCad pad numbers, nets and physical orientation must also match the G-1/G-2/G-4 records.</text>
</svg>
'''
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Exported {OUTPUT.name} (A4, 1:1 mm units; verify printed 10 mm bar)")


if __name__ == "__main__":
    main()
