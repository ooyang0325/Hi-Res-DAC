# Pre-layout gate record — design set v1.1

Design Spec v1.1 permits **provisional placement on a 100 × 80 mm board**. Schematic freeze and routing remain on HOLD until G-1–G-4 pass. The KiCad netlist/ERC and a passing GitLab pipeline establish capture consistency, not physical contact or footprint fit.

| Gate | Evidence needed before schematic freeze and routing | Current record |
| --- | --- | --- |
| G-1 — J101 USB-C | Two identified USB4105-GF-A samples; DMM continuity of all 12 GCT solder lands, the four shell stakes and both plug orientations against the 16 JLC pad IDs; signed pad-to-contact table. | Owner reports both samples fully match the KiCad map, including both plug orientations. Sample IDs, raw readings and a signed pad table remain to be recorded before formal sign-off. |
| G-2 — J701/J702 jacks | Two identified samples of each jack; pad-to-plug contact table with no plug, fully inserted and slow insertion/removal; all internally common pairs; J701 tabs 11/12 versus sleeve/bushing; J702 break contacts 5/6. Only TRS use is permitted for J702. | Partial: owner reports both J702 samples match 3–5 and 4–6 closed with no plug and open with intended TRS inserted; with that plug, pads 1/2 = sleeve, 3 = right ring, 4 = left tip. Both J701 samples match pad 1 = sleeve, 2/3 = R−, 4/5 = R+, 6 = L−, 7/8 = L+ with the intended 4.4 mm plug. Sample IDs, raw DMM readings, shell/common-pair and insertion sweeps, and J701 tabs 11/12 remain to be recorded. |
| G-3 — 1:1 footprints | Drawing/sample overlay of J101/J701/J702, K601–K604, X201–X203, U202 exposed pad, the other new/changed lands in Spec §9.6, including U611/U612, Q627, C647–C654, and TI DGK U613–U620. Record pin-1 marks, slots, pegs, copper clearance and ≥0.1 mm terminal overlap; obtain JLCPCB DFM acceptance of the enlarged jack copper. | Open. Owner chose copper-only enlargement: J701 2.00 × 1.20 mm pads around unchanged 1.40 × 0.50 mm slots (+0.10 mm width tolerance); J702 pads 1/2 2.10 × 1.20 mm around unchanged 1.50 × 0.60 mm slots. Both reach a 0.30 mm worst copper ring. |
| G-4 — polarity | DMM diode/continuity checks on two samples against body/tape marks for D705/D706, BAT54S, D102, D104/D105, D411/D412, D609/D610, C442/C443, Q623–Q627, K601–K604 and the other pin-1 parts in Notes §9.6. | Open; the KiCad D705/D706 pad map was corrected, but physical orientation has not been recorded. |

## Decisions already in force

- Board size 100 × 80 mm, four layers, top-side Standard PCBA and the owner-fitted list remain as in Spec v1.1. These permit provisional placement.
- The 3.5 mm output is for TRS plugs only. The HRO jack has a TRRS body, but TRRS headphones are outside the supported use; G-2 needs the intended TRS test, which the owner reports matched on both samples. The PCB silkscreen/user instructions should say “3.5 SE · TRS only”.
- The v1.1 defaults remain adopted: pairwise boot self-test with production per-leg injection, the Spec's DC-energy definition, and the High-mode 32 Ω frozen-full-scale engineering estimate with a bring-up energy test. Reopening self-test coverage would add parts and must happen before routing.
- The owner kept the 50 mΩ-per-jack-contact and per-0 Ω-link assumption. Output impedance is measured at both jacks at bring-up against ≤0.5 Ω; this is not a pre-layout measurement.
- The owner chose a 0.30 mm worst copper ring by enlarging copper only. Slots, pad centres and peg holes do not move. G-3 overlay and JLCPCB DFM acceptance remain required.
- The 0.30 mm ring calculation includes the stated J701 slot-size tolerance but not fabrication registration error; JLCPCB must confirm the final land in DFM. The nearest J701 pad-to-pad copper gap is also 0.30 mm.

## Holds after layout

| Gate | Remaining work |
| --- | --- |
| G-5 — netlist/BOM freeze | Re-run the design, stress and PCBA checks after layout; confirm value-locked Rf, VREF and leg parts; review routed geometry and manufacturing outputs. |
| G-6 — order release | Obtain JLCPCB's written method for soldering J101 stakes S1–S4 and J702 slots 1/2, or invoke the owner bottom-side solder fallback. Confirm J702 reflow suitability and C631–C634 film-capacitor dwell or owner fitting; resolve stock/private-library lines, order remarks, quote, X-ray and placement rotation. |

Although G-6 is later, provisional placement must leave L4 access to J101 stakes and J702 slots, allow hand-solder clearance if J702 becomes entirely owner-fitted, and preserve 1.5 mm iron clearance around C631–C634 for their owner-fit fallback. These choices prevent an order-stage answer from forcing a board redesign.

The 22 open qualification rows in the Evidence register are bring-up obligations, not 22 additional pre-layout gates. Important thin margins include Default current, X201 duty/load, High-mode 32 Ω fault energy, timer leakage/reset level, and output power; the designed-in tests and fallbacks remain in Spec §9.1 and Notes Chapter 10.
