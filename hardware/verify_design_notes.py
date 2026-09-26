#!/usr/bin/env python3
"""Check high-risk, machine-checkable schematic rules from Notes v0.9.

This complements verify_schematic.py: that script checks KiCad against the
workbook, while this checks selected independently stated rules in the notes.
It does not claim to cover firmware, layout, physical gates, or every rule in
the notes' Section 6 checklist.
"""

from __future__ import annotations

import re
from collections import Counter

from generate_schematic import apply_approved_overrides, read_source


def main() -> None:
    parts, pins, _ = read_source()
    checks = 0

    def pin(ref: str, number: str, net: str) -> None:
        nonlocal checks
        found = {p.number: p.net for p in pins[ref]}
        assert found[number] == net, f"{ref} pad {number}: {found[number]} != {net}"
        checks += 1

    def value(ref: str, expected: str) -> None:
        nonlocal checks
        assert parts[ref].value == expected, f"{ref}: {parts[ref].value} != {expected}"
        checks += 1

    def members(net: str, expected: set[tuple[str, str]]) -> None:
        nonlocal checks
        found = {(ref, p.number) for ref, group in pins.items() for p in group if p.net == net}
        assert found == expected, f"{net}: {sorted(found ^ expected)} differ"
        checks += 1

    # Notes Section 6 rules 1–5: connector, input TVS/clamp, and supply.
    for number, net in {
        "A1/B12": "GND", "B1/A12": "GND", "A4/B9": "VBUS", "B4/A9": "VBUS",
        "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP",
        "A7": "USB_DN", "B7": "USB_DN", "A8": "NC", "B8": "NC",
        "S1": "N1_SHIELD", "S2": "N1_SHIELD", "S3": "N1_SHIELD", "S4": "N1_SHIELD",
    }.items():
        pin("J101", number, net)
    pin("D102", "1", "VBUS")
    pin("D102", "2", "GND")
    for number, net in {"1": "5V_SYS", "2": "N1_U102_ILIM", "3": "NC", "4": "N1_U102_EN", "5": "GND", "6": "VBUS", "PAD": "GND"}.items():
        pin("U102", number, net)
    pin("U101", "5", "3V3M")
    value("R108", "100 kΩ")
    value("R109", "470 kΩ")
    value("C102", "2.2 µF")  # Spec v1.0 and detailed Notes; Section 6 row 4 is stale.
    value("C104", "100 nF")

    # Rules 12–18, 22, 25–28: clocks, DAC and current-to-voltage stage.
    for number, net in {"1": "MCLK_EN", "2": "GND", "3": "N2_AVCC_EN_G", "4": "N2_MCLK_OE", "5": "3V3D", "6": "N2_MCLK_PERMIT"}.items():
        pin("U206", number, net)
    for number, net in {"1": "N2_MCLK_OE", "2": "GND", "3": "N2_X201_OUT", "4": "3V3D"}.items():
        pin("X201", number, net)
    members("N2_X201_OUT", {("X201", "3"), ("R203", "1"), ("R227", "1")})
    value("R203", "33 Ω")
    value("R227", "10 kΩ")
    value("R665", "330 Ω")
    for ref in ("R207", "R208"):
        value(ref, "10 kΩ")
    for number, net in {"2": "GND", "5": "GND", "6": "NC", "7": "MCLK", "19": "GND", "22": "GND", "23": "DAC_LOCK", "24": "NC", "28": "DAC_RESETB", "EP": "GND"}.items():
        pin("U301", number, net)
    members("DAC_RESETB", {("U301", "28"), ("Q207", "3"), ("R305", "1"), ("TP746", "1")})
    for net, ref, opamp, feedback, capacitor in (
        ("DACL", "13", ("U403", "2"), "R423", "C417"),
        ("DACLB", "14", ("U403", "6"), "R424", "C418"),
        ("DACR", "9", ("U404", "2"), "R425", "C419"),
        ("DACRB", "10", ("U404", "6"), "R426", "C420"),
    ):
        members(net, {("U301", ref), opamp, (feedback, "1"), (capacitor, "1")})
        value(feedback, "698 Ω")
        value(capacitor, "820 pF")
    value("R431", "9.76 kΩ")
    value("R432", "10.0 kΩ")
    for ref in ("U403", "U404"):
        pin(ref, "3", "VREF")
        pin(ref, "5", "VREF")
        pin(ref, "8", "N4_VPOS_IV")
        pin(ref, "4", "N4_VNEG_IV")
    # Rules 23 and 28–32: DAC rails, I/V hold-up, clamp placement and leg outputs.
    for ref, rail in (("R301", "AVCC_L"), ("R302", "AVCC_R")):
        value(ref, "2.2 Ω")
        pin(ref, "1", "3V3A")
        pin(ref, "2", rail)
    for ref, source, rail in (("FB301", "3V3D", "DVCC"), ("FB302", "3V3A", "VCCA")):
        pin(ref, "1", source)
        pin(ref, "2", rail)
    for ref, rail, capacitance in (("C303", "AVCC_L", "2.2 µF"), ("C304", "AVCC_R", "2.2 µF"),
                                   ("C305", "AVCC_L", "100 nF"), ("C306", "AVCC_R", "100 nF"),
                                   ("C307", "VCCA", "100 nF"), ("C308", "DVCC", "100 nF"),
                                   ("C309", "1V3", "100 nF"), ("C310", "1V3", "2.2 µF"),
                                   ("C439", "DVCC", "2.2 µF"), ("C440", "VCCA", "2.2 µF")):
        value(ref, capacitance)
        pin(ref, "1", rail)
        pin(ref, "2", "GND")
    for ref, anode, cathode in (("D411", "VPOS", "N4_VPOS_IV"),
                               ("D412", "N4_VNEG_IV", "VNEG")):
        pin(ref, "1", cathode)
        pin(ref, "2", anode)
    for ref, anode, cathode in (("D413", "GND", "N4_VPOS_IV"),
                               ("D414", "N4_VNEG_IV", "GND")):
        pin(ref, "1", anode)
        pin(ref, "2", "NC")
        pin(ref, "3", cathode)
    pin("C442", "1", "N4_VPOS_IV")
    pin("C442", "2", "GND")
    pin("C443", "1", "GND")
    pin("C443", "2", "N4_VNEG_IV")
    for ref, rail, iv_output in (("D405", "AVCC_L", "N4_IVL_P"),
                                 ("D406", "AVCC_L", "N4_IVL_N"),
                                 ("D407", "AVCC_R", "N4_IVR_P"),
                                 ("D408", "AVCC_R", "N4_IVR_N")):
        pin(ref, "1", "GND")
        pin(ref, "2", rail)
        pin(ref, "3", iv_output)
    for ref in ("U401", "U402"):
        pin(ref, "2", "VPOS")
        pin(ref, "4", "VNEG")
        pin(ref, "8", "VPOS")
        pin(ref, "PAD", "VNEG")
    for ref, amp_output, leg in (("R417", "N4_LP_OUT", "LEG_LP"),
                                 ("R418", "N4_LN_OUT", "LEG_LN"),
                                 ("R419", "N4_RP_OUT", "LEG_RP"),
                                 ("R420", "N4_RN_OUT", "LEG_RN")):
        value(ref, "0 Ω")
        pin(ref, "1", amp_output)
        pin(ref, "2", leg)

    # Rules 13, 17–19 and 21: MCU/CPLD isolation, two clock families and test access.
    for number, net in {"1": "N2_LINK_SCK_BUF", "2": "LINK_FRAME", "3": "N2_LINK_MOSI_BUF", "4": "GND", "5": "LINK_MOSI", "6": "N2_LINK_FRAME_MCU", "7": "LINK_SCK", "8": "3V3D"}.items():
        pin("U208", number, net)
    for number, net in {"9": "LINK_SCK", "10": "LINK_MOSI", "11": "LINK_FRAME", "12": "LINK_MISO", "24": "CPLD_JTMS", "25": "CPLD_JTCK"}.items():
        pin("U202", number, net)
    for ref, enable, output in (("X202", "OSC48_EN", "N2_X202_OUT"), ("X203", "OSC44_EN", "N2_X203_OUT")):
        pin(ref, "1", enable)
        pin(ref, "3", output)
    pin("U205", "1", "N2_MUX_I1")
    pin("U205", "3", "N2_MUX_I0")
    pin("U205", "4", "N2_MUX_Y")
    pin("U205", "6", "OSC44_EN")
    for ref in ("R212", "R213", "R216", "R217", "R231", "R238", "R239"):
        value(ref, "10 kΩ")
    for ref in ("R210", "R211", "R215", "R224", "R225"):
        value(ref, "33 Ω")
    for ref in ("R228", "R229", "R230", "R242", "R243", "R244", "R245", "R246"):
        value(ref, "330 Ω")
    for number, net in {"20": "N2_LINK_FRAME_MCU", "21": "N2_LINK_SCK_MCU", "22": "LINK_MISO", "23": "N2_LINK_MOSI_MCU", "33": "N2_CAP_WS", "34": "N2_CAP_CK", "36": "N2_CAP_SD"}.items():
        pin("U201", number, net)
    pin("J201", "1", "N2_J201_3V3")
    pin("R241", "1", "3V3M")
    pin("R241", "2", "N2_J201_3V3")
    for ref, sense, pin_net in (("R242", "DC_SENSE_LP", "N2_DCS_LP_PIN"),
                                ("R243", "DC_SENSE_LN", "N2_DCS_LN_PIN"),
                                ("R244", "DC_SENSE_RP", "N2_DCS_RP_PIN"),
                                ("R245", "DC_SENSE_RN", "N2_DCS_RN_PIN"),
                                ("R246", "V3A_MON", "N2_V3A_MON_PIN")):
        pin(ref, "1", sense)
        pin(ref, "2", pin_net)

    # Rules 33–45, 53–60: always-on rail, switch isolation, latch and polarity.
    for number, net in {"1": "VBUS", "2": "GND", "3": "NC", "4": "NC", "5": "3V3M"}.items():
        pin("U502", number, net)
    for number, net in {"1": "GND", "2": "N5_DVDT", "3": "ANA_EN", "4": "5V_SYS", "5": "5V_ANA", "6": "ANA_FAULT_N", "7": "N5_ILIM", "8": "NC", "PAD": "GND"}.items():
        pin("U503", number, net)
    # Rules 24 and 34–41: regulator feedback, limit switch, rail readback and discharge.
    for number, net in {"1": "3V3D", "2": "GND", "3": "3V3D", "4": "N3_1V3_FB", "5": "1V3"}.items():
        pin("U303", number, net)
    value("R533", "15.0 kΩ")
    value("R534", "11.0 kΩ")
    pin("R533", "1", "1V3")
    pin("R533", "2", "N3_1V3_FB")
    pin("R534", "1", "N3_1V3_FB")
    pin("R534", "2", "GND")
    for number, net in {"1": "N5_ILIM_HI", "2": "GND", "3": "GND", "4": "ILIM_HI", "5": "3V3M"}.items():
        pin("U505", number, net)
    value("R510", "3.74 kΩ")
    value("R511", "100 kΩ")
    pin("R511", "1", "ILIM_HI")
    pin("R511", "2", "GND")
    value("R505", "100 kΩ")
    value("R522", "10 kΩ")
    value("R532", "470 kΩ")
    pin("R505", "1", "N5_PGOOD")
    pin("R505", "2", "5V_ANA_F")
    pin("R522", "1", "N5_PGOOD")
    pin("R522", "2", "RAILS_OK_N")
    pin("R532", "1", "RAILS_OK_N")
    pin("R532", "2", "GND")
    # Rules 36 and 39: LM27762 feedback and the ANA_SENSE divider.
    for number, net in {"2": "N5_FBP", "3": "5V_ANA_F", "6": "VNEG", "7": "N5_FBN", "8": "5V_ANA_F", "11": "VPOS", "12": "5V_ANA_F", "PAD": "GND"}.items():
        pin("U501", number, net)
    for ref, resistance, top, bottom in (("R501", "221 kΩ", "VPOS", "N5_FBP"),
                                        ("R502", "100 kΩ", "N5_FBP", "GND"),
                                        ("R503", "205 kΩ", "VNEG", "N5_FBN"),
                                        ("R504", "100 kΩ", "N5_FBN", "GND")):
        value(ref, resistance)
        pin(ref, "1", top)
        pin(ref, "2", bottom)
    for ref, resistance, top, bottom in (("R535", "100 kΩ", "5V_ANA_F", "ANA_SENSE"),
                                        ("R536", "47 kΩ", "ANA_SENSE", "GND")):
        value(ref, resistance)
        pin(ref, "1", top)
        pin(ref, "2", bottom)
    value("C516", "100 pF")
    pin("C516", "1", "ANA_SENSE")
    for ref, regulator_output in (("D104", "3V3A"), ("D105", "5V_ANA")):
        pin(ref, "1", regulator_output)
        pin(ref, "2", "NC")
        pin(ref, "3", "5V_SYS")
    for ref, gate, drain in (("Q502", "AVCC_EN", "N5_DIS_A"),
                             ("Q503", "N5_DIS_A", "N5_DIS_A_R"),
                             ("Q504", "AUD_EN", "N5_DIS_D"),
                             ("Q505", "N5_DIS_D", "N5_DIS_D_R"),
                             ("Q506", "N5_DIS_D", "N5_DIS_13_R")):
        pin(ref, "1", gate)
        pin(ref, "2", "GND")
        pin(ref, "3", drain)
    for ref, rail, drain, resistance in (("R527", "3V3A", "N5_DIS_A_R", "10 Ω"),
                                        ("R529", "3V3D", "N5_DIS_D_R", "10 Ω"),
                                        ("R530", "1V3", "N5_DIS_13_R", "4.7 Ω")):
        value(ref, resistance)
        pin(ref, "1", rail)
        pin(ref, "2", drain)
    pin("FB501", "1", "5V_ANA")
    pin("FB501", "2", "5V_ANA_F")
    value("C507", "10 µF")
    value("R531", "1 Ω")
    value("C513", "10 µF")
    for ref in ("R537", "R538"):
        value(ref, "100 kΩ")
    pin("Q507", "1", "N5_Q507_B")
    pin("Q507", "2", "GND")
    pin("Q507", "3", "N1_U102_EN")
    for ref, leg, jack in (("K601", "LEG_LP", "JACK_LP"), ("K602", "LEG_LN", "JACK_LN"), ("K603", "LEG_RP", "JACK_RP"), ("K604", "LEG_RN", "JACK_RN")):
        pin(ref, "3", "NC")
        pin(ref, "4", leg)
        pin(ref, "5", "NC")
        pin(ref, "6", jack)
    # Rules 43–45: two LED strings and four independent hardware permits.
    for ref, anode, cathode in (("K601", "5V_SYS", "N6_SL_A"),
                               ("K602", "N6_SL_A", "N6_SL_C"),
                               ("K603", "5V_SYS", "N6_SR_A"),
                               ("K604", "N6_SR_A", "N6_SR_C")):
        pin(ref, "1", anode)
        pin(ref, "2", cathode)
    for ref, emitter in (("R641", "N6_EL"), ("R642", "N6_ER")):
        value(ref, "24.9 Ω")
        pin(ref, "1", emitter)
        pin(ref, "2", "N6_EM")
    for ref, gate, drain, source in (("Q616", "N6_GMC", "N6_EM", "N6_M2"),
                                    ("Q617", "N6_H", "N6_M2", "N6_M3"),
                                    ("Q622", "N6_ARMG", "N6_M3", "GND")):
        pin(ref, "1", gate)
        pin(ref, "2", source)
        pin(ref, "3", drain)
    pin("R645", "1", "N2_MCLK_OE")
    pin("R645", "2", "N6_GMC")
    value("R645", "1 kΩ")
    value("R646", "100 kΩ")
    value("R647", "100 kΩ")
    # Rules 45–48: leg windows, common-mode window and slow DC sense.
    for ref, leg, filtered in (("R601", "LEG_LP", "N6_FLP"),
                               ("R602", "LEG_LN", "N6_FLN"),
                               ("R603", "LEG_RP", "N6_FRP"),
                               ("R604", "LEG_RN", "N6_FRN")):
        value(ref, "115 kΩ")
        pin(ref, "1", leg)
        pin(ref, "2", filtered)
    for ref, filtered, comparator in (("R649", "N6_FLP", "N6_CLP"),
                                      ("R650", "N6_FLN", "N6_CLN"),
                                      ("R651", "N6_FRP", "N6_CRP"),
                                      ("R652", "N6_FRN", "N6_CRN")):
        value(ref, "100 kΩ")
        pin(ref, "1", filtered)
        pin(ref, "2", comparator)
    for ref, expected in (("R607", "121 kΩ"), ("R608", "115 kΩ"),
                          ("R609", "10.0 kΩ"), ("R610", "10.0 kΩ")):
        value(ref, expected)
    for ref, output, common in (("R653", "N4_IVL_P", "N6_CML"),
                                ("R654", "N4_IVL_N", "N6_CML"),
                                ("R655", "N4_IVR_P", "N6_CMR"),
                                ("R656", "N4_IVR_N", "N6_CMR")):
        value(ref, "100 kΩ")
        pin(ref, "1", output)
        pin(ref, "2", common)
    for ref, common in (("C620", "N6_CML"), ("C621", "N6_CMR")):
        value(ref, "10 nF")
        pin(ref, "1", common)
        pin(ref, "2", "GND")
    value("R660", "330 kΩ")
    pin("R660", "1", "VPOS")
    pin("R660", "2", "N6_CMTH_LO")
    for n, sense, leg in ((0, "DC_SENSE_LP", "LEG_LP"), (1, "DC_SENSE_LN", "LEG_LN"),
                          (2, "DC_SENSE_RP", "LEG_RP"), (3, "DC_SENSE_RN", "LEG_RN")):
        source, pullup, pulldown, cap = (f"R{624+n}", f"R{628+n}", f"R{632+n}", f"C{608+n}")
        value(source, "6.8 kΩ")
        pin(source, "1", leg)
        pin(source, "2", sense)
        value(pullup, "5.1 kΩ")
        pin(pullup, "1", sense)
        pin(pullup, "2", "3V3A")
        value(pulldown, "16.9 kΩ")
        pin(pulldown, "1", sense)
        pin(pulldown, "2", "GND")
        value(cap, "4.7 µF")
        pin(cap, "1", sense)
        pin(cap, "2", "GND")
    for number, net in {"1": "RELAY_EN", "2": "N6_CLR_N", "3": "NC", "5": "N6_ARM", "6": "N6_CLR_N", "7": "3V3D", "8": "3V3D"}.items():
        pin("U608", number, net)
    for number, net in {"10": "N6_H", "11": "N6_HREF", "13": "N6_TRIP"}.items():
        pin("U606", number, net)
    for ref in ("U609", "U610"):
        pin(ref, "13", "N6_H")
        pin(ref, "14", "N6_H")
    # Rules 49–51 and 58–59: supervisor, MCLK detector, latch and timers.
    for number, net in {"1": "N6_V3AG_A", "2": "N6_V3A_DA", "3": "N6_V3R_A", "4": "GND", "5": "N6_V3R_B", "6": "N6_V3A_DB", "7": "N6_V3AG_B", "8": "3V3M"}.items():
        pin("U605", number, net)
    pin("Q619", "1", "N6_V3AG_A")
    pin("Q619", "3", "N2_AVCC_EN_G")
    pin("Q620", "1", "N6_V3AG_B")
    pin("Q620", "3", "AUD_EN")
    for ref in ("R688", "R689"):
        value(ref, "470 kΩ")
    for number, net in {"1": "NC", "2": "N6_MCK_IN", "3": "GND", "4": "N6_MCK_BUF", "5": "3V3D"}.items():
        pin("U607", number, net)
    value("C624", "100 pF")
    value("C625", "82 pF")
    value("R666", "1.00 MΩ")
    value("R667", "100 kΩ")
    value("R668", "1.00 MΩ")
    value("R669", "100 kΩ")
    for number, net in {"1": "GND", "2": "N6_MCK_RC", "3": "N6_PMP"}.items():
        pin("D609", number, net)
    for number, net in {"1": "N6_V13_TI", "2": "NC", "3": "N6_V13_TEST"}.items():
        pin("D610", number, net)
    pin("Q621", "1", "N6_TRIP")
    pin("Q621", "3", "N6_CLR_N")
    for ref, v in (("R690", "330 kΩ"), ("R691", "100 kΩ"),
                   ("R692", "1 kΩ"), ("R693", "100 kΩ"),
                   ("R694", "330 kΩ"), ("R695", "100 kΩ"), ("R696", "100 kΩ")):
        value(ref, v)
    for ref, timer in (("R920", "N6_TLP_L"), ("R921", "N6_TLN_L"),
                       ("R922", "N6_TLP_R"), ("R923", "N6_TLN_R")):
        value(ref, "110 kΩ")
        pin(ref, "1", "VPOS")
        pin(ref, "2", timer)
    value("R924", "69.8 kΩ")
    value("R925", "100 kΩ")
    pin("R924", "2", "N6_VT")
    pin("R925", "1", "N6_VT")
    for ref, output, timer in (("Q623", "N6_OLP_L", "N6_TLP_L"),
                               ("Q624", "N6_OLN_L", "N6_TLN_L"),
                               ("Q625", "N6_OLP_R", "N6_TLP_R"),
                               ("Q626", "N6_OLN_R", "N6_TLN_R")):
        pin(ref, "1", output)
        pin(ref, "2", "GND")
        pin(ref, "3", timer)
    for ref in ("D705", "D706"):
        pin(ref, "1", "GND")
    value("R509", "4.75 kΩ")
    for ref in ("C631", "C632", "C633", "C634"):
        value(ref, "220 nF")
    assert "D103" not in parts
    assert "RAIL_EN" not in {p.net for group in pins.values() for p in group}
    checks += 2
    fit = Counter(part.fit for part in parts.values())
    assert fit == {"Yes": 412, "Owner": 7, "No": 9, "Pads": 3, "No part": 52}, fit
    assert {ref for ref, part in parts.items() if part.fit == "Owner"} == {"K601", "K602", "K603", "K604", "J701", "D102", "R509"}
    assert {ref for ref, part in parts.items() if part.fit == "No"} == {"C101", "C441", "C513", "J703", "R241", "R446", "R447", "R531", "R703"}
    checks += 3
    # Rule 57: every fitted 0.1 % resistor above 240 kΩ uses 0603 lands.
    high_precision = set()
    for ref, part in parts.items():
        if not ref.startswith("R") or not part.rating_tolerance.startswith("0.1 %") or part.fit == "No":
            continue
        match = re.fullmatch(r"([0-9.]+)\s*([kM]?)Ω", part.value)
        if not match:
            raise AssertionError(f"Cannot decode precision resistor {ref}: {part.value!r}")
        ohms = float(match.group(1)) * {"": 1, "k": 1_000, "M": 1_000_000}[match.group(2)]
        if ohms > 240_000:
            assert part.package == "0603", f"{ref} {part.value} 0.1 % package is {part.package}"
            high_precision.add(ref)
            checks += 1
    assert high_precision == {"R677", "R684", "R678", "R685", "R900", "R902", "R904", "R906", "R908", "R910", "R912", "R914", "R901", "R903", "R905", "R907", "R909", "R911", "R913", "R915"}
    checks += 1
    corrected_pins = apply_approved_overrides(pins)
    for ref, drive in (("D705", "N7_LEDG_A"), ("D706", "N7_LEDR_A")):
        corrected = {item.number: (item.name, item.net) for item in corrected_pins[ref]}
        assert corrected == {"1": ("A", drive), "2": ("K", "GND")}, (ref, corrected)
        checks += 2
    j701 = {item.number: (item.name, item.net) for item in corrected_pins["J701"]}
    expected_j701 = {
        "1": ("GND", "GND"),
        "2": ("R-", "JACK_RN"), "3": ("R-", "JACK_RN"),
        "4": ("R+", "JACK_RP"), "5": ("R+", "JACK_RP"),
        "6": ("L-", "JACK_LN"),
        "7": ("L+", "JACK_LP"), "8": ("L+", "JACK_LP"),
        "9": ("SWITCH", "NC"), "10": ("DETECT", "NC"),
        "11": ("EP", "NC"), "12": ("EP", "NC"),
    }
    assert set(j701) == set(expected_j701)
    checks += 1
    for number, (name, net) in expected_j701.items():
        assert j701[number][0] == name, (number, j701[number], name)
        assert j701[number][1] == net, (number, j701[number], net)
        checks += 2
    print(f"PASS: {checks} selected design-note pin, value, membership, and fit checks")
    print("CORRECTED: D705/D706/J701 owner-approved physical pad maps differ from the source checklist")
    print("OPEN: J101/J701/J702 and G-1–G-4 remain unverified")


if __name__ == "__main__":
    main()
