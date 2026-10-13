#!/bin/bash
# prepare.sh EVIDENCE_ZIP : lay out the reviewer's v1.1 re-verification code next to this README and build its
# copper model (pcbrev2/model.pkl) from the committed board with the reviewer's own parser. No source edits:
# the code finds the model at ../../pcbrev2 relative to indrev2/power. Portable (no sed).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ZIP="$1"; TMP="$(mktemp -d)"
unzip -q "$ZIP" -d "$TMP"
rm -rf "$HERE/indrev2" "$HERE/pcbrev2"
mkdir -p "$HERE/indrev2" "$HERE/pcbrev2"
cp -R "$TMP/power" "$HERE/indrev2/power"; rm -rf "$HERE/indrev2/power/oldref"; mkdir -p "$HERE/indrev2/power/cache"
cp "$TMP"/geometry/*.py "$HERE/pcbrev2/"
cp "$HERE/../../DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb" "$HERE/pcbrev2/board.kicad_pcb"
(cd "$HERE/pcbrev2" && python3 -c "import sys,pickle; sys.path.insert(0,'.'); import sexp; pickle.dump(sexp.parse(open('board.kicad_pcb').read()), open('board.pkl','wb'))" && python3 model.py)
(cd "$HERE/indrev2/power" && python3 raster_cache.py)
echo "ready: cd $HERE/indrev2/power && python3 pdn_gndcheck_rev.py && python3 pdn_rev.py A && python3 pdn_rev.py B"
