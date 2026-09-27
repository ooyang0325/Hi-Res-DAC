# Connector pin-map review (capture v1.1)

The schematic follows Parts List v0.9 for connectivity while the physical-sample gates remain open. J701 and J702 now use the maker-drawing maps recorded in that workbook. G-1/G-2 sample continuity and G-3 overlays must confirm the physical assignments before routing.

| Ref | Finding | Current capture | Required action |
| --- | --- | --- | --- |
| J101 | The [GCT USB4105 drawing](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5492/USB4105.pdf) gives 12 PCB solder lands: A1/B12, A4/B9, A5–A8, B1/A12, B4/A9, B5–B8; four shell-stake slots; and two 0.65 mm locating holes. JLCPCB C3020560 CAD splits the four shared lands into separate touching pads, giving 16 signal-pad IDs. | Workbook composite pad labels and nets are retained. `DAC_HPA:J101_USB4105-GF-A_12lands_4stakes` is a provisional footprint from the GCT layout, with all 16 named pads plus two unnumbered locating holes. Its four plated shell slots currently have no F.Paste apertures. | G-1 continuity on two samples, G-3 1:1 overlay, then confirm pin-in-paste process and apertures with JLCPCB at G-6. |
| J701 | The [G-Switch GT-3321667P-01 drawing](https://atta.szlcsc.com/upload/public/pdf/source/20210324/C2762984_895B09C838D8EF4D4228BF97BFC29634.pdf) maps pad 1 to GND, 2/3 to R−, 4/5 to R+, 6 to L−, and 7/8 to L+. Pads 9/10 are switch/detect contacts; 11/12 are mounting tabs. | Parts List v0.9 carries the approved 12-pad map. Pads 9–12 have no-connect flags, yet 11/12 retain solder lands. `DAC_HPA:J701_GT-3321667P-01_maker_slots` keeps the maker's 0.50 × 1.40 mm plated slots and pad centres, adds two Ø1.20 mm NPTH peg holes, and uses owner-approved 2.00 × 1.20 mm copper pads. | G-2 continuity on two samples must confirm all contacts and whether tabs 11/12 are common with sleeve or bushing; G-3 checks the revised copper, slot, hole and peg overlay. |
| J702 | The [HRO PJ-332A-6A drawing](https://datasheet.lcsc.com/datasheet/pdf/ae194aee17b3d1e2f10994958208a91f.pdf?productCode=C2848643) maps pad 1 to sleeve, 2 to ring 2, 3 to ring 1, 4 to tip, and 5/6 to break contacts. | Parts List v0.9 assigns 1/2 to GND, 3 to `JACK_RP`, 4 to `JACK_LP`, and 5/6 to no-connect. **Never connect 5/6 to GND:** with no plug, they close to the driven contacts. `DAC_HPA:J702_PJ-332A-6A_peg_holes` keeps the 0.60 × 1.50 mm slots and pad centres, enlarges the copper on pads 1/2 to 2.10 × 1.20 mm, and adds two Ø1.20 mm NPTH peg holes. | The owner reports both physical samples match the TRS contact and break maps; full G-2 record and any allowed TRRS plug check remain. G-3 overlays the revised copper, slots and pegs. JLCPCB confirms slot soldering at G-6. |

The workbook's internal clean check and KiCad ERC confirm capture consistency; neither verifies a connector's physical contact map. No manufacturing data follows from the provisional connector assignments.

## J701 correction approved and captured

| JLC/G-Switch pad | Published contact name | Captured DAC-HPA net |
| --- | --- | --- |
| 1 | GND | `GND` |
| 2, 3 | R− | `JACK_RN` on both |
| 4, 5 | R+ | `JACK_RP` on both |
| 6 | L− | `JACK_LN` |
| 7, 8 | L+ | `JACK_LP` on both |
| 9 | SWITCH | No-connect flag |
| 10 | DETECT | No-connect flag |
| 11, 12 | `ep` in JLC symbol; mounting tabs in maker drawing | No-connect flags; soldered lands; physical electrical role checked at G-2 |

The map is now present in Parts List v0.9 and captured without a J701 override. The two-sample G-2 check must still confirm the contact map and the electrical role of pads 11/12 before schematic freeze.

## Slot-pad copper ring decision

Design Spec v1.1 left the maker-pad copper rings open: J701 0.25 mm nominal and 0.20 mm at the +0.10 mm slot tolerance; J702 0.20 mm. On 27 September 2026, the owner chose to enlarge **copper only** before G-3. J701 pads are now 2.00 × 1.20 mm around the unchanged 1.40 × 0.50 mm slots, giving a 0.30 mm worst ring at the +0.10 mm slot width. J702 pads 1/2 are now 2.10 × 1.20 mm around unchanged 1.50 × 0.60 mm slots, also giving a 0.30 mm ring. Pad centres and locating holes stay fixed. The closest J701 copper-to-copper gap is 0.30 mm between pads 7 and 10. `verify_critical_footprints.py` checks the pad dimensions; G-3 must still verify the physical overlay and JLCPCB DFM must accept the revised lands and gap. The 0.30 mm result includes the stated slot-size tolerance, but not slot-to-copper registration error at fabrication. [JLCPCB's slot guidance](https://jlcpcb.com/blog/pcb-via-design-best-practices) prefers a copper width above 0.30 mm for long slots and notes 0.20 mm as a limit; its [general through-hole advice](https://jlcpcb.com/help/article/common-mistakes-when-using-altium-designer) gives >0.18 mm. This design uses ENIG and reaches 0.30 mm by geometry, pending JLCPCB's project-specific DFM review.

## J702 sample check reported by the owner

The owner reports that **both J702 samples** show pads 3–5 and 4–6 closed with no plug and open with the intended TRS plug fully inserted. With that plug inserted, pads 1/2 contact the sleeve, pad 3 the right ring, and pad 4 the left tip, with no other pad-to-contact connections. The owner decided that J702 supports **TRS plugs only**, so a TRRS contact test is outside the accepted use. Sample identifiers, raw DMM readings, shell continuity and an insertion sweep still belong in the full G-2 record; the gate is not signed off yet.

The owner also reports that **both J701 samples** match the intended 4.4 mm plug contacts: pad 1 sleeve, 2/3 R−, 4/5 R+, 6 L−, and 7/8 L+. The mounting-tab and switch/detect continuity, sample identifiers, raw readings and insertion sweep remain to be recorded before G-2 sign-off.

## G-2 continuity record to collect

On two samples of each jack, label the physical terminals using the JLC footprint top view. Record continuity from every terminal to tip, each ring, sleeve, and any metal shell with no plug, then with the intended plug fully inserted. Repeat while slowly inserting and removing the plug to identify detect/switch contacts. For J702, test the intended TRS plug; TRRS use is excluded by the owner's decision. Record any pair of terminals that are internally common. The resulting table determines the final symbol pin names, nets, and footprint pad assignments.
