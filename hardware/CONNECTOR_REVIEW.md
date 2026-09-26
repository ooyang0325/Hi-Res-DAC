# Connector pin-map review (capture v1.0)

The schematic follows Parts List v0.8 for connectivity while the physical-sample gates remain open. The exceptions and conflicts below must be resolved before schematic freeze or routing.

| Ref | Finding | Current capture | Required action |
| --- | --- | --- | --- |
| J101 | The [GCT USB4105 drawing](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5492/USB4105.pdf) gives 12 PCB solder lands: A1/B12, A4/B9, A5–A8, B1/A12, B4/A9, B5–B8; four shell-stake slots; and two 0.65 mm locating holes. JLCPCB C3020560 CAD splits the four shared lands into separate touching pads, giving 16 signal-pad IDs. | Workbook composite pad labels and nets are retained. `DAC_HPA:J101_USB4105-GF-A_12lands_4stakes` is a provisional footprint from the GCTa layout, with all 16 named pads plus two unnumbered locating holes. Its four plated shell slots currently have no F.Paste apertures. | G-1 continuity on two samples, G-3 1:1 overlay, then confirm pin-in-paste process and apertures with JLCPCB at G-6. |
| J701 | The [G-Switch GT-3321667P-01 drawing](https://atta.szlcsc.com/upload/public/pdf/source/20210324/C2762984_895B09C838D8EF4D4228BF97BFC29634.pdf) names pin 1 GND, 2/3 R−, 4/5 R+, 6 L−, 7/8 L+, 9 switch, and 10 detect. JLCPCB C2762984 CAD has 12 numbered pads; its symbol calls 11/12 `ep`, without an established electrical role. The workbook has seven pins, with pin 1 assigned L+. | On 26 September 2026 the owner approved the 12-pad manufacturer/JLC map shown below. The KiCad symbol now uses it and is assigned `JLC_Imported:AUDIO-TH_GT-3321667P-01`; pads 9–12 are retained without nets. The original workbook is preserved. | Measure hole and peg dimensions and perform G-2 continuity on two samples; confirm the role of pads 11/12 before schematic freeze. |
| J702 | The [HRO PJ-332A-6A drawing](https://datasheet.lcsc.com/datasheet/pdf/ae194aee17b3d1e2f10994958208a91f.pdf?productCode=C2848643) shows a six-terminal contact/switch network for the A variant. It does not identify pins 5/6 as GND-only mounting pads as the workbook assumes. JLCPCB C2848643 CAD has six numbered pads but generic pin names, so it does not resolve the audio contact map. Its pads 1/2 are plated through-hole slots without F.Paste apertures; pads 3–6 are surface lands, although the workbook calls J702 SMD. | Workbook six-pin map and the JLCPCB candidate footprint remain provisional. | G-2 continuity of tip/rings/sleeve and switch states on two samples, then revise nets before routing. Confirm with JLCPCB how pads 1/2 are soldered in its Standard PCBA process before order. |

The workbook's internal clean check and KiCad ERC confirm capture consistency; neither verifies a connector's physical contact map. Do not generate manufacturing data from the provisional connector assignments.

## J701 correction approved and captured

| JLC/G-Switch pad | Published contact name | Proposed DAC-HPA net |
| --- | --- | --- |
| 1 | GND | `GND` |
| 2, 3 | R− | `JACK_RN` on both |
| 4, 5 | R+ | `JACK_RP` on both |
| 6 | L− | `JACK_LN` |
| 7, 8 | L+ | `JACK_LP` on both |
| 9 | SWITCH | No connection unless the detect circuit is needed |
| 10 | DETECT | No connection unless the detect circuit is needed |
| 11, 12 | `ep` in JLC symbol | No connection until their physical role is confirmed |

This replaces the workbook's seven-pad J701 map in KiCad, including its incorrect `JACK_LP` assignment on physical pad 1. `generate_schematic.py` applies the owner-approved override and `verify_schematic.py` lists all approved differences. The two-sample G-2 check must still confirm the contact map and the electrical role of pads 11/12 before schematic freeze.

## G-2 continuity record to collect

On two samples of each jack, label the physical terminals using the JLC footprint top view. Record continuity from every terminal to tip, each ring, sleeve, and any metal shell with no plug, then with the intended plug fully inserted. Repeat while slowly inserting and removing the plug to identify detect/switch contacts. For J702, test both the intended TRS and any TRRS plug configuration allowed by the design. Record any pair of terminals that are internally common. The resulting table determines the final symbol pin names, nets, and footprint pad assignments.
