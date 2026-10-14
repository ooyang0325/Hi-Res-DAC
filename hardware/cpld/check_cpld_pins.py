#!/usr/bin/env python3
"""U202_pins.asf and link_fit_skeleton.v must match the schematic netlist's U202 pin map (OD-16)."""
import re, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
cli = shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "n.xml"
    subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out),
                    str(HERE.parent / "DAC_HPA.kicad_sch")], check=True, capture_output=True)
    root = ET.parse(out).getroot()
netlist = {node.get("pin"): net.get("name") for net in root.findall("./nets/net")
           for node in net.findall("node") if node.get("ref") == "U202"}
io = {pin: net for pin, net in netlist.items()
      if not net.startswith("unconnected-") and net not in ("GND", "N2_V33_CPLD", "CPLD_JTMS", "CPLD_JTCK")}
SUPRA_NAMED = {"NRST": "4"}  # Supra names the dedicated reset pad PIN_NRST, not PIN_4
asf = {SUPRA_NAMED.get(p, p): net for p, net in
       re.findall(r"set_location_assignment PIN_(\w+) -to (\w+)", (HERE / "U202_pins.asf").read_text())}
ports = set(re.findall(r"^\s*(?:input|output)\s+(?:wire|reg)\s+(\w+)", (HERE / "link_fit_skeleton.v").read_text(), re.M))
errors = [f"pin {p}: netlist {io.get(p)} vs asf {asf.get(p)}" for p in sorted(set(io) | set(asf), key=int) if io.get(p) != asf.get(p)]
errors += [f"port set differs from asf: {sorted(ports ^ set(asf.values()))}"] if ports != set(asf.values()) else []
if errors:
    sys.exit("U202 pin constraints disagree with the netlist:\n  " + "\n  ".join(errors))
print(f"PASS: {len(asf)} U202 pins match the netlist and the skeleton ports")
