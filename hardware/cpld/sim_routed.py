#!/usr/bin/env python3
"""Run link_fit_skeleton_tb.v on Supra's routed netlist (zero delay) with Icarus Verilog.

  sim_routed.py <supra_dir> <work_dir> [<iverilog_bin_dir>]

Supra's alta_sim.v holds SystemVerilog models (ADC, PLL) that Icarus cannot parse, so only the cell
models the routed netlist needs, and what they instantiate, are copied into <work_dir>/alta_cells.v.
"""
import re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
supra, work = Path(sys.argv[1]), Path(sys.argv[2])
bindir = sys.argv[3] if len(sys.argv) > 3 else None
iverilog = shutil.which("iverilog", path=bindir) or sys.exit("iverilog not found")
vvp = shutil.which("vvp", path=bindir) or sys.exit("vvp not found")

src = (supra / "etc/arch/rodinia/alta_sim.v").read_text(encoding="utf-8", errors="replace")
header = src[:src.index("\nmodule ")]          # defines; opens `ifdef _ALTA_LIB, closed below
models = {m.group(1): m.group(0) for m in re.finditer(r"^module\s+(\w+)\b.*?^endmodule", src, re.M | re.S)}
routed = work / "link_fit_skeleton_routed.v"
need = set(re.findall(r"^(alta_\w+) ", routed.read_text(), re.M))
cells, tb, out = work / "alta_cells.v", HERE / "link_fit_skeleton_tb.v", work / "routed_tb"
for _ in range(20):                             # add models until elaboration finds none missing
    cells.write_text(header + "\n" + "\n\n".join(models[m] for m in sorted(need)) + "\n`endif\n")
    r = subprocess.run([iverilog, "-g2012", "-o", str(out), str(routed), str(cells), str(tb)],
                       capture_output=True, text=True)
    missing = set(re.findall(r"Unknown module type: (\w+)", r.stdout + r.stderr)) & set(models)
    if not missing:
        break
    need |= missing
if r.returncode:
    sys.exit(r.stdout + r.stderr)
run = subprocess.run([vvp, "-n", str(out)], capture_output=True, text=True)
print(run.stdout.strip())
sys.exit(0 if "\nPASS" in "\n" + run.stdout else 1)
