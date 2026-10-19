Subject: Pre-order questions and quote request: 6-layer PCBA, 120 × 100 mm, 5 boards

Dear JLCPCB team,

We are preparing a PCB + PCBA order and would like to confirm a few points before we place it.

The board is 120 × 100 mm, 6 layers (stackup JLC06161H-3313), 1.6 mm thick, with an ENIG finish. We
need 5 boards, assembled with Standard PCBA, components on the top side only. The designators and
part numbers below match the BOM and placement files we will upload.

1. Connectors with plated slots (J101, J702)

J101 is a GCT USB4105-GF-A USB-C receptacle (LCSC C3020560). It has 12 SMD lands and 4 plated
shell-stake slots:
- S1/S2: 0.60 × 1.70 mm slots in 1.14 × 2.24 mm pads;
- S3/S4: 0.60 × 1.40 mm slots in 1.14 × 1.94 mm pads.

J702 is an HRO PJ-332A-6A 3.5 mm jack (LCSC C2848643). Pins 3–6 are SMD lands; pins 1 and 2 are
0.60 × 1.50 mm plated slots in 2.25 × 1.35 mm pads.

Can you solder these slots in the same reflow (pin-in-paste)? If so, what stencil aperture do you need
on the slots, and should we add it to our paste layer, or will you set it from an order remark? If not,
please confirm that you will reflow the SMD lands only and leave the slots unsoldered; we will then
solder them by hand.

2. Pin headers (J201, J202)

J201 is an XKB X6511WVS-08H-C60D48R1 (LCSC C2883805) and J202 an XKB X6511WVS-05H-C60D48R1 (LCSC
C2883802). Your parts pages say these need an assembly fixture. Please confirm the fixture and its
cost. Please also show both headers in the DFM placement preview, so that we can check pin 1 before
production.

3. Via filling

The board has 1578 vias with drills of 0.20–0.40 mm, and 59 of them are inside or touching SMD pads.
We plan to order "Epoxy filled & capped" for the whole board. Please confirm that this covers every
via, including the ones in pads, and that the caps are plated flat so those pads remain solderable.

4. Cleaning after assembly

The board has high-impedance circuits, so flux residue must not remain. Please wash the boards after
reflow, including the areas under component bodies. We need a surface insulation resistance of at
least 2 × 10¹⁰ Ω/sq after cleaning. Can you do this, and what cleanliness record can you provide (for
example an ionic contamination or surface insulation resistance test)? What would it cost?

5. Reflow profile

C631–C634 are Panasonic ECH-U1H224GX9 PPS film capacitors (2416 size). They allow at most 95 s above
220 °C and a 260 °C peak. J101 is rated for 255 °C for 5 s, so we would like a peak of 245 °C or lower.
Does your reflow profile stay within both limits? If it cannot meet the film capacitor limit, please
leave C631–C634 unplaced and we will fit them by hand.

6. USB impedance control

The USB D+/D− pair runs on the top layer over the first inner ground layer, in stackup JLC06161H-3313.
In the coupled section the traces are 0.17 mm wide with a 0.215 mm gap, designed for 90 Ω differential
(our calculation gives 89–90 Ω). Can you build with impedance control on this pair, and to what
tolerance? If you would adjust the widths, please tell us the values you recommend. If impedance
control is not available, we will order without it.

7. Marking of U202

U202 is LCSC C18208899, listed as AGM AGRV2KQ32. The manufacturer sells this device as the AG32VF
series, so the parts may be marked "AG32VF?03K?U6" rather than "AGRV2KQ32". Please confirm which
marking your stock carries, and that your incoming inspection and placement check will accept it.

8. Quote

Please quote the order with the options above: 5 boards; epoxy filled and capped vias; 469 placed
parts, two of them (J101, J702) with plated slots; the J201/J202 fixture; washing with a cleanliness
record; and impedance control on the USB pair, if available.

Thank you. We look forward to your reply.

Best regards,
[Name]
[Company / contact details]

---

# JLCPCB reply (15 Oct 2026) and the resulting order settings

Internal record; not part of the email above.

| # | JLCPCB answer | What follows | Status |
| --- | --- | --- | --- |
| 1 | The stencil follows our paste layer: slots with paste are pin-in-paste; without, they get no paste. The method is confirmed in the DFM review | The slot pads carry no paste. This is the Spec v1.2 R01 fallback, since JLCPCB gave no aperture geometry. JLCPCB reflows the SMD lands; the owner hand-solders J101 S1–S4 and J702 pins 1/2 from the bottom side (6 joints per board). Order remark below | Decided by R01; confirm at DFM |
| 2 | Fixture required: USD 8.21 each, 2 fixtures for 5 boards = USD 16.42 (not shipped). Both headers are shown in the DFM placement preview | Select "Confirm Parts Placement" and check pin 1 of J201/J202 in the preview (OD-10) | Closed; cost into the quote |
| 3 | Epoxy filled & capped covers every via, including those in pads, plated flat; free on 6 layers | Order that option | Closed |
| 4 | Board Cleaning service, USD 0.157 per board (dry-ice cleaning), including under bodies. **No SIR or ionic contamination report** | The ≥ 2 × 10¹⁰ Ω/sq requirement (OD-9) cannot be evidenced by JLCPCB. Recommendation: order the cleaning. After the owner's hand soldering, which adds its own flux, clean those joints with IPA (no ultrasonic: X201–X203 are crystal oscillators). Take the evidence from the planned 50 °C / 85 % RH bring-up test on the high-impedance nodes. That test also covers the open question of how well dry-ice cleaning reaches under QFN bodies | **Owner decision** |
| 5 | Reflow peak 240 ± 5 °C, about 60–90 s above 217 °C | Within the film-capacitor limit (≤ 95 s above 220 °C, 260 °C peak) and J101 (255 °C / 5 s). C631–C634 are placed by JLCPCB | Closed |
| 6 | Impedance control available, ±10 %. Give value, layer, reference, width/spacing and location with the Gerber; JLCPCB re-verifies and proposes widths before production | ±10 % is 81–99 Ω; the solved build corners are 82.2–98.6 Ω, inside it. Requirement text below. If JLCPCB proposes other widths, re-run the field solve and the clearance check before approving | Closed; text with the order |
| 7 | C18208899 is in stock; the AG32VF marking is expected and accepted against the part number and datasheet | Nothing to do | Closed |
| 8 | Upload Gerber, BOM and CPL for the base quote; the options are confirmed after the order is placed | Files from `python3 hardware/export_jlc_order.py OUT_DIR`: Gerber + drill zip, BOM, CPL (469 placements = BOM). For the real order, regenerate them from the frozen commit | Quote: owner |

**JLCDFM check (19 Oct 2026, JLCONE app, files from `0b8a4d6`).**

PCB DFM. Every red or orange item was traced to the board. None needs a change:

| Check | Result | Where / why acceptable |
| --- | --- | --- |
| Slot width | 18 red | J701 0.50 mm, J101 S1–S4 and J702 pins 1/2 0.60 mm plated slots. JLCDFM's red limit is 0.61 mm; JLCPCB's published plated-slot minimum is 0.50 mm, and every slot is ≥ 2 × its width (short-slot check: 0) |
| Pad spacing | 2 red, 9 orange | All same-net: VPOS via pair 0.052 mm and VNEG via pair 0.100 mm on B.Cu, plus 0.6 mm vias next to their own SMD pads (U609, Q619, R951, R905, R941, R412). Hole spacing check: 0 |
| Via to pad | 3 red, 1 orange | R218, C433, R671 and the U401/U402 pad vias. All are in the filled-and-capped set |
| Mask opening exposes trace | 1 red, 6 orange | Same-net trace leaving its pad (R928 LEG_RP 0.065 mm and others) |
| Trace spacing | 1 orange | N6_VT to N6_VT, same net |
| Annular ring | orange (vias) | 0.15 mm on the 0.3/0.6 mm vias; JLCDFM red limit 0.10 mm |
| Silkscreen to pad / hole, line width | red/orange (capped at 50) | Silk is clipped at mask openings and over capped vias; 0.15 mm lines are JLCDFM's orange band. Cosmetic |

SMT DFM (BOM + CPL):
- **J201/J202 position: fixed.** Their footprint origin is pin 1, so the CPL placed both headers 8.89 / 5.08 mm left of their lands. `export_jlc_order.py` now writes the body centre (`CENTRE_OFFSETS`); the preview then shows both on their lands with the legs on the alternating pads. Only J201/J202 changed in the CPL.
- **J201/J202 "collision" (red):** JLCDFM's models overlap by 0.31 mm. The XKB drawing gives the body as B = 2.54 × n ± 0.5 mm (20.32 / 12.70 mm), so the real gap is 0.68 mm nominal, 0.18 mm worst case. Not a clash; noted in the order remark.
- Component to edge: J101 and J702, edge connectors by design.
- Lead to hole (32): the filled-and-capped vias in the R218, C224, R690 and exposed-pad lands.
- Pin edge (U202, U301, U503): terminals flush with the land edges (0–0.008 mm). Accepted.
- Silk under body (34): pin-1 marks and outlines under part bodies. Cosmetic.

**BOM match: four lines had no LCSC number, and JLCPCB's auto-match picked wrong parts for them.** The owner supplied numbers on 19 Oct; checked on the JLCPCB part pages:

| Line | Required part | Auto-match offered | LCSC number now |
| --- | --- | --- | --- |
| C631–C634 | Panasonic ECH-U1H224GX9 | C5447085, an RS-485 transceiver | **C569856**, exact MPN, 2,828 in stock |
| R402–R416 (even) | Susumu RG1608N-202-W-T1 (0.05 %, 10 ppm/K) | C22975, a 2 kΩ thick-film 0603WAF2001T5E | **C4101918**, exact MPN, 0 in stock (pre-order) |
| X202 | NDK NZ2520SDA-49.152MHZ-NSC5083D | C5632403, a Crystek CCHD-575 in 7.5 × 5 mm | open |
| X203 | NDK NZ2520SDA-45.1584MHZ-NSC5083D | C5632479, a Crystek CCHD-575 in 7.5 × 5 mm | open |

Rejected candidates: C2073999 is Susumu RR0816P-202-D (0.5 %, 25 ppm/K, 0 in stock), outside the R402–R416
requirement. C5122395 is a generic "NZ2520SDA" listing with no frequency or option code (0 in stock), so it
cannot identify either X202 or X203. Until X202/X203 have exact numbers, deselect them at order or source
the listed MPNs through Global Sourcing; never accept the auto-match.

**Impedance requirement (to attach with the Gerber).**

> Controlled impedance: 90 Ω ± 10 % differential, USB D+/D− pair. Layer L1 (top), reference plane L2
> (first inner layer, solid ground), stackup JLC06161H-3313. Coupled sections: 0.17 mm width / 0.215 mm
> spacing (about 10 mm), and 0.18 mm width / 0.32 mm spacing (about 2.5 mm). Location: between J101
> (USB-C) and U201, passing U101. The short 0.20 mm split runs around U101 and the 0.16 mm escapes at
> J101 are not controlled.

**Order remark.**

> 1. J101 slots S1–S4 and J702 pins 1/2: no solder paste by design. Please reflow the SMD lands only and
>    leave these slots unsoldered; we will solder them by hand.
> 2. Please apply Board Cleaning after assembly.
> 3. Impedance control on the USB pair as specified in the attached requirement.
> 4. U202 (C18208899) parts marked "AG32VF…" are expected.
> 5. Please show the J201/J202 placement in the DFM preview for our pin-1 check.
> 6. J201/J202 are 0.68 mm apart (body 2.54 × n ± 0.5 mm per the XKB drawing). The online DFM models show
>    a 0.31 mm overlap; the real parts do not collide.
> 7. X202 and X203 must be the NDK MPNs in our BOM (no LCSC stock part). Please do not substitute.
