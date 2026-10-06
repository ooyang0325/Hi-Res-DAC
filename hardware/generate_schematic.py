#!/usr/bin/env python3
"""Capture the DAC-HPA workbook plus an asserted functional ECO in KiCad.

Parts List v0.9 and Calculation Package v1.1 remain immutable baselines. The
explicit overlay below corrects the LED pads, buffers U605's MCU readbacks,
and adds local J702 ESD devices. U403/U404 retain the owner-approved DGK
package substitution and swap their equivalent A/B I/V channels for the
reviewed physical macro. Physical and firmware qualification gates remain open.
"""

from __future__ import annotations

import json
import math
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

from openpyxl import load_workbook


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORKBOOK = ROOT / "doc" / "DAC_HPA_Parts_List_v0.9.xlsx"
PROJECT = "DAC_HPA"
GRID = 1.27
ROOT_UUID = "0c6c0976-e401-5c8a-8977-bc60da031e5e"


def uid(*parts: object) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "hi-res-dac/" + "/".join(map(str, parts))))


def q(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def f(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"


def mm(units: int | float) -> str:
    return f(float(units) * GRID)


def natural(ref: str) -> tuple[str, int, str]:
    match = re.fullmatch(r"([A-Za-z]+)(\d+)(.*)", ref)
    if match:
        return match.group(1), int(match.group(2)), match.group(3)
    return ref, 0, ""


@dataclass(frozen=True)
class Pin:
    number: str
    name: str
    net: str


@dataclass
class Part:
    row: int
    block: int
    refs: list[str]
    value: str
    mpn: str
    package: str
    rating_tolerance: str
    lcsc: str
    fit: str
    source: str
    datasheet: str
    description: str
    notes: str

    @property
    def symbol_id(self) -> str:
        return f"P{self.row:03d}"


def read_source() -> tuple[dict[str, Part], dict[str, list[Pin]], dict[str, Part]]:
    wb = load_workbook(WORKBOOK, read_only=True, data_only=True)
    net_pins: dict[str, list[Pin]] = defaultdict(list)
    for row in list(wb["Netlist"].values)[3:]:
        if row[0] is not None:
            net_pins[str(row[0])].append(Pin(str(row[1]), str(row[2]), str(row[3])))

    parts: dict[str, Part] = {}
    libparts: dict[str, Part] = {}
    for number, row in enumerate(list(wb["Parts list"].values)[3:], start=4):
        if row[1] is None or str(row[12]) == "Board":
            continue
        refs = [ref for ref in str(row[25] or "").split(",") if ref]
        if not refs:
            continue
        block = int(str(row[0]).split(" ", 1)[0])
        part = Part(
            row=number,
            block=block,
            refs=refs,
            value=str(row[4] or ""),
            mpn=str(row[7] or ""),
            package=str(row[5] or ""),
            rating_tolerance=str(row[6] or ""),
            lcsc=str(row[8] or ""),
            fit=str(row[12] or ""),
            source=str(row[10] or ""),
            datasheet=str(row[23] or ""),
            description=str(row[3] or ""),
            notes=str(row[24] or ""),
        )
        if set(refs) == {"U403", "U404"}:
            if (part.value, part.mpn, part.package, part.lcsc) != (
                "OPA2210IDR", "TI OPA2210IDR", "SOIC-8", "C1849415"
            ):
                raise ValueError("U403/U404 source MPN changed; review the approved DGK override")
            part.value = "OPA2210IDGKR"
            part.mpn = "TI OPA2210IDGKR"
            part.package = "VSSOP-8 (DGK)"
            part.lcsc = "C2876414"
            part.source = "JLCPCB Extended SMT (pre-order)"
            part.notes = (
                "Owner-approved 27 Sep 2026 package substitution; "
                "provisional DAC-to-I/V routed limit 7 mm, subject to extraction "
                "and I/V step-response bring-up. JLC extended part C2876414; "
                "quantity and sourcing must be confirmed before order."
            )
        if set(refs) == {"R417", "R418", "R419", "R420"}:
            if (part.value, part.mpn, part.package, part.lcsc,
                    part.rating_tolerance, part.fit) != (
                "0 Ω", "UNI-ROYAL 0402WGF0000TCE", "0402", "C17168",
                "jumper, ≤ 50 mΩ", "Yes"
            ):
                raise ValueError("Output-link source changed; review the low-DCR jumper ECO")
            # This is a same-value, same-size review candidate. The v0.9
            # workbook remains the immutable source baseline; R107 stays on
            # its own original BOM row. Yageo specifies <=1 mOhm for the
            # PA0402 07 jumper, but stock and assembly need an order check.
            part.mpn = "YAGEO PA0402-R-070RL"
            part.lcsc = "C4044221"
            part.rating_tolerance = "jumper, ≤ 1 mΩ (manufacturer maximum)"
            part.source = "JLCPCB Extended SMT; stock must be rechecked at order"
            part.datasheet = "https://www.yageogroup.com/content/Resource%20Library/Datasheet/PYU-PA_JUMPER_L_51_ROHS.pdf"
            part.notes = (
                "Review-only output-link BOM ECO, 28 Sep 2026: same nominal "
                "0 Ω and 0402 land; Yageo PA0402 07 maximum resistance "
                "1 mΩ versus the source workbook's 50 mΩ link assumption. "
                "Retain removable design-for-test links R417–R420. "
                "JLC C4044221 availability, footprint, assembly and R-15 "
                "measurement require order-stage confirmation."
            )
        libparts[part.symbol_id] = part
        for ref in refs:
            if ref in parts:
                raise ValueError(f"Repeated designator {ref} in Parts list")
            parts[ref] = part

    if set(parts) != set(net_pins):
        raise ValueError(
            f"Parts/netlist designator mismatch: parts-only={sorted(set(parts)-set(net_pins))}, "
            f"netlist-only={sorted(set(net_pins)-set(parts))}"
        )
    for part in libparts.values():
        signatures = {
            tuple((pin.number, pin.name) for pin in net_pins[ref]) for ref in part.refs
        }
        if len(signatures) != 1:
            raise ValueError(f"Different pin maps within Parts list row {part.row}")
    return parts, net_pins, libparts


def apply_approved_overrides(workbook_pins: dict[str, list[Pin]]) -> dict[str, list[Pin]]:
    """Apply owner-approved physical corrections without editing versioned docs.

    On 26 September 2026 the owner approved correcting D705/D706 to the
    manufacturer/JLC pin maps. Parts List v0.9 now carries the owner-approved
    J701 map and the HRO drawing's J702 map directly. Assert all three source
    signatures so a later workbook revision cannot silently change them.
    """
    corrected = {ref: list(items) for ref, items in workbook_pins.items()}
    for ref, drive in (("D705", "N7_LEDG_A"), ("D706", "N7_LEDR_A")):
        current = {(pin.number, pin.name, pin.net) for pin in corrected[ref]}
        expected = {("1", "K", "GND"), ("2", "A", drive)}
        if current != expected:
            raise ValueError(f"{ref} workbook pin map changed; re-review the approved LED override: {current}")
        corrected[ref] = [Pin("1", "A", drive), Pin("2", "K", "GND")]
    expected_connectors = {
        "J701": {
            ("1", "GND", "GND"),
            ("2", "R−", "JACK_RN"), ("3", "R−", "JACK_RN"),
            ("4", "R+", "JACK_RP"), ("5", "R+", "JACK_RP"),
            ("6", "L−", "JACK_LN"),
            ("7", "L+", "JACK_LP"), ("8", "L+", "JACK_LP"),
            ("9", "SWITCH", "NC"), ("10", "DETECT", "NC"),
            ("11", "EP", "NC"), ("12", "EP", "NC"),
        },
        "J702": {
            ("1", "Sleeve", "GND"), ("2", "Ring 2", "GND"),
            ("3", "Ring 1 (R+)", "JACK_RP"),
            ("4", "Tip (L+)", "JACK_LP"),
            ("5", "Ring-1 break contact", "NC"),
            ("6", "Tip break contact", "NC"),
        },
    }
    for ref, expected in expected_connectors.items():
        actual = {(pin.number, pin.name, pin.net) for pin in corrected[ref]}
        if actual != expected:
            raise ValueError(f"{ref} workbook pin map changed; review maker drawing: {actual ^ expected}")
    return corrected


def apply_functional_eco(
    base_parts: dict[str, Part], approved_pins: dict[str, list[Pin]],
    base_libparts: dict[str, Part],
) -> tuple[dict[str, Part], dict[str, list[Pin]], dict[str, Part]]:
    """Add reviewed F02/F04 and I/V channel ECOs without changing the workbook.

    Every affected source part, pin and net is asserted before it is overlaid.
    Synthetic symbol rows 9001–9005 never appear in Parts List v0.9.
    """
    parts = dict(base_parts)
    pins = {ref: list(items) for ref, items in approved_pins.items()}
    libparts = dict(base_libparts)
    if len(base_parts) != 526 or sum(map(len, approved_pins.values())) != 1445:
        raise ValueError("Parts List v0.9 inventory changed; re-review the functional ECO")
    new_nets = {
        "N6_V3AG_A_BUF_IN", "N6_V3AG_B_BUF_IN",
        "N6_V3AG_A_BUF_OUT", "N6_V3AG_B_BUF_OUT",
    }
    if new_nets & {pin.net for group in pins.values() for pin in group}:
        raise ValueError("Functional-ECO buffer net name already exists in the source")

    def require(ref: str, expected: tuple[tuple[str, str, str], ...], value: str = "") -> None:
        actual = tuple((pin.number, pin.name, pin.net) for pin in pins[ref])
        if actual != expected or (value and parts[ref].value != value):
            raise ValueError(f"{ref} v0.9 source changed; re-review functional ECO: {actual}")

    require("R688", (("1", "1", "N6_V3AG_A"), ("2", "2", "N6_V3AG_A_MCU")), "470 kΩ")
    require("R689", (("1", "1", "N6_V3AG_B"), ("2", "2", "N6_V3AG_B_MCU")), "470 kΩ")
    for ref, source, target in (
        ("R688", "N6_V3AG_A_MCU", "N6_V3AG_A_BUF_IN"),
        ("R689", "N6_V3AG_B_MCU", "N6_V3AG_B_BUF_IN"),
    ):
        pins[ref] = [Pin(pin.number, pin.name, target if pin.net == source else pin.net)
                     for pin in pins[ref]]
    for number, net in (("45", "N6_V3AG_A_MCU"), ("62", "N6_V3AG_B_MCU")):
        if {pin.number: pin.net for pin in pins["U201"]}.get(number) != net:
            raise ValueError(f"U201 pin {number} source net changed; re-review functional ECO")
    for ref, net in (("D701", "JACK_LP"), ("D702", "JACK_RP")):
        require(ref, (("1", "1", net), ("2", "2", "GND")), "5 V")
        if (parts[ref].mpn, parts[ref].lcsc, parts[ref].package) != (
            "GOODWORK LESD5D5.0CT1G", "C41399463", "SOD-523"
        ):
            raise ValueError(f"{ref} source TVS identity changed; re-review functional ECO")
    for number, net in (("3", "JACK_RP"), ("4", "JACK_LP"), ("5", "NC"), ("6", "NC")):
        if {pin.number: pin.net for pin in pins["J702"]}.get(number) != net:
            raise ValueError(f"J702 pin {number} source net changed; re-review functional ECO")

    # The DGK dual amplifiers have identical A and B channels. The rotated
    # I/V macro assigns the P legs to B and the N legs to A. Assert every
    # workbook pin, including TI's physical pin names, before changing only
    # the four input/output nets on each package.
    iv_source_and_eco = {
        "U403": (
            (("1", "OUT A", "N4_IVL_P"), ("2", "-IN A", "DACL"),
             ("3", "+IN A", "VREF"), ("4", "V-", "N4_VNEG_IV"),
             ("5", "+IN B", "VREF"), ("6", "-IN B", "DACLB"),
             ("7", "OUT B", "N4_IVL_N"), ("8", "V+", "N4_VPOS_IV")),
            {"1": "N4_IVL_N", "2": "DACLB", "6": "DACL", "7": "N4_IVL_P"},
        ),
        "U404": (
            (("1", "OUT A", "N4_IVR_P"), ("2", "-IN A", "DACR"),
             ("3", "+IN A", "VREF"), ("4", "V-", "N4_VNEG_IV"),
             ("5", "+IN B", "VREF"), ("6", "-IN B", "DACRB"),
             ("7", "OUT B", "N4_IVR_N"), ("8", "V+", "N4_VPOS_IV")),
            {"1": "N4_IVR_N", "2": "DACRB", "6": "DACR", "7": "N4_IVR_P"},
        ),
    }
    for ref, (source, swapped_nets) in iv_source_and_eco.items():
        require(ref, source, "OPA2210IDGKR")
        pins[ref] = [Pin(pin.number, pin.name, swapped_nets.get(pin.number, pin.net))
                     for pin in pins[ref]]

    def add(part: Part, pin_maps: dict[str, list[Pin]]) -> None:
        if part.symbol_id in libparts or set(part.refs) != set(pin_maps):
            raise ValueError(f"Functional-ECO symbol row/reference collision: {part.symbol_id}")
        signatures = {tuple((pin.number, pin.name) for pin in pin_maps[ref])
                      for ref in part.refs}
        if len(signatures) != 1:
            raise ValueError(f"Functional-ECO symbol {part.symbol_id} has inconsistent pin names")
        libparts[part.symbol_id] = part
        for ref in part.refs:
            if ref in parts or ref in pins:
                raise ValueError(f"Functional-ECO designator {ref} already exists")
            parts[ref] = part
            pins[ref] = pin_maps[ref]

    add(Part(
        row=9001, block=6, refs=["U621"], value="SN74AUP2G17DCKR",
        mpn="TI SN74AUP2G17DCKR", package="SC70-6 (DCK)",
        rating_tolerance="0.8–3.6 V; dual noninverting Schmitt buffer",
        lcsc="C507231", fit="Yes", source="JLCPCB C507231; order availability recheck",
        datasheet="https://www.ti.com/lit/ds/symlink/sn74aup2g17.pdf",
        description="Dual Schmitt buffer for 3V3A-good MCU readback isolation",
        notes="Functional ECO F02; exact JLC C507231 footprint/model imported; TI DCK G-3 overlay remains open",
    ), {"U621": [
        Pin("1", "1A", "N6_V3AG_A_BUF_IN"), Pin("2", "GND", "GND"),
        Pin("3", "2A", "N6_V3AG_B_BUF_IN"),
        Pin("4", "2Y", "N6_V3AG_B_BUF_OUT"),
        Pin("5", "VCC", "3V3M"), Pin("6", "1Y", "N6_V3AG_A_BUF_OUT"),
    ]})
    add(replace(base_parts["R951"], row=9002, block=6,
                refs=["R952", "R953"],
                notes="Functional ECO F02: 10 kΩ MCU-side output series resistor"), {
        "R952": [Pin("1", "1", "N6_V3AG_A_BUF_OUT"), Pin("2", "2", "N6_V3AG_A_MCU")],
        "R953": [Pin("1", "1", "N6_V3AG_B_BUF_OUT"), Pin("2", "2", "N6_V3AG_B_MCU")],
    })
    add(replace(base_parts["R680"], row=9003, block=6,
                refs=["R954", "R955"],
                notes="Functional ECO F02: MCU-side pull-up makes an open buffer output fault-high"), {
        "R954": [Pin("1", "1", "3V3M"), Pin("2", "2", "N6_V3AG_A_MCU")],
        "R955": [Pin("1", "1", "3V3M"), Pin("2", "2", "N6_V3AG_B_MCU")],
    })
    add(replace(base_parts["C628"], row=9004, block=6, refs=["C667"],
                notes="Functional ECO F02: 100 nF local bypass at U621 pin 5"), {
        "C667": [Pin("1", "1", "3V3M"), Pin("2", "2", "GND")],
    })
    add(replace(base_parts["D701"], row=9005, block=7,
                refs=["D707", "D708"],
                notes="Functional ECO F04: local J702 LP/RP TVS; verify nonlinear load, grounding and system ESD"), {
        "D707": [Pin("1", "1", "JACK_RP"), Pin("2", "2", "GND")],
        "D708": [Pin("1", "1", "JACK_LP"), Pin("2", "2", "GND")],
    })
    # Functional ECO F05: fit SMD programming headers on the J201 (MCU WCH-Link)
    # and J202 (CPLD) debug pad blocks. Pin order and nets are unchanged.
    for ref, lcsc, count in (("J201", "C2883805", 8), ("J202", "C2883802", 5)):
        source = parts[ref]
        if source.fit != "Pads" or len(pins[ref]) != count:
            raise ValueError(f"{ref} source pads changed; re-review header ECO F05")
        fitted = replace(
            source, value=f"X6511WVS-{count:02d}H-C60D48R1",
            mpn=f"XKB X6511WVS-{count:02d}H-C60D48R1",
            package=f"SMD 1x{count} P2.54 mm vertical, staggered legs",
            rating_tolerance="3 A, 250 V; 2.5 mm body, 6.0 mm mating pin",
            lcsc=lcsc, fit="Yes", source=f"JLCPCB {lcsc}; order availability recheck",
            datasheet=f"https://www.lcsc.com/datasheet/{lcsc}.pdf",
            notes=f"Functional ECO F05: fitted programming header on the {ref} debug pads")
        parts[ref] = fitted
        libparts[fitted.symbol_id] = fitted
    # Functional ECO F06 (v2): layout-driven AGRV2K I/O reassignment (RTL pin constraint
    # change only). The west row is walled by FAM_CLK and its L2-protection via keep-out,
    # so every reassignable signal moves to a side that can escape: the LINK bus, CPLD_IRQ
    # and OSC48_EN to the north row facing U208/U201, OSC44_EN to pin 8 (escapes south).
    cpld_moves = {"10": "27", "11": "26", "12": "28", "14": "29", "2": "31", "3": "8"}
    cpld = {pin.number: pin.net for pin in pins["U202"]}
    expected = {"10": "LINK_MOSI", "11": "LINK_FRAME", "12": "LINK_MISO", "14": "CPLD_IRQ",
                "2": "OSC48_EN", "3": "OSC44_EN",
                "26": "NC", "27": "NC", "28": "NC", "29": "NC", "31": "NC", "8": "NC"}
    if any(cpld.get(number) != net for number, net in expected.items()):
        raise ValueError("U202 source pins changed; re-review CPLD pin ECO F06")
    for old_pin, new_pin in cpld_moves.items():
        cpld[new_pin], cpld[old_pin] = cpld[old_pin], "NC"
    pins["U202"] = [Pin(pin.number, pin.name, cpld[pin.number]) for pin in pins["U202"]]
    # Functional ECO F07 (owner decision, 2 October): I2S capture copies. The three DAC-bound
    # N2_*_SRC lines leave pins 18-20 side by side as F.Cu-only 3W routes, so the 330 ohm
    # bit-perfect capture taps cannot branch at the CPLD end. The CPLD now drives dedicated
    # copies of BCLK and SDATA on spare pins 22/23 into R228/R230, which become source series
    # resistors; WS is captured from LRCLK_FB (pin 13), which the notes already define as a copy of
    # LRCLK from its own output register (R229 now taps it). The DAC lines carry no capture stubs.
    # RTL: duplicate the BCLK and SDATA output registers onto pins 22/23 (same edge as 18/20).
    copies = {"22": "N2_CPY_CK", "23": "N2_CPY_SD"}
    taps = {"R228": ("N2_BCLK_SRC", "N2_CPY_CK"), "R229": ("N2_LRCLK_SRC", "LRCLK_FB"),
            "R230": ("N2_SDATA_SRC", "N2_CPY_SD")}
    if set(copies.values()) & {pin.net for group in pins.values() for pin in group}:
        raise ValueError("ECO F07 copy net name already exists in the source")
    if (any(cpld.get(number) != "NC" for number in copies)
            or any({pin.number: pin.net for pin in pins[ref]}.get("1") != source
                   for ref, (source, _) in taps.items())):
        raise ValueError("U202/R228-R230 source changed; re-review I2S capture ECO F07")
    cpld.update(copies)
    pins["U202"] = [Pin(pin.number, pin.name, cpld[pin.number]) for pin in pins["U202"]]
    for ref, (_, copy) in taps.items():
        pins[ref] = [Pin(pin.number, pin.name, copy if pin.number == "1" else pin.net)
                     for pin in pins[ref]]
    # Functional ECO F08 (layout-driven CPLD pin rotation, 4 October): east-row IO pins 21-23
    # become N2_CPY_CK / N2_CPY_SD / MCLK_EN (top to bottom: 23 MCLK_EN). The two copies run
    # south-east to R228/R230 and MCLK_EN north-west, so MCLK_EN must take the top pin or it
    # crosses both copies at the pin row. RTL pin constraint change only.
    if (cpld.get("21"), cpld.get("22"), cpld.get("23")) != ("MCLK_EN", "N2_CPY_CK", "N2_CPY_SD"):
        raise ValueError("U202 pins 21-23 changed; re-review CPLD pin ECO F08")
    cpld["21"], cpld["22"], cpld["23"] = "N2_CPY_CK", "N2_CPY_SD", "MCLK_EN"
    pins["U202"] = [Pin(pin.number, pin.name, cpld[pin.number]) for pin in pins["U202"]]
    # Functional ECO F09 (layout-driven, 6 October): CPLD_IRQ moves from north-row pin 29 to west-row
    # pin 3. Pin 29 sits under LINK_MISO's escape via between pins 28 and 30, so no route can leave it;
    # pin 3 (the I/O that carried OSC44_EN before F06) escapes west. RTL pin constraint change only.
    if (cpld.get("29"), cpld.get("3")) != ("CPLD_IRQ", "NC"):
        raise ValueError("U202 pins 29/3 changed; re-review CPLD pin ECO F09")
    cpld["3"], cpld["29"] = "CPLD_IRQ", "NC"
    pins["U202"] = [Pin(pin.number, pin.name, cpld[pin.number]) for pin in pins["U202"]]
    # Functional ECO F10 (sign-off review, 7 October): ground-sense reference for the 3.5 mm output.
    # The difference-stage reference resistors R404/R408/R412/R416 return to the J702 sleeve through
    # N4_GSENSE instead of the local plane, so ground currents between the DAC area and the jack (USB
    # frame-rate digital current, SE load return, line-out ground loop) are rejected by the stage's
    # CMRR instead of adding 1:1 to the single-ended output. R448 (0 ohm) is the only GND join,
    # placed at the sleeve; C402/C404/C406/C408 stay on the plane for RF.
    gsense = ("R404", "R408", "R412", "R416")
    if any({pin.number: pin.net for pin in pins[ref]}.get("2") != "GND" for ref in gsense):
        raise ValueError("R404/R408/R412/R416 pin 2 changed; re-review ground-sense ECO F10")
    for ref in gsense:
        pins[ref] = [Pin(pin.number, pin.name, "N4_GSENSE" if pin.number == "2" else pin.net)
                     for pin in pins[ref]]
    add(replace(base_parts["R107"], row=9006, block=4, refs=["R448"],
                description="0 Ω net tie: N4_GSENSE to GND at the J702 sleeve (single join)",
                notes="Functional ECO F10: ground-sense reference join at the J702 sleeve"), {
        "R448": [Pin("1", "1", "N4_GSENSE"), Pin("2", "2", "GND")],
    })
    return parts, pins, libparts


def read_design() -> tuple[dict[str, Part], dict[str, list[Pin]], dict[str, Part]]:
    """Return the immutable source plus owner-approved, explicitly checked ECOs."""
    parts, workbook_pins, libparts = read_source()
    return apply_functional_eco(parts, apply_approved_overrides(workbook_pins), libparts)


def footprint(part: Part, ref: str) -> str:
    package = part.package.strip()
    prefix = re.match(r"[A-Za-z]+", ref).group(0)
    if ref == "J101":
        return "DAC_HPA:J101_USB4105-GF-A_12lands_4stakes"
    if ref == "D102":
        return "DAC_HPA:D102_SMDJ12A_HandSolder"
    if ref in {"C631", "C632", "C633", "C634"}:
        return "DAC_HPA:C631_ECHU1H224GX9_D4"
    if ref in {"K601", "K602", "K603", "K604"}:
        return "DAC_HPA:K601_TLP3545A_LF1_HandSolder"
    if ref == "J201":
        return "DAC_HPA:PinHeader_1x08_P2.54mm_SMD_XKB_X6511WVS-08H-C60D48R1"
    if ref == "J202":
        return "DAC_HPA:PinHeader_1x05_P2.54mm_SMD_XKB_X6511WVS-05H-C60D48R1"
    if ref == "J701":
        return "DAC_HPA:J701_GT-3321667P-01_maker_slots"
    if ref == "J702":
        return "DAC_HPA:J702_PJ-332A-6A_peg_holes"
    if ref == "J703":
        return "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical"
    if ref == "X201":
        return "DAC_HPA:X201_KC2520K80_Kyocera"
    if ref in {"U403", "U404"}:
        # The existing JLC library land is for TI's same DGK0008A VSSOP-8
        # package (C140314). TI's OPA2210 D/DGK pin table is identical.
        return "JLC_Imported:VSSOP-8_L3.0-W3.0-P0.65-LS5.0-BL"
    if ref == "U621":
        if part.lcsc != "C507231":
            raise ValueError("U621 JLC C507231 identity changed; re-review ECO footprint")
        # Imported from the exact C507231 EasyEDA Pro device. The TI DCK0006A
        # example land is larger, so physical G-3 overlay/DFM is still open.
        return "JLC_Imported:SC-70-6_L2.2-W1.3-P0.65-LS2.1-BL"
    if ref in {"X202", "X203"}:
        return "DAC_HPA:X202_X203_NDK_NZ2520SDA"
    if package in {"0402", "0603", "0805", "1206"}:
        size = {"0402": "0402_1005Metric", "0603": "0603_1608Metric", "0805": "0805_2012Metric", "1206": "1206_3216Metric"}[package]
        family = {"R": "Resistor_SMD:R", "C": "Capacitor_SMD:C", "FB": "Inductor_SMD:L"}.get(prefix)
        if family:
            return f"{family}_{size}"
    if ref.startswith("TP"):
        return "DAC_HPA:TestPad_D1.0mm"
    if ref.startswith("MH"):
        return "DAC_HPA:MountingHole_M3_3.2mm_Pad6.0mm"
    if ref.startswith("FID"):
        return "Fiducial:Fiducial_1mm_Mask2mm"
    candidate = jlc_footprint_map().get(part.lcsc)
    if candidate and candidate["status"] == "candidate_exact_numbers":
        return f"JLC_Imported:{candidate['footprint']}"
    alias = JLC_EXPOSED_PAD_ALIASES.get(part.lcsc)
    if candidate and alias:
        original, pad_name = alias
        if candidate["footprint"] != original:
            raise ValueError(f"JLC footprint changed for {part.lcsc}")
        return f"DAC_HPA:{original}_{pad_name}"
    return ""


@lru_cache(maxsize=1)
def jlc_footprint_map() -> dict:
    path = HERE / "jlc_footprints.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


JLC_EXPOSED_PAD_ALIASES = {
    "C128401": ("WSON-6_L2.0-W2.0-P0.65-TL-EP", "PAD"),
    "C18208899": ("QFN-32_L4.0-W4.0-P0.40-BL-EP2.7", "EP"),
    "C2155774": ("ESOP-8_L4.9-W3.9-P1.27-LS6.0-BL-EP", "PAD"),
    "C2688377": ("QFN-28_L5.0-W5.0-P0.50-BL-EP3.3", "EP"),
    "C2848334": ("WSON-6_L2.0-W2.0-P0.65-TL-EP", "PAD"),
    "C2876559": ("VSON-10_L3.0-W3.0-P0.50-BL-EP1.65", "PAD"),
    "C473398": ("WSON-12_L3.0-W2.0-P0.50-BL-EP", "PAD"),
}


def symbol_value(part: Part) -> str:
    if part.value and part.value != "—":
        return part.value
    if part.mpn and part.mpn != "—":
        return part.mpn
    return part.description.split(";")[0][:35]


def workbook_value(part: Part, ref: str) -> str:
    """Keep the original v0.9 value visible when an owner override is applied."""
    if part.row >= 9000:
        return "— (functional ECO; absent from Parts List v0.9)"
    return "OPA2210IDR" if ref in {"U403", "U404"} else part.value


def datasheet_url(part: Part) -> str:
    # The workbook links these KYOCERA AVX TAJ capacitors to an unrelated
    # Kemet T495 page. Keep the specified MPN and use its maker's TAJ sheet.
    if part.mpn == "Kyocera AVX TAJD227K010RNJ":
        return "https://datasheets.kyocera-avx.com/TAJ.pdf"
    return part.datasheet


def geom(pins: list[Pin]) -> tuple[int, int, list[tuple[Pin, int, int, int]], str]:
    """Return body half-width/half-height, pin endpoint positions, and drawing kind.

    Coordinates are integer multiples of the 1.27 mm KiCad connection grid.
    Symbol coordinates have +y upwards; the schematic has +y downwards.
    """
    count = len(pins)
    if count == 1:
        return 2, 2, [(pins[0], -4, 0, 0)], "testpoint"
    if count == 2:
        return 2, 2, [(pins[0], -4, 0, 0), (pins[1], 4, 0, 180)], "two-pin"
    left = math.ceil(count / 2)
    right = count - left
    rows = max(left, right)
    half_h = rows + 1
    longest = max(len(pin.name) for pin in pins)
    half_w = max(8, min(17, math.ceil(longest * 0.45) + 5))
    if count >= 20:
        half_w = max(half_w, 16)
    positions = []
    for i, pin in enumerate(pins[:left]):
        positions.append((pin, -half_w - 4, rows - 1 - 2 * i, 0))
    for i, pin in enumerate(pins[left:]):
        positions.append((pin, half_w + 4, rows - 1 - 2 * i, 180))
    return half_w, half_h, positions, "box"


def prop(name: str, value: str, x: float, y: float, size: float = 1.016, hide: bool = False) -> str:
    return (
        f"(property {q(name)} {q(value)} (at {f(x)} {f(y)} 0) "
        f"(effects (font (size {f(size)} {f(size)})){' (hide yes)' if hide else ''}))"
    )


POWER_OUTPUT_PINS = {
    "U102": {"1"}, "U302": {"5"}, "U303": {"5"},
    "U501": {"6", "11"}, "U502": {"5"}, "U503": {"5"}, "U504": {"1"},
}

PUSH_PULL_OUTPUT_PINS = {
    "U201": {"4"},
    "U205": {"4"}, "U206": {"4"}, "U208": {"2", "5", "7"},
    "U301": {"9", "10", "13", "14", "23"},
    "U401": {"7", "9"}, "U402": {"7", "9"},
    "U403": {"1", "7"}, "U404": {"1", "7"},
    "U604": {"1", "7"}, "U607": {"4"}, "U608": {"3", "5"},
    "X201": {"3"}, "X202": {"3"}, "X203": {"3"},
    "U621": {"4", "6"},
}

OPEN_COLLECTOR_OUTPUT_PINS = {
    ref: {"1", "2", "13", "14"}
    for ref in ("U603", "U606", "U609", "U610", "U611", "U612")
}
OPEN_COLLECTOR_OUTPUT_PINS["U605"] = {"1", "7"}
for _comparator in (f"U{number}" for number in range(613, 621)):
    OPEN_COLLECTOR_OUTPUT_PINS[_comparator] = {"1", "7"}

INPUT_PINS = {
    "U102": {"4"}, "U205": {"1", "3", "6"}, "U206": {"1", "3", "6"},
    "U208": {"1", "3", "6"},
    "U301": {"3", "5", "7", "25", "26", "27", "28"},
    "U401": {"1", "5", "6", "8", "10"},
    "U402": {"1", "5", "6", "8", "10"},
    "U403": {"2", "3", "5", "6"}, "U404": {"2", "3", "5", "6"},
    "U502": {"3"}, "U503": {"3"}, "U505": {"4"},
    "U604": {"2", "3", "5", "6"},
    "U605": {"2", "3", "5", "6"}, "U607": {"2"},
    "U608": {"1", "2", "6", "7"},
    "X201": {"1"}, "X202": {"1"}, "X203": {"1"},
    "U621": {"1", "3"},
}
for _comparator in ("U603", "U606", "U609", "U610", "U611", "U612"):
    INPUT_PINS[_comparator] = {"4", "5", "6", "7", "8", "9", "10", "11"}
for _comparator in (f"U{number}" for number in range(613, 621)):
    INPUT_PINS[_comparator] = {"2", "3", "5", "6"}


def electrical_type(ref: str, pin: Pin) -> str:
    """Type outputs confirmed by the design notes; leave other pins conservative."""
    if pin.number in POWER_OUTPUT_PINS.get(ref, set()):
        return "power_out"
    if pin.number in PUSH_PULL_OUTPUT_PINS.get(ref, set()):
        return "output"
    if pin.number in OPEN_COLLECTOR_OUTPUT_PINS.get(ref, set()):
        return "open_collector"
    if pin.number in INPUT_PINS.get(ref, set()):
        return "input"
    return "passive"


def pin_def(pin: Pin, x: int, y: int, angle: int, count: int, pin_type: str) -> str:
    length = 2 if count <= 2 else 4
    text_size = 0.762 if count >= 3 else 0.889
    return (
        f"(pin {pin_type} line (at {mm(x)} {mm(y)} {angle}) (length {mm(length)}) "
        f"(name {q(pin.name)} (effects (font (size {f(text_size)} {f(text_size)})))) "
        f"(number {q(pin.number)} (effects (font (size 0.762 0.762)))))"
    )


def library_symbol(part: Part, pins: list[Pin], embedded: bool) -> str:
    half_w, half_h, positions, kind = geom(pins)
    sid = part.symbol_id
    name = f"{PROJECT}:{sid}" if embedded else sid
    prefix = re.match(r"[A-Za-z]+", part.refs[0]).group(0)
    lines = [
        f"(symbol {q(name)}",
        "(pin_numbers (hide yes))",
        "(pin_names (offset 0.508))",
        "(exclude_from_sim no) (in_bom yes) (on_board yes)",
        prop("Reference", prefix, 0, GRID * (half_h + 3)),
        prop("Value", symbol_value(part), 0, -GRID * (half_h + 3)),
        prop("Footprint", "", 0, 0, hide=True),
        prop("Datasheet", "", 0, 0, hide=True),
        prop("Description", part.description, 0, 0, hide=True),
        f"(symbol {q(sid + '_1_1')}",
    ]
    if kind == "box":
        lines.append(
            f"(rectangle (start {mm(-half_w)} {mm(half_h)}) "
            f"(end {mm(half_w)} {mm(-half_h)}) "
            "(stroke (width 0.254) (type default)) (fill (type background)))"
        )
    elif kind == "two-pin":
        if prefix == "C":
            for plate_x in (-1, 1):
                lines.append(
                    f"(polyline (pts (xy {mm(plate_x)} {mm(2)}) (xy {mm(plate_x)} {mm(-2)})) "
                    "(stroke (width 0.254) (type default)) (fill (type none)))"
                )
        else:
            lines.append(
                f"(rectangle (start {mm(-2)} {mm(1)}) (end {mm(2)} {mm(-1)}) "
                "(stroke (width 0.254) (type default)) (fill (type none)))"
            )
            if prefix in {"D", "LED"}:
                lines.append(
                    f"(polyline (pts (xy {mm(-2)} {mm(2)}) (xy {mm(-2)} {mm(-2)})) "
                    "(stroke (width 0.254) (type default)) (fill (type none)))"
                )
    else:
        lines.append(
            f"(circle (center 0 0) (radius {mm(1)}) "
            "(stroke (width 0.254) (type default)) (fill (type none)))"
        )
    lines.extend(pin_def(pin, x, y, angle, len(pins), electrical_type(part.refs[0], pin))
                 for pin, x, y, angle in positions)
    lines.extend([")", ")"])
    return "\n".join(lines)


def lib_mechanical(sid: str, embedded: bool) -> str:
    name = f"{PROJECT}:{sid}" if embedded else sid
    lines = [
            f"(symbol {q(name)}",
            "(pin_numbers (hide yes)) (pin_names (hide yes))",
            "(exclude_from_sim no) (in_bom no) (on_board yes)",
            prop("Reference", sid, 0, 5.08),
            prop("Value", sid, 0, -5.08),
            prop("Footprint", "", 0, 0, hide=True),
            prop("Datasheet", "", 0, 0, hide=True),
            f"(symbol {q(sid + '_1_1')}",
            f"(circle (center 0 0) (radius {mm(2)}) (stroke (width 0.254) (type default)) (fill (type none)))",
    ]
    if sid == "MH":
        lines.append(
            '(pin passive line (at -5.08 0 0) (length 2.54) '
            '(name "1" (effects (font (size 0.762 0.762)))) '
            '(number "1" (effects (font (size 0.762 0.762)))))'
        )
    lines.extend([")", ")"])
    return "\n".join(lines)


# Per-sheet regions, in 1.27 mm grid units. All pages fit A2 landscape.
REGIONS = {
    1: (16, 20, 135, 280),
    2: (16, 20, 280, 280),
    3: (16, 20, 145, 280),
    4: (16, 20, 323, 280),
    5: (16, 20, 205, 300),
    6: (16, 20, 620, 390),
    7: (16, 20, 174, 95),
    8: (16, 20, 174, 223),
}

TITLES = {
    1: "1  USB-C INPUT / OVP / SENSING",
    2: "2  USB AUDIO BRIDGE / CPLD / CLOCKS",
    3: "3  ES9018K2M DAC",
    4: "4  I/V CONVERTERS / OUTPUT LEGS",
    5: "5  POWER DOMAINS / RAILS",
    6: "6  PROTECTION / OUTPUT SWITCH",
    7: "7  OUTPUTS / INDICATORS",
    8: "8  TEST PADS / PCB ITEMS",
}

SHEET_FILES = {
    1: "01_usb_input.kicad_sch",
    2: "02_usb_bridge.kicad_sch",
    3: "03_dac.kicad_sch",
    4: "04_iv_output_legs.kicad_sch",
    5: "05_power.kicad_sch",
    6: "06_protection.kicad_sch",
    7: "07_outputs.kicad_sch",
    8: "08_test_pads.kicad_sch",
}

PAPER_BY_BLOCK = {1: "A3", 3: "A3", 6: "A1", 7: "A4"}  # Dense protection sheet needs A1.


def layout(parts: dict[str, Part], pins: dict[str, list[Pin]]) -> dict[str, tuple[int, int]]:
    positions: dict[str, tuple[int, int]] = {}
    for block in range(1, 9):
        left, top, width, height = REGIONS[block]
        refs = sorted((ref for ref, part in parts.items() if part.block == block), key=natural)
        active = sorted((ref for ref in refs if len(pins[ref]) >= 3), key=lambda r: (-len(pins[r]), natural(r)))
        small = [ref for ref in refs if len(pins[ref]) <= 2]
        x = left + 6
        y = top + 22
        shelf = 0
        for ref in active:
            hw, hh, _, _ = geom(pins[ref])
            item_width = max(43, 2 * (hw + 4 + 2 + 9))
            item_height = max(15, 2 * hh + 12)
            if x + item_width > left + width - 3:
                x = left + 6
                y += shelf
                shelf = 0
            positions[ref] = (x + item_width // 2, y + item_height // 2)
            x += item_width
            shelf = max(shelf, item_height)
        small_top = y + shelf + (7 if active else 0)
        cell_w = 32 if block == 8 else 36
        cell_h = 12
        cols = max(1, (width - 12) // cell_w)
        for index, ref in enumerate(small):
            positions[ref] = (
                left + 6 + cell_w // 2 + (index % cols) * cell_w,
                small_top + cell_h // 2 + (index // cols) * cell_h,
            )
        last_y = small_top + math.ceil(len(small) / cols) * cell_h
        if last_y > top + height - 4:
            raise ValueError(f"Block {block} overflows its A0 region ({last_y} > {top + height})")
    # Mechanical designators are specified in the Parts list but have no Netlist rows.
    for index in range(1, 5):
        positions[f"MH{index}"] = (30 + (index - 1) * 35, 190)
    for index in range(1, 8):
        positions[f"FID{index}"] = (30 + (index - 1) % 4 * 35, 205 + (index - 1) // 4 * 13)
    return positions


def label_at(net: str, x: int, y: int, side: int, key: str) -> str:
    angle = 180 if side < 0 else 0
    return (
        f"(global_label {q(net)} (shape bidirectional) (at {mm(x)} {mm(y)} {angle}) "
        f"(effects (font (size 0.762 0.762)) (justify {'right' if side < 0 else 'left'} bottom)) "
        f"(uuid {q(uid('label', key))}))"
    )


def placed_symbol(ref: str, part: Part | None, pins: list[Pin], x: int, y: int, sheet_uuid: str) -> list[str]:
    sid = part.symbol_id if part else ("MH" if ref.startswith("MH") else "FID")
    hw, hh, pin_positions, _ = geom(pins) if part else (
        2, 2, [(pins[0], -4, 0, 0)] if pins else [], "testpoint"
    )
    is_dnf = part is not None and part.fit == "No"
    is_bom = part is not None and part.fit in {"Yes", "Owner", "No"}
    value = symbol_value(part) if part else ("M3 plated to GND" if ref.startswith("MH") else "Fiducial")
    package = part.package if part else ("M3 3.2 mm / 6.0 mm pad" if ref.startswith("MH") else "1.0 mm / 2.0 mm mask")
    fp = footprint(part, ref) if part else (
        "DAC_HPA:MountingHole_M3_3.2mm_Pad6.0mm"
        if ref.startswith("MH") else "Fiducial:Fiducial_1mm_Mask2mm"
    )
    lines = [
        f"(symbol (lib_id {q(PROJECT + ':' + sid)}) (at {mm(x)} {mm(y)} 0) (unit 1) "
        f"(exclude_from_sim no) (in_bom {'yes' if is_bom else 'no'}) "
        f"(on_board {'no' if ref == 'J703' else 'yes'}) "
        f"(dnp {'yes' if is_dnf else 'no'}) (uuid {q(uid('placed', ref))})",
        prop("Reference", ref, (x * GRID), (y - hh - 2) * GRID, size=0.889),
        prop("Value", value, (x * GRID), (y + hh + 2) * GRID, size=0.889),
        prop("Footprint", fp, x * GRID, y * GRID, hide=True),
        prop("Datasheet", datasheet_url(part) if part else "", x * GRID, y * GRID, hide=True),
        prop("MPN", part.mpn if part else "", x * GRID, y * GRID, hide=True),
        prop("LCSC", part.lcsc if part else "", x * GRID, y * GRID, hide=True),
        prop("LCSC Part #", part.lcsc if part else "", x * GRID, y * GRID, hide=True),
        prop("Assembly", part.fit if part else "No part", x * GRID, y * GRID, hide=True),
        prop("Package", package, x * GRID, y * GRID, hide=True),
        prop("Rating/Tolerance", part.rating_tolerance if part else "", x * GRID, y * GRID, hide=True),
        prop("Source", part.source if part else "PCB copper", x * GRID, y * GRID, hide=True),
        prop("Workbook Value", workbook_value(part, ref) if part else "", x * GRID, y * GRID, hide=True),
        prop("Footprint status", "PROVISIONAL" if not fp else "VERIFY G-3", x * GRID, y * GRID, hide=True),
    ]
    for pin in pins:
        lines.append(f"(pin {q(pin.number)} (uuid {q(uid('placed-pin', ref, pin.number))}))")
    lines.append(
        f"(instances (project {q(PROJECT)} (path {q('/' + ROOT_UUID + '/' + sheet_uuid)} "
        f"(reference {q(ref)}) (unit 1))))"
    )
    lines.append(")")

    for pin, px, py, angle in pin_positions:
        gx, gy = x + px, y - py
        key = f"{ref}:{pin.number}"
        if pin.net == "NC":
            lines.append(f"(no_connect (at {mm(gx)} {mm(gy)}) (uuid {q(uid('nc', key))}))")
            continue
        side = -1 if angle == 0 else 1
        label_x = gx + side * 2
        lines.append(
            f"(wire (pts (xy {mm(gx)} {mm(gy)}) (xy {mm(label_x)} {mm(gy)})) "
            f"(stroke (width 0) (type solid)) (uuid {q(uid('wire', key))}))"
        )
        lines.append(label_at(pin.net, label_x, gy, side, key))
    return lines


def text_note(value: str, x: int, y: int, size: float) -> str:
    return (
        f"(text {q(value)} (exclude_from_sim no) (at {mm(x)} {mm(y)} 0) "
        f"(effects (font (size {f(size)} {f(size)})) (justify left bottom)) "
        f"(uuid {q(uid('text', value))}))"
    )


def make() -> None:
    base_parts, workbook_pins, base_libparts = read_source()
    pins = apply_approved_overrides(workbook_pins)
    parts, pins, libparts = apply_functional_eco(base_parts, pins, base_libparts)
    # Preserve every pre-ECO sheet position. Put the new buffer group in the
    # open lower area of sheet 6 and the two TVS symbols in sheet 7's last row.
    positions = layout(base_parts, workbook_pins)
    positions.update({
        "R688": (40, 278), "R689": (76, 278), "U621": (130, 278),
        "R952": (220, 278), "R953": (256, 278),
        "R954": (292, 278), "R955": (328, 278), "C667": (364, 278),
        "D707": (112, 105), "D708": (148, 105),
        "R448": (76, 207),  # ECO F10: next free cell after R447 on sheet 4
    })
    project_file = HERE / f"{PROJECT}.kicad_pro"
    if not project_file.exists():
        project_file.write_text("{}\n", encoding="utf-8")
    lib = [library_symbol(part, pins[part.refs[0]], embedded=False) for part in libparts.values()]
    lib += [lib_mechanical("MH", False), lib_mechanical("FID", False)]
    (HERE / f"{PROJECT}.kicad_sym").write_text(
        "(kicad_symbol_lib (version 20251024) (generator \"kicad_symbol_editor\")\n"
        + "\n".join(lib)
        + "\n)\n",
        encoding="utf-8",
    )
    (HERE / "sym-lib-table").write_text(
        '(sym_lib_table (lib (name "DAC_HPA") (type "KiCad") '
        '(uri "${KIPRJMOD}/DAC_HPA.kicad_sym") (options "") (descr "DAC-HPA capture symbols")) '
        '(lib (name "JLC_DAC_HPA") (type "EasyEDA (JLCEDA) Pro") '
        '(uri "${KIPRJMOD}/JLC_Source/JLC_DAC_HPA.elibz") (options "") '
        '(descr "JLCPCB source symbols for cross-check")))\n',
        encoding="utf-8",
    )
    root_lines = [
        "(kicad_sch", "(version 20260306)", '(generator "eeschema")',
        '(generator_version "10.0")', f"(uuid {q(ROOT_UUID)})", '(paper "A3")',
        '(title_block (title "USB DAC + Balanced Headphone Amplifier") '
        '(date "2026-09-28") (rev "v1.1-ECO1") '
        '(comment 1 "Spec v1.1 / Notes v1.0 / Parts List v0.9 + ECO F02/F04") '
        '(comment 2 "REVIEW ONLY: capture F01, attach F03 and G-1 to G-4 open"))',
        text_note("SCHEMATIC CAPTURE v1.1-ECO1 — F02/F04 captured; F01/F03 and G-1 to G-4 open.", 20, 20, 1.524),
    ]
    for block, title in TITLES.items():
        sheet_uuid = uid("sheet", block)
        sx, sy = 20 + (block - 1) % 2 * 150, 40 + (block - 1) // 2 * 45
        sw, sh = 120, 25
        root_lines.append(
            f"(sheet (at {mm(sx)} {mm(sy)}) (size {mm(sw)} {mm(sh)}) "
            f"(stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) "
            f"(uuid {q(sheet_uuid)}) "
            f"{prop('Sheetname', title, sx * GRID, (sy - 2) * GRID)} "
            f"{prop('Sheetfile', SHEET_FILES[block], sx * GRID, (sy + sh + 2) * GRID)} "
            f"(instances (project {q(PROJECT)} (path {q('/' + ROOT_UUID)} "
            f"(page {q(block + 1)})))))"
        )
    root_lines.extend(['(sheet_instances (path "/" (page "1")))', ")"])
    (HERE / f"{PROJECT}.kicad_sch").write_text("\n".join(root_lines) + "\n", encoding="utf-8")

    for block, title in TITLES.items():
        sheet_uuid = uid("sheet", block)
        document_uuid = uid("document", block)
        embedded = [library_symbol(part, pins[part.refs[0]], embedded=True)
                    for part in libparts.values() if part.block == block]
        if block == 8:
            embedded += [lib_mechanical("MH", True), lib_mechanical("FID", True)]
        lines = [
            "(kicad_sch", "(version 20260306)", '(generator "eeschema")',
            '(generator_version "10.0")', f"(uuid {q(document_uuid)})",
            f'(paper {q(PAPER_BY_BLOCK.get(block, "A2"))})',
            f"(title_block (title {q(title)}) (date \"2026-09-28\") "
            f"(rev \"v1.1-ECO1\") "
            f"(comment 1 \"Spec v1.1 / Notes v1.0 / Parts List v0.9 + ECO F02/F04\") "
            f"(comment 2 \"REVIEW ONLY: capture F01, attach F03 and G-1 to G-4 open\"))",
            "(lib_symbols", *embedded, ")",
            text_note(title, 16, 12, 1.524),
        ]
        for ref in sorted(parts, key=natural):
            if parts[ref].block != block:
                continue
            x, y = positions[ref]
            lines.extend(placed_symbol(ref, parts[ref], pins[ref], x, y, sheet_uuid))
        if block == 8:
            for ref in [*(f"MH{i}" for i in range(1, 5)), *(f"FID{i}" for i in range(1, 8))]:
                x, y = positions[ref]
                mechanical_pins = [Pin("1", "1", "GND")] if ref.startswith("MH") else []
                lines.extend(placed_symbol(ref, None, mechanical_pins, x, y, sheet_uuid))
        lines.append(")")
        (HERE / SHEET_FILES[block]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated 8 sheets, {len(parts)} netlisted components, 11 mechanical components, "
          f"{sum(map(len, pins.values()))} approved schematic pins")


if __name__ == "__main__":
    make()
