"""Externally sourced acceptance criteria for the DAC_HPA sign-off gates.

Every threshold in this module is traceable to a published standard, a
fabricator capability sheet or a device-vendor application note.  Nothing here
is derived from the project's own audit scripts -- this file is the independent
reference the gates are measured against.

Sources
-------
IPC-2221B Table 6-1   Electrical conductor spacing vs peak voltage.
IPC-2221B eq. 6-4     I = k * dT^0.44 * A^0.725 (A in mil^2), k = 0.048
                      external / 0.024 internal.
IPC-2152              Supersedes the 2221 charts; less conservative because it
                      models heat spreading, so 2221 is used as the floor.
IPC-6012 Class 2/3    Plated-hole annular ring and aspect-ratio limits.
IPC-7351B             Courtyard excess (Most/Nominal/Least) for SMD land
                      patterns.
JLCPCB capability     https://jlcpcb.com/capabilities/pcb-capabilities and
                      https://jlcpcb.com/impedance (captured 2026-10).
USB 2.0 / USB-IF      High-Speed D+/D- 90 ohm +/-15% differential; intra-pair
                      skew budget ~150 mil (~3.8 mm, ~22 ps on microstrip).
C. R. Paul,           "Inductance: Loop and Partial", Wiley 2010, ch. 5 --
                      via-pair loop inductance L = (mu0*h/pi)*acosh(s/d).
Hammerstad & Jensen   Microstrip characteristic impedance closed form.
CISPR 32 / FCC 15B    Radiated emission limits, class B, 3 m.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

MU0 = 4e-7 * 3.141592653589793           # H/m
EPS0 = 8.8541878128e-12                  # F/m
C0 = 299_792_458.0                       # m/s
RHO_CU_20C = 1.724e-8                    # ohm*m, annealed copper
CU_TEMPCO = 0.00393                      # 1/K
OZ_TO_MM = 0.0347222                     # 1 oz/ft^2 finished copper, mm


# ---------------------------------------------------------------------------
# IPC-2221B Table 6-1 -- electrical clearance (mm) vs peak volts between
# the two conductors.  B1 = internal, B2 = external uncoated,
# B4 = external with permanent polymer coating (soldermask).
# ---------------------------------------------------------------------------

IPC2221_CLEARANCE_MM = [
    # (max_peak_volts, B1_internal, B2_external_uncoated, B4_external_coated)
    (15,   0.05, 0.10, 0.05),
    (30,   0.05, 0.10, 0.05),
    (50,   0.10, 0.60, 0.13),
    (100,  0.10, 0.60, 0.13),
    (150,  0.20, 0.60, 0.40),
    (170,  0.20, 1.25, 0.40),
    (250,  0.20, 1.25, 0.40),
    (300,  0.20, 1.25, 0.40),
    (500,  0.25, 2.50, 0.80),
]
IPC2221_ABOVE_500_MM_PER_V = (0.0025, 0.005, 0.00305)


def ipc2221_clearance_mm(peak_volts: float, internal: bool, coated: bool = True) -> float:
    """Minimum electrical clearance for a conductor pair, IPC-2221B Table 6-1."""
    v = abs(peak_volts)
    col = 1 if internal else (3 if coated else 2)
    for vmax, *cols in IPC2221_CLEARANCE_MM:
        if v <= vmax:
            return cols[col - 1]
    base = IPC2221_CLEARANCE_MM[-1][col]
    per_v = IPC2221_ABOVE_500_MM_PER_V[col - 1]
    return base + (v - 500.0) * per_v


# ---------------------------------------------------------------------------
# IPC-2221B current capacity
# ---------------------------------------------------------------------------

IPC2221_K_EXTERNAL = 0.048
IPC2221_K_INTERNAL = 0.024
IPC2221_EXP_DT = 0.44
IPC2221_EXP_AREA = 0.725

#: Temperature rise the gate designs to.  10 K is the conservative end of the
#: 10-20 K band normally used for signal/analogue boards.
DESIGN_DELTA_T_K = 10.0

#: JLCPCB multilayer: 1 oz outer, 0.5 oz inner is the default build.  The
#: project has not pinned a stackup, so the gate assumes the JLC default and
#: reports that assumption.
OUTER_CU_OZ = 1.0
INNER_CU_OZ = 0.5

#: JLCPCB states 18 um average plated-barrel copper in through holes.
VIA_BARREL_PLATING_MM = 0.018


def ipc2221_current_a(width_mm: float, cu_thickness_mm: float, *, internal: bool,
                      delta_t_k: float = DESIGN_DELTA_T_K) -> float:
    """Ampacity of a rectangular conductor, IPC-2221B eq. 6-4."""
    area_mil2 = (width_mm / 0.0254) * (cu_thickness_mm / 0.0254)
    k = IPC2221_K_INTERNAL if internal else IPC2221_K_EXTERNAL
    return k * (delta_t_k ** IPC2221_EXP_DT) * (area_mil2 ** IPC2221_EXP_AREA)


def ipc2221_width_mm(current_a: float, cu_thickness_mm: float, *, internal: bool,
                     delta_t_k: float = DESIGN_DELTA_T_K) -> float:
    """Minimum conductor width for a current, IPC-2221B eq. 6-4 inverted."""
    k = IPC2221_K_INTERNAL if internal else IPC2221_K_EXTERNAL
    area_mil2 = (current_a / (k * delta_t_k ** IPC2221_EXP_DT)) ** (1.0 / IPC2221_EXP_AREA)
    return area_mil2 * 0.0254 * 0.0254 / cu_thickness_mm


def via_current_a(drill_mm: float, *, plating_mm: float = VIA_BARREL_PLATING_MM,
                  delta_t_k: float = DESIGN_DELTA_T_K) -> float:
    """Ampacity of a plated barrel, treating the unrolled barrel as a conductor.

    The barrel is unrolled into an equivalent strip of width pi*d and thickness
    equal to the plating, then evaluated with the IPC-2221B *internal* constant
    because a barrel is enclosed by laminate and cools poorly.
    """
    width_mm = 3.141592653589793 * drill_mm
    return ipc2221_current_a(width_mm, plating_mm, internal=True, delta_t_k=delta_t_k)


# ---------------------------------------------------------------------------
# JLCPCB capability -- multilayer (4-32 layer) process, 1 oz outer / 0.5 oz
# inner, green mask.  Values captured from jlcpcb.com, 2026-10.
# ---------------------------------------------------------------------------

JLC = {
    "min_track_mm": 0.09,
    "min_clearance_mm": 0.09,
    "preferred_track_mm": 0.127,
    "min_via_drill_mm": 0.15,
    "preferred_via_drill_mm": 0.20,
    "min_via_diameter_mm": 0.25,
    "via_diameter_over_drill_mm": 0.10,
    "surcharge_free_via_pad_mm": 0.45,
    "min_pth_annular_mm": 0.18,
    "preferred_pth_annular_mm": 0.25,
    "min_npth_mm": 0.50,
    "via_hole_to_hole_mm": 0.20,
    "pad_hole_to_hole_mm": 0.45,
    "pth_hole_to_track_min_mm": 0.28,
    "pth_hole_to_track_preferred_mm": 0.35,
    "via_hole_to_track_mm": 0.20,
    "copper_to_edge_routed_mm": 0.20,
    "mask_bridge_green_mm": 0.10,
    "silk_line_mm": 0.15,
    "silk_text_height_mm": 1.00,
    "silk_to_pad_mm": 0.15,
    "min_smd_pad_mm": 0.25,
    "smd_pad_to_pad_diff_net_mm": 0.15,
    "blind_buried_supported": False,
    "via_in_pad_diameter_range_mm": (0.15, 0.55),
    "plugged_via_max_diameter_mm": 0.50,
    "board_thickness_tolerance_pct": 10.0,
    "track_width_tolerance_pct": 20.0,
    "impedance_tolerance_pct": 10.0,
    "prepreg_er": {"7628": 4.4, "3313": 4.1, "1080": 3.91, "2116": 4.16},
    "core_er": 4.6,
    "soldermask_er": 3.8,
    "soldermask_over_trace_mm": 0.0152,   # 0.6 mil
    "soldermask_over_substrate_mm": 0.0305,  # 1.2 mil
}

#: IPC-6012 plated through hole aspect ratio (board thickness : drill).
ASPECT_RATIO_WARN = 8.0
ASPECT_RATIO_FAIL = 10.0

#: IPC-6012 minimum annular ring.  Class 2 allows 90 deg breakout; class 3
#: requires a continuous ring of at least 0.025 mm (internal) / 0.05 mm.
IPC6012_CLASS2_ANNULAR_MM = 0.05
IPC6012_CLASS3_ANNULAR_MM = 0.025


# ---------------------------------------------------------------------------
# USB 2.0 High-Speed
# ---------------------------------------------------------------------------

USB_HS = {
    "z_diff_ohm": 90.0,
    "z_diff_tol_pct": 15.0,
    "z_se_ohm": 45.0,
    "z_se_tol_pct": 10.0,
    "intra_pair_skew_mm": 3.81,      # ~150 mil, ~22 ps on microstrip
    "max_trace_mm": 150.0,
    "max_stub_mm": 2.0,
    "min_spacing_to_other_signals_w": 3.0,
    "max_vias_per_leg": 2,
}


# ---------------------------------------------------------------------------
# Mixed-signal / audio layout criteria
# ---------------------------------------------------------------------------

AUDIO = {
    # I/V and any inverting summing node: the feedback loop is an antenna and
    # the inverting input is the highest-impedance node on the board.
    "iv_feedback_loop_area_max_mm2": 25.0,
    "iv_feedback_trace_max_mm": 15.0,
    "summing_node_max_trace_mm": 10.0,

    # Decoupling: distance from the device power pin to the HF bypass cap.
    "hf_bypass_max_pad_distance_mm": 3.0,
    "bulk_bypass_max_pad_distance_mm": 10.0,
    "hf_bypass_max_mount_inductance_nh": 2.5,

    # Return path.
    "max_stitch_via_distance_mm": 2.0,
    "critical_net_max_via_count": 4,

    # Crosstalk: 3W centre-to-centre is the classic screen; for a 120 dB
    # dynamic-range target the gate also applies an absolute floor.
    "digital_to_analog_min_gap_mm": 0.75,
    "clock_to_analog_min_gap_mm": 1.00,
    "w_rule_multiplier": 3.0,

    # Headphone output: series resistance budget.  Damping factor = Zload/Zout;
    # for a 32 ohm load a DF of 100 needs the whole source side under 0.32 ohm,
    # of which the PCB should consume a small fraction.
    "headphone_load_ohm": 32.0,
    "min_damping_factor": 100.0,
    "max_output_trace_resistance_ohm": 0.10,
    "max_channel_resistance_mismatch_ohm": 0.02,

    # ESD: IEC 61000-4-2 contact discharge is ~30 A in ~1 ns, so every nH of
    # stub inductance shows up as ~30 V of let-through.
    "esd_max_stub_mm": 10.0,
    "esd_di_dt_a_per_s": 30.0 / 1e-9,
    "esd_max_let_through_v": 500.0,
}


def jitter_snr_db(jitter_s: float, signal_hz: float) -> float:
    """Jitter-limited SNR, SNR = 20*log10(1/(2*pi*f*tj))."""
    import math
    return 20.0 * math.log10(1.0 / (2.0 * math.pi * signal_hz * jitter_s))


# ---------------------------------------------------------------------------
# Power integrity
# ---------------------------------------------------------------------------

#: Maximum DC drop permitted on a rail, as a fraction of its nominal voltage.
#: Analogue rails are held tighter than digital because op-amp PSRR falls with
#: frequency and the drop is a static error term.
IR_DROP_BUDGET_PCT = {
    "analog": 1.0,
    "digital": 3.0,
    "default": 2.0,
}

#: PDN target impedance, Ztarget = Vdd * ripple_fraction / I_transient.
PDN_RIPPLE_FRACTION = {"analog": 0.01, "digital": 0.05, "default": 0.02}

#: Signal-layer to nearest-plane dielectric height, in mm.
#:
#: The board declares no stackup, so this cannot be read from the design.  A
#: 6-layer 1.6 mm build places the first plane one prepreg below the outer
#: layer, which for the common 3313/7628 constructions lands between roughly
#: 0.09 mm and 0.20 mm.  Gates that depend on this value sweep the whole range
#: instead of picking a point, so the conclusion is reported together with its
#: sensitivity rather than resting on a guess.
OUTER_TO_PLANE_MM = {"min": 0.09, "typical": 0.12, "max": 0.20}

#: PDN control band.  The lower edge is set by the regulator's loop bandwidth
#: (below it the regulator, not the capacitors, controls the impedance) and the
#: upper edge by the fastest edge rate on the board.
PDN_BAND_HZ = {"low": 1e5, "high": 1e8}


def pdn_target_impedance_ohm(vdd: float, transient_a: float, kind: str = "default") -> float:
    return vdd * PDN_RIPPLE_FRACTION.get(kind, PDN_RIPPLE_FRACTION["default"]) / max(transient_a, 1e-9)


def via_pair_inductance_h(pitch_mm: float, drill_mm: float, length_mm: float) -> float:
    """Loop inductance of a via pair, C. R. Paul, Inductance ch. 5.

    L = (mu0 * h / pi) * acosh(s / d)
    """
    import math
    s = pitch_mm * 1e-3
    d = drill_mm * 1e-3
    h = length_mm * 1e-3
    ratio = max(s / d, 1.0000001)
    return (MU0 * h / math.pi) * math.acosh(ratio)


def trace_inductance_h(length_mm: float, width_mm: float, height_mm: float) -> float:
    """Partial self-inductance of a microstrip run above a plane.

    Uses the standard L = (mu0*h_diel/w) * l transmission-line result, which is
    the loop inductance per unit length of a wide microstrip over its plane.
    """
    return MU0 * (height_mm * 1e-3) / (width_mm * 1e-3) * (length_mm * 1e-3)


# ---------------------------------------------------------------------------
# Transmission line models
# ---------------------------------------------------------------------------

def microstrip_z0(w_mm: float, h_mm: float, t_mm: float, er: float) -> float:
    """Hammerstad & Jensen microstrip Z0 with thickness correction."""
    import math
    w, h, t = w_mm, h_mm, t_mm
    if t > 0:
        # Effective width correction for finite conductor thickness.
        if w / h >= 1.0 / (2.0 * math.pi):
            dw = (t / math.pi) * (1.0 + math.log(2.0 * h / t))
        else:
            dw = (t / math.pi) * (1.0 + math.log(4.0 * math.pi * w / t))
        w = w + dw
    u = w / h
    # Hammerstad & Jensen effective permittivity.
    a = 1.0 + (1.0 / 49.0) * math.log((u ** 4 + (u / 52.0) ** 2) / (u ** 4 + 0.432)) \
        + (1.0 / 18.7) * math.log(1.0 + (u / 18.1) ** 3)
    b = 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053
    e_eff = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 10.0 / u) ** (-a * b)
    # Characteristic impedance of the equivalent air line.
    fu = 6.0 + (2.0 * math.pi - 6.0) * math.exp(-((30.666 / u) ** 0.7528))
    z01 = 59.95238 * math.log(fu / u + math.sqrt(1.0 + (2.0 / u) ** 2)) * 2.0
    return z01 / math.sqrt(e_eff)


def microstrip_eeff(w_mm: float, h_mm: float, er: float) -> float:
    import math
    u = w_mm / h_mm
    a = 1.0 + (1.0 / 49.0) * math.log((u ** 4 + (u / 52.0) ** 2) / (u ** 4 + 0.432)) \
        + (1.0 / 18.7) * math.log(1.0 + (u / 18.1) ** 3)
    b = 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053
    return (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 10.0 / u) ** (-a * b)


def edge_coupled_microstrip_zdiff(w_mm: float, s_mm: float, h_mm: float,
                                  t_mm: float, er: float) -> float:
    """Differential impedance of an edge-coupled microstrip pair.

    IPC-2141A eq. for coupled microstrip:
        Zdiff = 2 * Z0 * (1 - 0.48 * exp(-0.96 * s/h))
    Accurate to a few percent for 0.1 <= s/h <= 3, which covers every practical
    USB pair on a 4-6 layer FR-4 stackup.
    """
    import math
    z0 = microstrip_z0(w_mm, h_mm, t_mm, er)
    return 2.0 * z0 * (1.0 - 0.48 * math.exp(-0.96 * s_mm / h_mm))


def propagation_delay_ps_per_mm(e_eff: float) -> float:
    import math
    return (math.sqrt(e_eff) / C0) * 1e12 / 1e3


# ---------------------------------------------------------------------------
# EMC -- CISPR 32 / EN 55032 class B radiated limits, quasi-peak, 3 m
# ---------------------------------------------------------------------------

CISPR32_CLASS_B_3M = [
    # (f_low_hz, f_high_hz, limit_dBuV_per_m)
    (30e6, 230e6, 40.0),
    (230e6, 1000e6, 47.0),
]


def cispr32_class_b_limit_dbuvm(freq_hz: float) -> float | None:
    for lo, hi, lim in CISPR32_CLASS_B_3M:
        if lo <= freq_hz < hi:
            return lim
    return None


def differential_mode_e_field_dbuvm(area_mm2: float, current_a: float,
                                    freq_hz: float, distance_m: float = 3.0) -> float:
    """Radiation from a small current loop (far field, free space).

    E [V/m] = 1.316e-14 * f^2 * A * I / r    (f in Hz, A in m^2, I in A, r in m)
    This is the standard differential-mode radiation estimate used in EMC
    pre-compliance work (Ott, "Electromagnetic Compatibility Engineering").
    """
    import math
    area_m2 = area_mm2 * 1e-6
    e_v_per_m = 1.316e-14 * (freq_hz ** 2) * area_m2 * current_a / distance_m
    if e_v_per_m <= 0:
        return -999.0
    return 20.0 * math.log10(e_v_per_m / 1e-6)


# ---------------------------------------------------------------------------
# IPC-7351B courtyard excess by package family (mm, nominal density level B)
# ---------------------------------------------------------------------------

IPC7351_COURTYARD_EXCESS_MM = {
    "chip": 0.25,
    "gullwing": 0.25,
    "nolead": 0.20,
    "bga": 1.00,
    "default": 0.25,
}

#: Two courtyards may touch but must not overlap (IPC-7351B 3.2).
COURTYARD_OVERLAP_TOLERANCE_MM2 = 0.01
