#!/usr/bin/env python3
"""Run with KiCad's bundled Python to inspect native footprint pad numbers."""

import json
import sys

import pcbnew


requests = json.load(sys.stdin)
result = {}
for key, data in requests.items():
    footprint = pcbnew.FootprintLoad(data["library_path"], data["name"])
    if footprint is None:
        raise RuntimeError("Cannot load " + key)
    result[key] = sorted({pad.GetNumber() for pad in footprint.Pads() if pad.GetNumber()})
json.dump(result, sys.stdout)
