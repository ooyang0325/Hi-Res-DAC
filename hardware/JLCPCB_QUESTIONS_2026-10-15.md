# Questions to JLCPCB before ordering (to send as written)

Board: 120 × 100 mm, 6 layers (JLC06161H-3313), 1.6 mm, ENIG. Quantity 5, with Standard PCBA,
components on the top side only. Designators and part numbers below match the BOM and placement
files we will upload.

**1. Connectors with plated slots: J101 and J702.**
- J101: GCT USB4105-GF-A (LCSC C3020560), a USB-C receptacle. It has 12 SMD lands and 4 plated shell-stake slots:
  - S1/S2: slots 0.60 × 1.70 mm, pads 1.14 × 2.24 mm;
  - S3/S4: slots 0.60 × 1.40 mm, pads 1.14 × 1.94 mm.
- J702: HRO PJ-332A-6A (LCSC C2848643), a 3.5 mm jack. Pins 3–6 are SMD lands; pins 1 and 2 are plated slots, 0.60 × 1.50 mm, in 2.25 × 1.35 mm pads.

Can you solder these slots in the same reflow (pin-in-paste)? If so:
- what stencil aperture do you need on the slots;
- should we add it to our paste layer, or will you set it from an order remark?

If not, please confirm that you will reflow the SMD lands only and leave the slots unsoldered, and we
will solder them by hand.

**2. Pin headers J201 and J202.**
- J201: XKB X6511WVS-08H-C60D48R1 (LCSC C2883805).
- J202: XKB X6511WVS-05H-C60D48R1 (LCSC C2883802).

Your parts pages say these need an assembly fixture. Please confirm the fixture and its cost. Please
also show both headers in the DFM placement preview, so we can check pin 1 before production.

**3. Via filling.** The board has 1578 vias, with drills of 0.20–0.40 mm. 59 of them are inside or touch
SMD pads. We plan to order "Epoxy filled & capped" for the whole board. Please confirm that:
- this covers every via, including the ones in the pads;
- the caps are plated flat, so those pads stay solderable.

**4. Cleaning after assembly.** The board has high-impedance circuits, so flux residue must not stay
on it.
- Please wash the boards after reflow, including the parts of the board under component bodies.
- The required surface insulation resistance after cleaning is at least 2 × 10¹⁰ Ω/sq.

Can you do this, and what cleanliness record can you provide (ionic contamination or surface
insulation resistance test)? What does it cost?

**5. Reflow profile.**
- C631–C634: Panasonic ECH-U1H224GX9 (PPS film capacitor, 2416). They allow at most 95 s above 220 °C and a 260 °C peak.
- J101's limit is 255 °C for 5 s, so we ask for a peak of 245 °C or lower.

Does your profile stay within both limits? If it cannot meet the film capacitor limit, we will leave
C631–C634 unplaced and fit them by hand.

**6. USB impedance.** The USB pair (D+/D−) runs on the top layer over the first inner ground layer:
- in stackup JLC06161H-3313;
- 0.17 mm traces with a 0.215 mm gap in the coupled section;
- designed for 90 Ω differential (calculated 89–90 Ω).

Can you build with impedance control on this pair, and to what tolerance? If you would change the
widths, please tell us the values. If impedance control is not possible, we will order without it.

**7. Marking of U202.** U202 is LCSC C18208899, listed as AGM AGRV2KQ32. The manufacturer sells this
device as the AG32VF series, so the parts may be marked "AG32VF?03K?U6" rather than "AGRV2KQ32". Please
confirm:
- which marking your stock carries;
- that your incoming inspection and placement check will accept it.

**8. Quote.** Please quote the order with the options above:
- 5 boards;
- epoxy filled and capped vias;
- 469 placed parts, two of them with plated slots (J101, J702);
- the J201/J202 fixture;
- washing with the cleanliness record;
- impedance control, if you offer it.
