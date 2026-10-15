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
