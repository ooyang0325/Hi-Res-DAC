#!/bin/bash
# LTspice.exe-style CLI for the sign-off suite on macOS (LTspice 26 Wine bottle); the last argument
# is a POSIX deck path, passed to LTspice as Z:\...
deck="${@: -1}"; set -- "${@:1:$#-1}"
win="Z:$(printf '%s' "$deck" | tr '/' '\\')"
CX_BOTTLE_PATH="$HOME/Library/Application Support/LTspice/Bottles" exec /Applications/LTspice.app/Contents/SharedSupport/ltspice/LTspice/wine --bottle=ltspice --wait-children 'C:\Program Files\ADI\LTspice\LTspice.exe' "$@" "$win"
