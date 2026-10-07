"""LTspice driver: write a deck, run it in batch mode, read the measurements.

The value of these decks is that every element value is *extracted from the
layout* -- copper resistance comes from the solved net, mounting inductance
from the real via geometry, capacitance from the placed part.  A deck written
from assumed values can only confirm the assumption.

LTspice reports ``.meas`` results for an AC analysis in decibels, formatted as
``name: expr=(X dB,Y deg) at F``.  :func:`parse_measurements` converts those
back to linear units; this was verified against an analytically solvable
R-L-C deck before being trusted.
"""

from __future__ import annotations

import os
import re
import subprocess

#: ``name: expr=(valuedB,phase°) ...`` -- the phase field may carry mojibake,
#: so only the leading numeric magnitude is captured.  The character classes
#: must exclude newlines: allowing them lets an unrelated preamble line such
#: as ``AsciiRawFile = true`` swallow the following measurement's value.
_MEAS_RE = re.compile(
    r"^[ \t]*(\w+):[^=\r\n]*=[ \t]*\(?[ \t]*(-?[\d.eE+]+)[ \t]*dB",
    re.MULTILINE)
#: Plain (non-dB) results, e.g. from an operating-point or transient measure.
_MEAS_PLAIN_RE = re.compile(
    r"^[ \t]*(\w+):[^=\r\n]*=[ \t]*(-?[\d.eE+]+)[ \t]*(?:$|[ \t])",
    re.MULTILINE)


class SpiceError(RuntimeError):
    pass


def db_to_linear(db: float) -> float:
    return 10.0 ** (db / 20.0)


#: A ``.step``ed run reports each measurement as a table:
#:
#:     Measurement: zmax
#:       step  MAX(mag(V(vdd)))  FROM  TO
#:            1  (-2.04dB,0deg)  100000  100000000
_STEP_HEADER_RE = re.compile(r"^Measurement:\s*(\w+)\s*$", re.MULTILINE)
_STEP_ROW_RE = re.compile(
    r"^\s*(\d+)\s+\(?\s*(-?[\d.eE+]+)\s*dB", re.MULTILINE)
_STEP_ROW_PLAIN_RE = re.compile(r"^\s*(\d+)\s+(-?[\d.eE+]+)\s*$", re.MULTILINE)


def parse_stepped_measurements(log_text: str) -> dict:
    """Return ``{name: [linear value per step]}`` for a ``.step``ed run."""
    out = {}
    matches = list(_STEP_HEADER_RE.finditer(log_text))
    for i, m in enumerate(matches):
        name = m.group(1).lower()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(log_text)
        block = log_text[m.end():end]
        vals = [db_to_linear(float(v)) for _, v in _STEP_ROW_RE.findall(block)]
        if not vals:
            vals = [float(v) for _, v in _STEP_ROW_PLAIN_RE.findall(block)]
        if vals:
            out[name] = vals
    return out


def parse_measurements(log_text: str) -> dict:
    """Return ``{name: linear_value}`` for every ``.meas`` line in the log.

    For a stepped run each name maps to the worst (largest) value across the
    sweep, which is the conservative reading for an impedance limit.
    """
    stepped = parse_stepped_measurements(log_text)
    out = {name: max(vals) for name, vals in stepped.items()}
    if out:
        return out
    for name, val in _MEAS_PLAIN_RE.findall(log_text):
        try:
            out[name.lower()] = float(val)
        except ValueError:
            pass
    # dB results take precedence: the same line matches both patterns, but the
    # dB form carries the correct interpretation.
    for name, val in _MEAS_RE.findall(log_text):
        try:
            out[name.lower()] = db_to_linear(float(val))
        except ValueError:
            pass
    return out


def run_deck(ltspice_exe: str, path: str, timeout: int = 180) -> dict:
    """Run one ``.cir`` in batch mode and return its parsed measurements."""
    if not ltspice_exe or not os.path.isfile(ltspice_exe):
        raise SpiceError(f"LTspice executable not available: {ltspice_exe!r}")
    path = os.path.abspath(path)
    log = os.path.splitext(path)[0] + ".log"
    if os.path.exists(log):
        os.remove(log)

    proc = subprocess.run([ltspice_exe, "-b", "-ascii", path],
                          capture_output=True, timeout=timeout)
    if not os.path.exists(log):
        raise SpiceError(
            f"LTspice produced no log for {os.path.basename(path)} "
            f"(exit {proc.returncode})")
    with open(log, "r", encoding="utf-8-sig", errors="replace") as fh:
        text = fh.read()
    if re.search(r"^\s*Fatal Error", text, re.MULTILINE | re.IGNORECASE):
        raise SpiceError(f"LTspice reported a fatal error in {path}:\n{text[:400]}")
    meas = parse_measurements(text)
    if not meas:
        raise SpiceError(
            f"No .meas results parsed from {os.path.basename(log)}; "
            f"log begins:\n{text[:400]}")
    return meas


def run_deck_stepped(ltspice_exe: str, path: str, timeout: int = 180) -> dict:
    """Like :func:`run_deck` but keeps every step's value.

    The caller decides how to reduce the sweep: an impedance limit wants the
    maximum across steps, while a crossover frequency wants the minimum.
    """
    meas = run_deck(ltspice_exe, path, timeout)
    log = os.path.splitext(os.path.abspath(path))[0] + ".log"
    with open(log, "r", encoding="utf-8-sig", errors="replace") as fh:
        text = fh.read()
    stepped = parse_stepped_measurements(text)
    return {k: stepped.get(k, [v]) for k, v in meas.items()} or stepped


def write_deck(directory: str, name: str, lines) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{name}.cir")
    with open(path, "w", encoding="ascii", errors="replace") as fh:
        fh.write("\n".join(lines) + "\n")
    return path
