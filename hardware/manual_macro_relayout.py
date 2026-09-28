#!/usr/bin/env python3
"""Apply hand-selected v2 macro positions to a separate placement study.

Coordinates below are design decisions, not the output of a placement search.
The source PCB, including any local outline edit, is never overwritten. Run
the independent placement, DFM and KiCad checks before considering promotion.
"""

from pathlib import Path

import pcbnew


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "DAC_HPA.kicad_pcb"
OUTPUT = HERE / "DAC_HPA_120x100_MACRO_STUDY_ONLY.kicad_pcb"

# (absolute KiCad x mm, absolute KiCad y mm, counterclockwise degrees).
# These are individually chosen locations; no packing/search is performed.
MOVES: dict[str, tuple[float, float, int]] = {
    # Hand translation of the already compact output-amplifier cores into the
    # open x=118..127 corridor. This gives T networks room to join them and
    # shortens their run toward the relay contact side.
    "C401": (119.5, 68.0, 90), "C402": (122.0, 79.0, 0),
    "C403": (120.0, 81.5, 90), "C404": (118.0, 92.0, 0),
    "C407": (121.5, 98.5, 0), "C432": (119.0, 71.5, 90),
    "C433": (122.0, 77.0, 0), "C434": (122.5, 81.0, 0),
    "C435": (119.5, 78.0, 90), "C436": (125.0, 81.0, 90),
    "C437": (118.0, 94.0, 0), "C438": (118.0, 90.0, 0),
    "R404": (118.0, 74.0, 0), "R405": (124.5, 77.5, 90),
    "R406": (126.5, 77.5, 90), "R407": (127.0, 81.0, 90),
    "R408": (126.0, 75.0, 0), "R409": (121.5, 89.5, 0),
    "R410": (126.0, 73.0, 0), "R411": (121.5, 91.5, 0),
    "R414": (120.5, 94.0, 90), "R415": (118.0, 96.0, 0),
    "R416": (122.5, 94.0, 90), "R417": (121.5, 70.0, 0),
    "R418": (122.0, 82.5, 0), "R419": (117.5, 77.5, 0),
    "R420": (117.5, 88.5, 0), "R440": (126.0, 71.0, 0),
    "R444": (121.5, 96.5, 0), "R445": (118.0, 98.0, 0),
    "U401": (122.2, 73.0, 0), "U402": (121.2, 86.0, 0),
    # DAC/I-V: keep U301 fixed. U403 leaves the north supply-pin corridor;
    # both dual amplifiers sit to the east with room for their feedback pairs.
    "U403": (97.0, 76.5, 0),
    "U404": (96.0, 85.5, 0),
    "R423": (96.3, 81.0, 0), "C417": (100.0, 81.0, 0),
    "R424": (96.0, 71.5, 0), "C418": (100.0, 71.5, 0),
    "R425": (96.0, 90.0, 0), "C419": (100.0, 90.0, 0),
    "R426": (102.0, 84.0, 0), "C420": (102.0, 86.5, 0),
    "C423": (93.5, 73.5, 0), "C424": (101.5, 78.5, 0),
    "C425": (99.5, 82.6, 0), "C426": (99.5, 88.5, 0),
    # DAC supply-pin breakout and larger capacitors behind the HF parts.
    "C303": (92.0, 75.2, 90), "C304": (90.0, 75.2, 90),
    "C305": (92.0, 72.8, 0), "C306": (90.0, 72.8, 0),
    "C307": (88.0, 76.5, 0), "C308": (86.0, 76.5, 90),
    "C309": (85.5, 78.0, 0),
    "C439": (87.5, 68.0, 0), "C440": (91.5, 68.0, 0),
    "R301": (92.0, 70.1, 90), "R302": (87.5, 70.0, 0),
    "FB301": (85.0, 73.0, 90), "FB302": (86.5, 71.5, 0),
    # U302/U303 each retain their own input/output/feedback neighbourhood.
    "C301": (78.0, 75.5, 90), "C302": (82.5, 80.0, 0),
    "C310": (88.0, 55.5, 90), "C311": (84.5, 52.5, 0),
    "R305": (88.0, 58.5, 0),
    # Four complete LPW comparator pairs in two rows. Signal taps enter from
    # outside; their filtered/high-value nodes stay inside each local macro.
    "U613": (100.0, 49.0, 0), "U614": (106.0, 49.0, 0),
    "U615": (100.0, 63.0, 0), "U616": (106.0, 63.0, 0),
    "U617": (117.0, 49.0, 0), "U618": (123.0, 49.0, 0),
    "U619": (117.0, 63.0, 0), "U620": (123.0, 63.0, 0),
    "R930": (95.5, 46.0, 90), "C643": (95.5, 50.0, 90),
    "R931": (95.5, 60.0, 90), "C644": (95.5, 64.0, 90),
    "R932": (112.0, 46.0, 90), "C645": (112.0, 50.0, 90),
    "R933": (112.0, 60.0, 90), "C646": (112.0, 64.0, 90),
    "C647": (100.0, 43.5, 0), "C648": (106.0, 43.5, 0),
    "C649": (100.0, 57.5, 0), "C650": (106.0, 57.5, 0),
    "C651": (117.0, 43.5, 0), "C652": (123.0, 43.5, 0),
    "C653": (117.0, 57.5, 0), "C654": (123.0, 57.5, 0),
    "R942": (103.0, 43.5, 90), "R943": (109.0, 43.5, 90),
    "R944": (103.0, 57.5, 90), "R945": (109.0, 57.5, 90),
    "R946": (120.0, 43.5, 90), "R947": (126.0, 43.5, 90),
    "R948": (120.0, 57.5, 90), "R949": (126.0, 57.5, 90),
    "C659": (97.0, 46.5, 90), "C660": (109.0, 46.5, 90),
    "C661": (97.0, 60.5, 90), "C662": (109.0, 60.5, 90),
    "C663": (114.0, 46.5, 90), "C664": (126.0, 46.5, 90),
    "C665": (114.0, 60.5, 90), "C666": (126.0, 60.5, 90),
    "R938": (110.0, 51.0, 0), "R939": (110.0, 53.5, 0),
    "R940": (110.0, 63.0, 0), "R941": (110.0, 65.5, 0),
    # Digital and family-clock bypasses follow the devices they serve.
    "C224": (89.8, 66.0, 0),
    "C222": (76.0, 61.6, 0),
    "C218": (74.0, 57.6, 0), "C219": (74.0, 73.4, 0),
    "C217": (90.3, 93.0, 0),
    "C223": (87.0, 91.5, 0),
    # Charge-pump input, flying and output capacitors remain with U501.
    "C507": (58.0, 127.0, 90), "C508": (62.0, 131.0, 0),
    "C509": (66.0, 127.0, 90), "C510": (59.0, 123.0, 90),
    "C511": (66.0, 123.0, 0),
    "R501": (60.0, 131.0, 90), "R502": (64.0, 131.0, 90),
    "R503": (69.0, 126.0, 90), "R504": (69.0, 123.0, 90),
}

# Second visual pass: clear the upper-right detector reservation by moving
# displaced output/analog parts into the output, DAC-rail and VREF macros.
# These overrides remain explicit hand-selected positions, not an optimizer.
MOVES.update({
    "U403": (96.9, 76.5, 0),
    "R412": (115.0, 87.5, 0), "R441": (115.0, 80.0, 0),
    "R442": (115.0, 84.0, 0), "R443": (115.0, 92.0, 0),
    "R419": (130.0, 78.0, 0), "R420": (130.0, 89.0, 0),
    "R401": (112.0, 69.0, 0), "R402": (115.0, 69.0, 0),
    "R403": (112.0, 71.5, 0), "R438": (115.0, 71.5, 0),
    "R439": (112.0, 74.0, 0), "C431": (115.0, 74.0, 0),
    "C405": (115.0, 90.0, 0),
    "C409": (125.0, 68.0, 0), "C410": (128.0, 69.0, 0),
    "C411": (116.0, 67.8, 0), "C412": (128.0, 66.8, 0),
    "C413": (113.0, 84.0, 0), "C414": (128.0, 84.0, 0),
    "C415": (112.0, 86.5, 0), "C416": (128.0, 86.5, 0),
    "R431": (109.0, 77.0, 0), "R432": (109.0, 79.5, 0),
    "C421": (109.0, 82.0, 0), "C441": (109.0, 84.5, 0),
    "D406": (105.0, 74.0, 0), "D405": (105.0, 78.5, 0),
    "D408": (105.0, 83.5, 0), "D407": (105.0, 88.5, 0),
    "C442": (130.0, 104.0, 0), "C443": (130.0, 112.0, 0),
    "D411": (122.0, 102.0, 0), "D412": (124.0, 111.0, 0),
    "C423": (99.5, 73.0, 0),
    "C439": (84.0, 69.0, 0), "C440": (88.0, 69.0, 0),
    "R301": (93.0, 70.5, 90), "R302": (88.0, 72.0, 0),
    "C305": (94.0, 74.0, 0),
    "FB301": (80.5, 69.5, 90), "FB302": (83.5, 72.0, 0),
    "TP707": (78.0, 69.0, 0), "TP710": (94.0, 67.5, 0),
    "TP746": (96.0, 69.5, 0),
    "C224": (91.0, 65.5, 0), "C222": (78.0, 61.0, 0),
    "C218": (77.0, 60.0, 0), "C219": (77.0, 70.0, 90),
    "C223": (85.0, 88.0, 90),
    "TP711": (92.5, 88.0, 0), "R703": (95.0, 93.5, 90),
    # Move the stray OR resistor back toward its comparator group.
    "R927": (121.0, 104.5, 0),
})

# Third hand pass: open measurable gaps around the packages instead of
# accepting touching bounding rectangles as usable routing space.
MOVES.update({
    "R439": (110.8, 74.0, 0), "C431": (114.3, 74.0, 0),
    "R404": (117.8, 74.0, 0),
    "R401": (111.5, 69.0, 0), "R402": (115.0, 69.0, 0),
    "R403": (111.5, 71.5, 0), "R438": (115.0, 71.5, 0),
    "C411": (112.0, 66.8, 0),
    "R443": (114.5, 92.0, 0), "C405": (114.5, 90.0, 0),
    "FB302": (81.0, 72.0, 0), "R302": (85.5, 72.0, 0),
    "C423": (100.0, 73.8, 0),
    "R653": (107.0, 73.5, 0), "R656": (112.0, 95.5, 0),
    "D406": (104.0, 70.0, 0), "D407": (105.0, 90.5, 0),
    "R655": (109.5, 93.5, 90),
    "R426": (100.0, 84.5, 0), "C425": (100.0, 82.8, 0),
    "TP709": (91.5, 61.0, 0), "TP750": (91.5, 65.0, 0),
    "D413": (105.0, 99.0, 0), "D414": (110.0, 99.0, 0),
    "R303": (78.5, 80.0, 0),
    "C218": (78.5, 57.5, 0), "TP717": (80.0, 58.0, 0),
    "TP707": (80.0, 67.0, 0), "TP712": (75.0, 74.0, 0),
    "TP716": (73.0, 75.0, 0), "TP715": (85.0, 70.0, 0),
    "R205": (83.0, 68.0, 90), "TP746": (99.0, 68.0, 0),
    # Revert the first charge-pump sketch while rebuilding its entire
    # surrounding supply macro; these original positions are not signed off.
    "C507": (62.0, 123.5, 90), "C508": (60.0, 130.0, 0),
    "C509": (64.5, 123.5, 90), "C510": (49.0, 120.0, 90),
    "C511": (59.0, 115.0, 0),
    "R501": (62.5, 130.5, 90), "R502": (60.0, 132.0, 0),
    "R503": (66.5, 123.5, 90), "R504": (64.5, 120.0, 90),
    # Keep the two hold-up diodes beside the south-east reservoirs, and
    # regroup the shared OR reference/test injection around Q627.
    "D411": (122.0, 98.5, 0), "D412": (121.0, 106.5, 0),
    "Q627": (113.0, 105.0, 90),
    "R934": (110.0, 101.0, 0), "R935": (112.5, 101.0, 0),
    "R936": (115.0, 101.0, 0), "R937": (117.5, 101.0, 0),
    "R950": (110.0, 108.0, 0), "R951": (113.0, 108.0, 0),
})

# Fourth visual pass: the OR injection/divider is collected in an open strip
# below K601, while existing U604 inputs retain their own lower-right space.
MOVES.update({
    "Q627": (128.0, 99.0, 90),
    "R934": (125.0, 92.0, 0), "R935": (127.2, 92.0, 0),
    "R936": (129.4, 92.0, 0), "R937": (131.6, 92.0, 0),
    "R950": (127.0, 94.5, 0), "R951": (130.0, 94.5, 0),
    "D411": (121.0, 102.0, 0), "D412": (121.0, 107.0, 0),
    "TP743": (117.0, 107.0, 0),
    "C408": (125.0, 90.0, 0), "C406": (126.0, 87.5, 90),
    "D413": (105.0, 97.2, 0), "D414": (110.0, 99.0, 0),
    "TP745": (115.0, 96.5, 0),
    "C413": (111.0, 84.0, 0), "C415": (114.8, 87.0, 0),
    "R412": (117.0, 87.5, 0), "R442": (115.0, 84.0, 0),
    "C441": (108.0, 87.0, 0),
    "C218": (70.0, 61.0, 0), "TP717": (86.0, 60.0, 0),
    "TP707": (76.0, 78.0, 0), "TP715": (80.0, 82.0, 0),
    "TP750": (93.5, 62.0, 0),
    "C439": (83.0, 69.0, 0), "C440": (89.0, 69.0, 0),
    "R205": (91.5, 68.0, 90), "R301": (94.0, 71.0, 90),
    "R204": (77.5, 72.5, 90),
})

MOVES.update({
    "U301": (90.5, 81.0, 0),
    "R301": (92.0, 71.0, 90),
    "C416": (130.0, 87.0, 0),
    "C218": (74.0, 56.8, 0), "R228": (81.5, 53.5, 0),
    "R231": (83.0, 59.0, 90),
    "TP715": (83.0, 84.0, 0),
    "C415": (112.5, 87.0, 0),
    "TP744": (118.0, 104.5, 0), "TP743": (123.5, 110.0, 0),
})

# Put the three I²S source resistors in one south-facing row, with the link
# buffer lifted out of that corridor. Their routes still require a real trial.
MOVES.update({
    "R204": (82.5, 69.0, 90), "R205": (85.0, 69.0, 90),
    "R206": (87.5, 69.0, 0),
    "C439": (96.0, 69.0, 0), "C440": (100.0, 69.0, 0),
    "R654": (94.0, 65.0, 0), "C644": (96.0, 64.0, 90),
    "TP746": (97.0, 66.0, 0),
    "U208": (92.0, 59.0, 0), "C224": (96.5, 57.5, 0),
    "TP709": (88.0, 61.0, 0),
    "TP746": (91.0, 67.5, 0), "TP710": (91.0, 64.5, 0),
})

# Restore the clock-to-sensitive-pad separation while keeping the BCLK probe
# close to its intended DAC-side run and the U208 bypass in the same macro.
MOVES.update({
    "TP715": (85.3, 79.8, 0),
    "U208": (90.0, 55.0, 0), "C224": (94.0, 55.0, 0),
    "C310": (88.0, 59.0, 90), "TP709": (87.0, 62.0, 0),
    "R305": (84.5, 59.5, 0),
    "R413": (108.5, 95.0, 90), "R655": (111.0, 92.0, 90),
    "TP717": (86.0, 63.0, 0), "TP709": (89.0, 65.0, 0),
})

# Charge-pump loop rebuilt in the free lower-left strip: the flying,
# input/CP and two output capacitors surround U501, with feedback nearby.
MOVES.update({
    "U501": (72.0, 132.0, 0),
    "C507": (68.5, 131.0, 90), "C508": (72.0, 128.5, 0),
    "C509": (76.0, 132.0, 90), "C510": (68.5, 135.0, 90),
    "C511": (75.5, 135.5, 0),
    "R501": (65.5, 130.5, 90), "R502": (72.0, 135.0, 0),
    "R503": (79.0, 134.5, 90), "R504": (65.5, 134.5, 90),
    "C642": (83.0, 131.0, 90),
    "TP722": (69.0, 126.5, 0), "TP752": (62.0, 135.0, 0),
    "R535": (60.5, 129.5, 0), "C516": (62.5, 129.5, 90),
})

# Begin distributing MCU supply capacitors to the actual north/bottom supply
# pins. The west/USB edge is intentionally reserved until pair escape is drawn.
MOVES.update({
    "C221": (70.0, 50.0, 90),
    "C203": (61.5, 54.5, 90),
    "C204": (67.0, 72.5, 0), "C205": (69.5, 72.5, 0),
})

# Move the OR comparator's right IC and bring all four high-value LEG taps,
# their filters and the shared threshold divider beside the two packages.
# The low-impedance LEG inputs may travel farther; N6_ORxx starts locally.
MOVES.update({
    "U612": (96.0, 125.0, 0),
    "R926": (76.0, 122.0, 0), "C639": (76.0, 125.0, 0),
    "R927": (76.0, 128.0, 0), "C640": (76.0, 131.0, 90),
    "R928": (101.0, 121.5, 0), "C641": (101.0, 124.5, 90),
    "R929": (101.0, 128.0, 0), "C642": (101.0, 131.0, 90),
    "C638": (103.0, 125.5, 90),
    "R934": (87.0, 122.0, 0), "R935": (87.0, 125.0, 0),
    "R936": (90.0, 122.0, 0), "R937": (90.0, 125.0, 0),
    "Q627": (89.0, 132.0, 90),
    "R950": (87.0, 136.0, 0), "R951": (90.0, 136.0, 0),
    "R701": (84.5, 133.5, 0),
    "R916": (80.0, 131.0, 0), "R917": (83.0, 131.0, 0),
    "R918": (94.0, 131.0, 0), "R919": (97.0, 131.0, 0),
})

# The first OR grouping exposed conflicts with nearby H/clock-monitor parts.
# Put the left tap/filter bank in the free gap above U611, keep H bypass by
# that comparator, and leave the clock-monitor reference beside U606.
MOVES.update({
    "R926": (80.2, 119.0, 0), "C639": (82.7, 119.0, 0),
    "R927": (85.2, 119.0, 0), "C640": (88.0, 119.0, 90),
    "C617": (85.5, 131.0, 90), "R647": (134.0, 116.0, 0),
    "TP718": (82.0, 136.0, 0),
    "R663": (104.0, 117.0, 90), "R669": (94.5, 119.5, 90),
    "R668": (91.3, 119.5, 90),
    "R662": (115.5, 106.5, 0),
    "C626": (91.5, 128.0, 90),
    "R919": (104.0, 119.5, 0),
})

# Align each OR tap/filter with the package pins it serves: LP/RP enter the
# lower comparator row, LN/RN the upper row. This removes the remaining long
# high-impedance branch created by the first compacting pass.
MOVES.update({
    "R926": (80.0, 131.0, 0), "C639": (82.5, 131.0, 0),
    "R928": (101.0, 129.5, 0), "C641": (101.0, 126.5, 90),
    "R929": (103.0, 122.0, 0), "C642": (101.0, 122.5, 90),
    "R916": (105.0, 124.5, 0), "R917": (108.0, 124.5, 0),
    "R919": (109.5, 122.0, 0),
})

# Two previously remote IC bypasses now sit by their actual supply pins.
MOVES.update({
    "C628": (74.0, 79.5, 0),
    "C630": (92.5, 137.0, 0),
    "C507": (68.5, 128.5, 90), "C510": (68.5, 133.0, 90),
    "TP722": (69.0, 124.0, 0),
})

# Repack the narrow U403/U404 east strip so the Rf/Cf branches and rail caps
# have separate vertical lanes; this reduces the long C420 feedback branch.
MOVES.update({
    "C417": (100.5, 77.8, 0), "C424": (101.5, 79.55, 0),
    "C420": (100.5, 81.4, 0), "C425": (100.0, 83.2, 0),
    "R426": (100.0, 85.0, 0),
})


def main() -> None:
    board = pcbnew.LoadBoard(str(SOURCE))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if len(footprints) != 536:
        raise SystemExit(f"Unexpected primary footprint count: {len(footprints)}")
    missing = sorted(set(MOVES) - set(footprints))
    if missing:
        raise SystemExit(f"Missing footprints: {missing}")
    for ref, (x_mm, y_mm, angle) in MOVES.items():
        fp = footprints[ref]
        fp.SetOrientationDegrees(angle)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
    for drawing in board.GetDrawings():
        if (isinstance(drawing, pcbnew.PCB_TEXT)
                and drawing.GetText().startswith("MANUAL LAYOUT REVIEW")):
            drawing.SetText("MACRO PLACEMENT V2 — REVIEW ONLY — PARTIAL COPPER")
    pcbnew.SaveBoard(str(OUTPUT), board)
    print(f"Saved {OUTPUT.name}: {len(MOVES)} hand-selected footprint moves")


if __name__ == "__main__":
    main()
