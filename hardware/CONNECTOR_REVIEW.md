# Connector pin-map review (capture v1.1)

The schematic follows Parts List v0.9 for connectivity while the physical-sample gates remain open. J701 and J702 now use the maker-drawing maps recorded in that workbook. G-1/G-2 sample continuity and G-3 overlays must confirm the physical assignments before routing.

| Ref | Finding | Current capture | Required action |
| --- | --- | --- | --- |
| J101 | The [GCT USB4105 drawing](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5492/USB4105.pdf) gives 12 PCB solder lands: A1/B12, A4/B9, A5–A8, B1/A12, B4/A9, B5–B8; four shell-stake slots; and two 0.65 mm locating holes. JLCPCB C3020560 CAD splits the four shared lands into separate touching pads, giving 16 signal-pad IDs. | Workbook composite pad labels and nets are retained. `DAC_HPA:J101_USB4105-GF-A_12lands_4stakes` is a provisional footprint from the GCT layout, with all 16 named pads plus two unnumbered locating holes. Its four plated shell slots currently have no F.Paste apertures. | G-1 continuity on two samples, G-3 1:1 overlay, then confirm pin-in-paste process and apertures with JLCPCB at G-6. |
| J701 | The [G-Switch GT-3321667P-01 drawing](https://atta.szlcsc.com/upload/public/pdf/source/20210324/C2762984_895B09C838D8EF4D4228BF97BFC29634.pdf) maps pad 1 to GND, 2/3 to R−, 4/5 to R+, 6 to L−, and 7/8 to L+. Pads 9/10 are switch/detect contacts; 11/12 are mounting tabs. | Parts List v0.9 carries the approved 12-pad map. Pads 9–12 have no-connect flags, yet 11/12 retain solder lands. `DAC_HPA:J701_GT-3321667P-01_maker_slots` uses the maker's 1.00 × 1.90 mm copper pads and 0.50 × 1.40 mm plated slots, with two Ø1.20 mm NPTH peg holes. | G-2 continuity on two samples must confirm all contacts and whether tabs 11/12 are common with sleeve or bushing; G-3 checks the hole and peg overlay. |
| J702 | The [HRO PJ-332A-6A drawing](https://datasheet.lcsc.com/datasheet/pdf/ae194aee17b3d1e2f10994958208a91f.pdf?productCode=C2848643) maps pad 1 to sleeve, 2 to ring 2, 3 to ring 1, 4 to tip, and 5/6 to break contacts. | Parts List v0.9 assigns 1/2 to GND, 3 to `JACK_RP`, 4 to `JACK_LP`, and 5/6 to no-connect. **Never connect 5/6 to GND:** with no plug, they close to the driven contacts. `DAC_HPA:J702_PJ-332A-6A_peg_holes` preserves the JLC signal lands and adds two Ø1.20 mm NPTH peg holes. | G-2 confirms the map and break-contact operation on two samples; G-3 overlays the slot and peg geometry. JLCPCB must confirm how plated slots 1/2 are soldered at G-6. |

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

## Slot-pad copper ring decision before G-3

The maker geometry gives J701 a 0.25 mm nominal ring around each plated slot, falling to 0.20 mm at the slot's +0.10 mm tolerance. J702 pads 1/2 have a 0.20 mm ring. Those clear the JLCPCB 0.18 mm minimum cited in Design Spec v1.1, but fall below this design's 0.30 mm rule. The owner has left this as an open G-3 decision. The current custom footprints keep the maker pad and slot sizes; `verify_critical_footprints.py` checks them. Do not widen the pads or shrink the slots without recording the decision and repeating the overlay.

## G-2 continuity record to collect

On two samples of each jack, label the physical terminals using the JLC footprint top view. Record continuity from every terminal to tip, each ring, sleeve, and any metal shell with no plug, then with the intended plug fully inserted. Repeat while slowly inserting and removing the plug to identify detect/switch contacts. For J702, test both the intended TRS and any TRRS plug configuration allowed by the design. Record any pair of terminals that are internally common. The resulting table determines the final symbol pin names, nets, and footprint pad assignments.
