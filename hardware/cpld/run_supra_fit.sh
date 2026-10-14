#!/usr/bin/env bash
# OD-16 fit of link_fit_skeleton.v on U202 (AGRV2KQ32) with AGM Supra's native flow: Supra setup,
# Supra's bundled Yosys mapper, then Supra place-and-route and timing. No Quartus licence needed.
#   hardware/cpld/run_supra_fit.sh <supra_dir> [<work_dir>]
# <supra_dir> holds bin/af.exe (Windows, Git Bash) or bin/af. <work_dir> must not contain spaces.
# Prints the timing summary and the drive/slew fields of the outputs; reports stay in <work_dir>/alta_db.
set -euo pipefail
SUPRA=${1:?usage: run_supra_fit.sh <supra_dir> [<work_dir>]}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${2:-$(mktemp -d)}
AF=$SUPRA/bin/af; [ -x "$AF.exe" ] && AF=$AF.exe
YOSYS=$SUPRA/map/bin/yosys; [ -x "$YOSYS.exe" ] && YOSYS=$YOSYS.exe

mkdir -p "$WORK"; cd "$WORK"
cp "$HERE/link_fit_skeleton.v" .
"$AF" --setup --design link_fit_skeleton --device AGRV2KQ32 --verilog link_fit_skeleton.v > setup.out 2>&1
cp "$HERE/link_fit.sdc" link_fit_skeleton.sdc     # setup writes empty .sdc/.asf; use ours
cp "$HERE/U202_pins.asf" link_fit_skeleton.asf
"$YOSYS" -TQd -v 1 -L map.log -c af_map.tcl > map.out 2>&1
"$AF" --batch --mode NATIVE > run.out 2>&1

grep -E '^ +[0-9]+ +(alta_bram9k|cycloneive_lcell_comb|dffeas)$' map.log | tail -3
grep -E "Total  Logic    Counts|Global    Signals" alta_logs/run.log | head -2
sed -n '/=== User constraints ===/,/=== Auto constraints ===/p' alta_db/setup_summary.rpt
sed -n '/Clock transfer report/,/^$/p' alta_db/hold_summary.rpt
grep -E "Found GCLK net" alta_logs/run.err || true
grep -E "^Error|Total .* fatals" alta_logs/run.err
grep -E "defparam \w+_o\.(CFG_SLR|CFG_PDRCTRL) " link_fit_skeleton_routed.v | sed 's/defparam //' | paste - -
echo "work dir: $WORK"

# The functional test on the routed netlist, when Icarus Verilog is installed (IVERILOG_BIN or PATH).
if command -v python >/dev/null && { [ -n "${IVERILOG_BIN:-}" ] || command -v iverilog >/dev/null; }; then
  echo "routed-netlist test:"; python "$HERE/sim_routed.py" "$SUPRA" "$WORK" ${IVERILOG_BIN:+"$IVERILOG_BIN"}
fi
