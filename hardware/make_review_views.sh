#!/usr/bin/env bash
# Export visual PCB review views from the committed primary board.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  printf 'Usage: KICAD_CLI=/path/to/kicad-cli bash hardware/make_review_views.sh OUTPUT_DIR [BOARD_FILE]\n' >&2
  exit 2
fi

hardware_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
board="${2:-$hardware_dir/DAC_HPA.kicad_pcb}"
output_dir="$1"
kicad_cli="${KICAD_CLI:-kicad-cli}"
if [[ ! -f "$board" ]]; then
  printf 'PCB file not found: %s\n' "$board" >&2
  exit 2
fi
export KICAD10_3DMODEL_DIR="${KICAD10_3DMODEL_DIR:-$hardware_dir/KICAD_STOCK_MODELS}"
mkdir -p "$output_dir"

plot() {
  local filename="$1"
  local layers="$2"
  shift 2
  "$kicad_cli" pcb export svg --mode-single --layers "$layers" \
    --page-size-mode 2 --exclude-drawing-sheet "$@" \
    -o "$output_dir/$filename.svg" "$board"
}

plot 01_body_courtyard F.Fab,F.CrtYd,Edge.Cuts
plot 02_top_copper F.Cu,Edge.Cuts
# Plot the saved zone fill. Reviewers should separately refill zones after edits.
plot 03_l2_ground In1.Cu,Edge.Cuts
plot 04_top_mask F.Mask,Edge.Cuts
plot 05_top_paste F.Paste,Edge.Cuts
plot 06_top_silkscreen F.Silkscreen,Edge.Cuts
plot 07_bottom_copper B.Cu,Edge.Cuts --mirror
"$kicad_cli" pcb export glb --force -o "$output_dir/08_board_3d.glb" "$board"
"$kicad_cli" pcb drc --format json --severity-error --severity-warning \
  -o "$output_dir/09_drc.json" "$board"

printf 'Review views written to %s\n' "$output_dir"
printf 'SVGs are scalable; the GLB is a review-only 3D assembly.\n'
