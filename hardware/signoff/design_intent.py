"""Declared electrical intent for the DAC_HPA board.

The gates need to know what each net *is* before they can judge the copper that
implements it: its nominal voltage, its DC current budget, and whether it is a
clock, an analogue audio path or plain logic.

These values are stated here explicitly, with the reasoning, rather than being
inferred from the layout, so that a reviewer can argue with the assumption
instead of having to reverse-engineer it.  Anything the gates could not justify
from the schematic is marked ``assumed`` and is reported as such.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Supply rails: nominal voltage and the DC current the copper must carry.
# ---------------------------------------------------------------------------
# Current budgets are the design maxima from the Calculation Package v1.1
# (doc/DAC_HPA_Calculation_Package_v1.1.zip, power/calc c03/c17, 26 Sep 2026),
# reconciled on 7 Oct 2026 after the first run of this suite used estimates:
#   VBUS         S4 High mode 765.27 mA (NDK X201 second source), c17 section 3.
#   5V_SYS       S4 less the 3V3M branch (U502 is fed from VBUS): <= 0.69 A.
#   5V_ANA(_F)   U503 TPS2596 High-mode current limit, 489.7 mA maximum (c17).
#                Default mode is limited to 222.6 mA.
#   VPOS/VNEG    LM27762 rated output, 250 mA per rail (the converter's own
#                limit); quiescent load 36.2 / 35.3 mA (analog r2_power F-1).
#                The rails are +/-3.85 V nominal (R501/R502 set point), not +/-15 V.
#   N4_V*_IV     OPA2210 I/V stage through D411/D412: 17.4 / 14.8 mA.
#   3V3D         c03 inventory: CPLD 40, DAC DVDD via U303 60 [PH], DVCC 14.2,
#                X201 8.2, two NDK 30, U205 4.7, U206 2.9, U607 3.4, U208 2.5 mA.
#   3V3M         MCU 80 mA planning value + 3 mA housekeeping.
#   3V3A         AVCC_L+R 16, VCCA 2.9, VREF 0.17, protection 1.8 mA.
#   1V3          ES9018K2M DVDD, 60 mA planning value (ESS nominal 50 mA at 80 MHz).
# ``transient_a`` is the current step the PDN gate (G40) sizes its target
# impedance with.  Digital loads take their full budget as a step (worst
# case).  The analogue rails carry no master-clock-rate current, so their step
# is the load the rail actually switches: the LM27762 input pulses at its rated
# 0.25 A output on 5V_ANA/5V_ANA_F (2 % ripple: the converter post-regulates
# with its own LDOs), the op-amp quiescent current on VPOS/VNEG, and the
# downstream 3.3 V steps on VBUS (3V3M + 3V3D) and 5V_SYS (3V3D).
# ``source`` lists the parts that drive the rail; their pins are not loads.
# ``loads`` (A) puts each major load's maximum at its own pads, so G10/G11 can
# solve the current every track and via actually carries; any other non-
# capacitor part on the rail draws ``minor_load_a`` (default 1 mA).  The
# loads add up to the rail budget (VPOS/VNEG: two OPA1622 at full output
# within the LM27762's 250 mA, plus the OPA2210 feed through D411/D412; the
# protection comparators and dividers total <= 2.74 mA, R10 F-1).
# N5_*: LM27762 flying-capacitor RMS current, sqrt(2) x 0.25 A (assumed).
RAILS = {
    "VBUS":      {"volts": 5.0,   "current_a": 0.77, "transient_a": 0.26, "kind": "digital", "assumed": False, "source": ("J101",),
                  "loads": {"U102": 0.69, "U502": 0.09}},
    "VBUS_SENSE": {"volts": 5.0,  "current_a": 0.001, "kind": "analog", "assumed": False, "supply": False},  # ADC divider
    "5V_SYS":    {"volts": 5.0,   "current_a": 0.69, "transient_a": 0.17, "kind": "digital", "assumed": False, "source": ("U102",),
                  "loads": {"U503": 0.49, "U504": 0.17, "U302": 0.025, "K601": 0.0066, "K603": 0.0066}},
    "5V_ANA":    {"volts": 5.0,   "current_a": 0.49, "transient_a": 0.25, "kind": "default", "assumed": False, "source": ("U503",),
                  "loads": {"FB501": 0.49}},
    "5V_ANA_F":  {"volts": 5.0,   "current_a": 0.49, "transient_a": 0.25, "kind": "default", "assumed": False, "source": ("FB501",),
                  "loads": {"U501": 0.49}},
    "VPOS":      {"volts": 3.85,  "current_a": 0.25, "transient_a": 0.036, "kind": "analog", "assumed": False, "source": ("U501",),
                  "loads": {"U401": 0.115, "U402": 0.115, "D411": 0.0174}, "minor_load_a": 0.0005},
    "VNEG":      {"volts": -3.85, "current_a": 0.25, "transient_a": 0.035, "kind": "analog", "assumed": False, "source": ("U501",),
                  "loads": {"U401": 0.115, "U402": 0.115, "D412": 0.0148}, "minor_load_a": 0.0005},
    "N4_VPOS_IV": {"volts": 3.5,  "current_a": 0.02, "kind": "analog", "assumed": False, "source": ("D411",)},
    "N4_VNEG_IV": {"volts": -3.5, "current_a": 0.02, "kind": "analog", "assumed": False, "source": ("D412",)},
    "3V3D":      {"volts": 3.3,   "current_a": 0.17, "kind": "digital", "assumed": False, "source": ("U504",)},
    "3V3A":      {"volts": 3.3,   "current_a": 0.025, "kind": "analog", "assumed": False, "source": ("U302",)},
    "3V3M":      {"volts": 3.3,   "current_a": 0.09, "kind": "digital", "assumed": False, "source": ("U502",)},
    "N2_V33_CPLD": {"volts": 3.3, "current_a": 0.04, "kind": "digital", "assumed": False},
    "N2_J201_3V3": {"volts": 3.3, "current_a": 0.05, "kind": "digital", "assumed": True, "supply": False},  # debug-header tap via DNF R241
    "1V3":       {"volts": 1.3,   "current_a": 0.06, "kind": "analog", "assumed": False, "source": ("U303",)},
    "DVCC":      {"volts": 3.3,   "current_a": 0.015, "kind": "digital", "assumed": False},
    "VCCA":      {"volts": 3.3,   "current_a": 0.003, "kind": "analog", "assumed": False},
    "AVCC_L":    {"volts": 3.3,   "current_a": 0.008, "kind": "analog", "assumed": False},
    "AVCC_R":    {"volts": 3.3,   "current_a": 0.008, "kind": "analog", "assumed": False},
    "VREF":      {"volts": 3.3,   "current_a": 0.001, "kind": "analog", "assumed": False, "supply": False},  # OPA2210 + inputs
    "N5_CP":    {"volts": 5.0,   "current_a": 0.36, "kind": "switching", "assumed": True},
    "N5_C1P":   {"volts": 5.0,   "current_a": 0.36, "kind": "switching", "assumed": True},
    "N5_C1N":   {"volts": 5.0,   "current_a": 0.36, "kind": "switching", "assumed": True},
    "GND":       {"volts": 0.0,   "current_a": 1.00, "kind": "return", "assumed": False},
}

#: The highest voltage present anywhere, used for the clearance gate.
MAX_RAIL_VOLTS = 15.0
#: Worst-case potential difference between any two conductors.  The real
#: bound is the VBUS hard-short kick (<= 17.08 V with D102, c17) against VNEG
#: (-3.9 V), 21 V; 30 V is kept as margin.
MAX_CONDUCTOR_DELTA_V = 30.0


# ---------------------------------------------------------------------------
# Net role classification
# ---------------------------------------------------------------------------

CLOCK_NETS = {
    "MCLK", "BCLK", "LRCLK", "LRCLK_FB", "SDATA", "FAM_CLK",
    "N2_X201_OUT", "N2_X202_OUT", "N2_X203_OUT",
    "N2_HSE_IN", "N2_HSE_OUT",
    "N2_BCLK_SRC", "N2_LRCLK_SRC", "N2_SDATA_SRC",
    "N2_CAP_CK", "N2_CAP_SD", "N2_CAP_WS",
    "N2_CPY_CK", "N2_CPY_SD",
    "N6_MCK_BUF", "N6_MCK_CMP", "N6_MCK_IN", "N6_REFMCK",  # N6_MCK_RC is the detector's RC-integrated (DC) node
    "N7_MCLK_MON", "LINK_SCK", "N2_LINK_SCK_MCU", "N2_LINK_SCK_BUF",
    "SWCLK", "CPLD_JTCK",
}

#: Highest-rate clock on the board, used for the jitter and crosstalk budget.
#: A 22.5792 MHz master clock is the usual 44.1 kHz-family MCLK.
MCLK_HZ = 22.5792e6
AUDIO_FULL_SCALE_VRMS = 2.0
TARGET_DYNAMIC_RANGE_DB = 120.0

USB_PAIR = ("USB_DP", "USB_DN")

#: DAC current outputs into the I/V stage -- the most sensitive nodes present.
IV_INPUT_NETS = {"DACL", "DACLB", "DACR", "DACRB"}
#: I/V amplifier outputs.
IV_OUTPUT_NETS = {"N4_IVL_P", "N4_IVL_N", "N4_IVR_P", "N4_IVR_N"}
#: Balanced headphone output path, amplifier -> relay -> jack.
OUTPUT_PATH_NETS = {
    "LEG_LP", "LEG_LN", "LEG_RP", "LEG_RN",
    "JACK_LP", "JACK_LN", "JACK_RP", "JACK_RN",
    "N4_LP_OUT", "N4_LN_OUT", "N4_RP_OUT", "N4_RN_OUT",
}
#: The parts each output net carries headphone current between.  LEG_xx also
#: feeds the 330 k-1 M DC/over-range sense dividers (R900-R933, R624-R627);
#: those taps carry no load current, so they are not part of the series path.
#: JACK_LP/RP serve both jacks; each jack is its own load path.
OUTPUT_SERIES_TERMINALS = {
    "N4_LP_OUT": [("U401", "R417")], "N4_LN_OUT": [("U401", "R418")],
    "N4_RP_OUT": [("U402", "R419")], "N4_RN_OUT": [("U402", "R420")],
    "LEG_LP": [("R417", "K601")], "LEG_LN": [("R418", "K602")],
    "LEG_RP": [("R419", "K603")], "LEG_RN": [("R420", "K604")],
    "JACK_LP": [("K601", "J701"), ("K601", "J702")], "JACK_LN": [("K602", "J701")],
    "JACK_RP": [("K603", "J701"), ("K603", "J702")], "JACK_RN": [("K604", "J701")],
}
#: Headphone output channel pairing, for channel-matching checks.
OUTPUT_CHANNEL_PAIRS = [
    ("JACK_LP", "JACK_RP"),
    ("JACK_LN", "JACK_RN"),
    ("LEG_LP", "LEG_RP"),
    ("LEG_LN", "LEG_RN"),
]

#: Amplifier input / feedback nodes: high impedance, loop area matters.
FEEDBACK_NETS = {
    "N4_LP_INN", "N4_LP_INP", "N4_LN_INN", "N4_LN_INP",
    "N4_RP_INN", "N4_RP_INP", "N4_RN_INN", "N4_RN_INP",
    "N4_LP_TP", "N4_LP_TN", "N4_LN_TP", "N4_LN_TN",
    "N4_RP_TP", "N4_RP_TN", "N4_RN_TP", "N4_RN_TN",
}

ANALOG_AUDIO_NETS = IV_INPUT_NETS | IV_OUTPUT_NETS | OUTPUT_PATH_NETS | FEEDBACK_NETS

#: Connector pins exposed to the outside world, which need an ESD path.
EXTERNAL_PORT_NETS = {
    "USB_DP", "USB_DN", "VBUS", "CC1", "CC2", "N1_SHIELD",
    "JACK_LP", "JACK_LN", "JACK_RP", "JACK_RN",
}

#: The switching regulator / charge pump area -- keep-out reference.
SWITCHING_NETS = {"N5_CP", "N5_C1P", "N5_C1N", "N5_DVDT", "N5_DAMP"}

#: Part-number fragments that identify a dedicated ESD/TVS protection device.
#: Reference designators alone are not reliable: an ESD array is commonly
#: placed as ``U`` (USBLC6-2SC6, TPD2E2U06) rather than ``D``.
_ESD_PART_HINTS = (
    "USBLC", "TPD", "ESD", "PESD", "SP0503", "SP3012", "SRV05",
    "CDSOT", "SMAJ", "SMBJ", "SMF", "PSM712", "NUP", "RCLAMP",
    "TVS", "DVIULC", "ULC6",
)


def is_protection_device(ref: str, value: str = "") -> bool:
    """True when a part can clamp an ESD strike on an exposed port.

    Matching is primarily on the part number because the protection device on
    a USB port is usually an ``U``-prefixed array.  A bare diode (``D``) or a
    ferrite (``FB``/``L`` in series) is also accepted as a clamp/filter.
    """
    up = (value or "").upper().replace("-", "").replace(" ", "")
    if any(h.replace("-", "") in up for h in _ESD_PART_HINTS):
        return True
    pre = ref_prefix(ref)
    return pre in {"D", "TVS", "FB", "ZD"}

_DIGITAL_HINTS = (
    "I2C_", "USART_", "SWD", "SWCLK", "JT", "LINK_", "LED_", "NRST", "BOOT",
    "PROG", "_EN", "EN_", "IRQ", "RESET", "PERMIT", "FAULT", "OK_N", "LOCK",
)


def rail_for(net: str):
    return RAILS.get(net)


def is_power(net: str) -> bool:
    return net in RAILS


def is_clock(net: str) -> bool:
    return net in CLOCK_NETS


def is_analog_audio(net: str) -> bool:
    return net in ANALOG_AUDIO_NETS


def is_digital(net: str) -> bool:
    if net in CLOCK_NETS:
        return True
    if net in RAILS or net in ANALOG_AUDIO_NETS:
        return False
    return any(h in net for h in _DIGITAL_HINTS)


def net_role(net: str) -> str:
    if net == "GND":
        return "return"
    if net in RAILS:
        return "power"
    if net in USB_PAIR:
        return "usb"
    if net in CLOCK_NETS:
        return "clock"
    if net in ANALOG_AUDIO_NETS:
        return "analog_audio"
    if net in SWITCHING_NETS:
        return "switching"
    if is_digital(net):
        return "digital"
    return "signal"


def net_voltage(net: str) -> float:
    """Nominal potential of a net relative to GND, for the clearance gate."""
    rail = RAILS.get(net)
    if rail:
        return rail["volts"]
    role = net_role(net)
    if role in ("clock", "digital"):
        return 3.3
    if role == "usb":
        return 3.3
    if role in ("analog_audio",):
        # Balanced legs swing on the +/-15 V rails.
        return 15.0
    if role == "switching":
        return 5.0
    return 5.0


# ---------------------------------------------------------------------------
# Reference designator families
# ---------------------------------------------------------------------------

_REF_RE = re.compile(r"^([A-Za-z_]+)(\d+)$")


def ref_prefix(ref: str) -> str:
    m = _REF_RE.match(ref or "")
    return m.group(1).upper() if m else (ref or "").upper()


def is_capacitor(ref: str) -> bool:
    return ref_prefix(ref) == "C"


def is_resistor(ref: str) -> bool:
    return ref_prefix(ref) == "R"


def is_ic(ref: str) -> bool:
    return ref_prefix(ref) in ("U", "IC")


# ---------------------------------------------------------------------------
# Capacitor value parsing (from the footprint Value field)
# ---------------------------------------------------------------------------

_VALUE_RE = re.compile(
    r"^\s*([0-9]*\.?[0-9]+)\s*(p|n|u|µ|μ|m)?\s*F?\s*$", re.IGNORECASE
)
_MULT = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6, "m": 1e-3}


def parse_capacitance(value: str):
    """Parse '100 nF', '4.7uF', '1.8 nF' -> farads.  None if not a capacitance."""
    if not value:
        return None
    m = _VALUE_RE.match(value.strip())
    if not m:
        return None
    num, suffix = m.group(1), (m.group(2) or "").lower()
    try:
        base = float(num)
    except ValueError:
        return None
    if not suffix:
        return None
    return base * _MULT.get(suffix, 1.0)


_RES_RE = re.compile(
    r"^\s*([0-9]*\.?[0-9]+)\s*(m|k|K|M|R)?\s*(?:ohm|Ohm|OHM|R|Ω)?\s*$"
)
_RES_MULT = {"m": 1e-3, "R": 1.0, "k": 1e3, "K": 1e3, "M": 1e6}


def parse_resistance(value: str):
    if not value:
        return None
    v = value.strip().replace("Ω", "").replace("ohm", "").replace("Ohm", "")
    m = _RES_RE.match(v)
    if not m:
        return None
    try:
        base = float(m.group(1))
    except ValueError:
        return None
    return base * _RES_MULT.get(m.group(2) or "R", 1.0)
