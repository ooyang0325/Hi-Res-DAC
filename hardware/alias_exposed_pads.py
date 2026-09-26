#!/usr/bin/env python3
"""Give JLCPCB exposed pads the pad labels used in Parts List v0.8."""

from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

# The copper geometry is unchanged. These are pin-number aliases only.
ALIASES = {
    "WSON-6_L2.0-W2.0-P0.65-TL-EP": ("7", "PAD"),
    "QFN-32_L4.0-W4.0-P0.40-BL-EP2.7": ("33", "EP"),
    "ESOP-8_L4.9-W3.9-P1.27-LS6.0-BL-EP": ("9", "PAD"),
    "QFN-28_L5.0-W5.0-P0.50-BL-EP3.3": ("29", "EP"),
    "VSON-10_L3.0-W3.0-P0.50-BL-EP1.65": ("11", "PAD"),
    "WSON-12_L3.0-W2.0-P0.50-BL-EP": ("13", "PAD"),
}


def alias_name(original: str, to_pad: str) -> str:
    return f"{original}_{to_pad}"


def make() -> None:
    for original, (from_pad, to_pad) in ALIASES.items():
        source = HERE / "JLC_Imported.pretty" / f"{original}.kicad_mod"
        target_name = alias_name(original, to_pad)
        target = HERE / "DAC_HPA.pretty" / f"{target_name}.kicad_mod"
        text = source.read_text(encoding="utf-8")
        text, count = re.subn(rf'\(pad "{re.escape(from_pad)}"', f'(pad "{to_pad}"', text)
        if count != 1:
            raise ValueError(f"Expected one exposed pad {from_pad} in {source}, found {count}")
        text = text.replace(f'(footprint "{original}"', f'(footprint "{target_name}"', 1)
        text = text.replace(f'(property "Value" "{original}"', f'(property "Value" "{target_name}"', 1)
        target.write_text(text, encoding="utf-8")
        print(f"{target.name}: {from_pad} -> {to_pad}")


if __name__ == "__main__":
    make()
