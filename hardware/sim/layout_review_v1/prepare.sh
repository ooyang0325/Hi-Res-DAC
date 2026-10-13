#!/bin/bash
# prepare.sh EVIDENCE_ZIP : lay out the reviewer's evidence code next to these wrappers and build its
# copper model (pcbrev/model.pkl) from the committed board, using the reviewer's own parser.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ZIP="$1"; TMP="$(mktemp -d)"
unzip -q "$ZIP" -d "$TMP"
rm -rf "$HERE/analog_run" "$HERE/si_run" "$HERE/pw" "$HERE/pcbrev"
cp -R "$TMP/analog" "$HERE/analog_run"; cp -R "$TMP/si" "$HERE/si_run"
mkdir -p "$HERE/pw" "$HERE/pcbrev"; cp -R "$TMP/power" "$HERE/pw/power"; mkdir -p "$HERE/pw/power/cache"
cp "$TMP"/geometry/*.py "$HERE/pcbrev/"
sed -i '' "s|PCBREV = '/mnt/workspace/working/pcbrev'|PCBREV = '$HERE/pcbrev'|" "$HERE/si_run/brd.py"
cp "$HERE/../../DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb" "$HERE/pcbrev/board.kicad_pcb"
(cd "$HERE/pcbrev" && python3 -c "import sys,pickle; sys.path.insert(0,'.'); import sexp; pickle.dump(sexp.parse(open('board.kicad_pcb').read()), open('board.pkl','wb'))" && python3 model.py)
(cd "$HERE/pw/power" && python3 raster_cache.py)
echo "ready: python3 verify_s2.py; python3 verify_si.py; python3 verify_thermal.py; (cd pw/power && python3 pdn_transient.py)"
