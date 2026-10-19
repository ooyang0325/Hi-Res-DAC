# G-4 polarity and pin-1 record — design set v1.2 (Spec v1.2 / Notes v1.1)

**Netlist level: done.** Every listed part's pin functions land on the intended nets (OD-17, accepted
14 Oct 2026; the nets are in the table). What remains is physical.

Check two samples of each applicable part against:
- the tape-pocket and body marks;
- the maker's pinout;
- the KiCad footprint (G-3 overlay cell);
- the captured net.

Use a DMM diode test on the diodes. Use the marks and the pin map for capacitors and ICs. Enter sample
IDs, readings and the reviewer before G-4 passes.

**Where the risk is.**
- **Two-terminal polarised parts** (D102, D411/D412, C442/C443, D705/D706) reverse if placed 180° the wrong way. A rotation error in the placement file would do exactly that at JLCPCB. Check them on the samples, and again in JLCPCB's DFM placement preview ("Confirm Parts Placement").
- **Three-pin SOT-23 parts** cannot be placed reversed. For them, pin 1 of the footprint must match pin 1 of the datasheet.

| Part(s) | Required physical check (expected net per pad) | G-3 cell | Sample IDs / readings / result |
| --- | --- | --- | --- |
| D705, D706 (KENTO KT-0805G / KT-0603R) | Pad 1 = anode (N7_LEDG_A / N7_LEDR_A), pad 2 = cathode (GND). Owner override of 26 Sep, now in Notes v1.1 check 53. Diode test on two samples each; record the tape/body cathode mark | 10, 11 | |
| D102 (Littelfuse SMDJ12A, owner-fitted) | Cathode band on pad 1 = VBUS, anode pad 2 = GND; fitted before the first USB plug-in | 12 | |
| D411, D412 (Nexperia PMEG2010AEH) | Cathode band on pad 1: D411 → N4_VPOS_IV (anode VPOS); D412 → VNEG (anode N4_VNEG_IV) | 14 | |
| C442, C443 (AVX TAJD227K010RNJ, D case) | + band on pad 1: C442 + → N4_VPOS_IV (− GND); C443 + → GND (− N4_VNEG_IV). A reversed MnO2 part fails short | 15 | |
| D104, D105, D413, D414 (Nexperia BAT54) | Pin 1 A, pin 3 K, pin 2 no net. D104 3V3A → 5V_SYS; D105 5V_ANA → 5V_SYS; D413 GND → N4_VPOS_IV; D414 N4_VNEG_IV → GND | 13 | |
| D405–D408 (Nexperia BAT54S) | Pin 1 A1 = GND, pin 2 K2 = AVCC_L (D405/D406) or AVCC_R (D407/D408), pin 3 K1/A2 = the I/V node | 28 | |
| D609, D610 | D609 (BAS70-04): pin 1 A1 = GND, pin 2 K2 = N6_MCK_RC, pin 3 K1/A2 = N6_PMP. D610 per the captured pin map | 20 | |
| K601–K604 (TLP3545A, owner-fitted) | Physical pin 1 matches the owner-fitted land and the silkscreen mark | 04 | |
| X201–X203 | Physical pin 1 (stand-by/INH) matches each 2520 land and the placement orientation. Include the X201 second source | 05, 06 | |
| U202 (C18208899) | Pin 1 mark matches the footprint; parts are marked `AG32VF?03K?U6` (expected, JLCPCB 15 Oct) | 27 | |
| U206, U208, U621 | Pin-1 body/tape marks match the footprints and captured pin 1 | 09, 16, 29 | |
| U403, U404 (OPA2210 DGK), U605–U620 | Pin-1 body/tape marks match the footprints and captured pin 1. U403/U404 and U613–U620 use the TI DGK land | 17–19, 22, 26 | |
| Q623–Q627 (MMBT3904LT1G) | Pin 1 base, pin 2 emitter, pin 3 collector, matching the onsemi SOT-23 land and the netlist | 23 | |
| J201, J202 (XKB headers) | Pin 1 matches the silk pin-1 mark. A wrong-variant header cannot land (J201) or is identical rotated 180° (J202, OD-10). Confirm in JLCPCB's DFM placement preview | 31, 32 | |

Not polarised, so outside G-4: the bidirectional ESD diodes D701, D707 and D708, and the film
capacitors C631–C634.

**At order review.** Check JLCPCB's DFM placement preview for every two-terminal polarised part above,
and for J201/J202 pin 1. Check the silkscreen pin-1 and polarity marks again on the placed board before
the G-5 freeze.

G-4 result: ☐ pass ☐ fail. Measurement date: __________. DFM preview checked (order no.): __________.
Reviewer/signature: ____________________.
