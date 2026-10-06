# G-1/G-2 physical continuity record — design set v1.1

**Disposition (27 September 2026):** after reporting two-sample checks, the owner explicitly instructed us to skip the G-1/G-2 measurement log. The results in `PRELAYOUT_GATES.md` are owner-accepted for layout planning, with sample IDs, raw readings and signature waived. This worksheet preserves the original Design Spec v1.1 protocol if the checks are ever repeated; blank cells are not recorded passes. Label pads from the **PCB top view** in the G-3 overlay. J702 is for TRS plugs only.

## G-1 — J101 USB4105-GF-A

Sample 1 ID: __________. Sample 2 ID: __________. Type-C breakout plug/cable ID: __________.

For each sample, test each composite land with the plug in both orientations. Expected common lands and net assignments:

| GCT land(s) | Expected contact/net | Sample 1 normal / flipped, reading | Sample 2 normal / flipped, reading |
| --- | --- | --- | --- |
| A1/B12 and B1/A12 | GND; each shared physical land's two JLC pad IDs on GND |  |  |
| A4/B9 and B4/A9 | VBUS; each shared physical land's two JLC pad IDs on VBUS |  |  |
| A5 / B5 | CC1 / CC2 respectively |  |  |
| A6 / B6 | D+ / D+ |  |  |
| A7 / B7 | D− / D− |  |  |
| A8 / B8 | SBU; no-connect in this design |  |  |
| S1–S4 | Metal shell; isolated from every internal GND contact inside the connector |  |  |

Owner reports both samples fully match this map, including both orientations. The table above is not yet a signed measurement log. Any short from shell to an internal GND contact, or any swapped/missing contact, fails G-1.

## G-2 — J701 GT-3321667P-01

Sample 1 ID: __________. Sample 2 ID: __________. Intended 4.4 mm plug ID: __________.

| Physical pad(s) | Expected contact/state | Sample 1 reading, no plug / inserted / slow sweep | Sample 2 reading, no plug / inserted / slow sweep |
| --- | --- | --- | --- |
| 1 | Sleeve / GND |  |  |
| 2, 3 | R− |  |  |
| 4, 5 | R+ |  |  |
| 6 | L− |  |  |
| 7, 8 | L+ |  |  |
| 9↔10 | Short without plug; open fully inserted; change state during insertion/removal. Each pad remains isolated from audio pads 1–8. Both are no-connect in KiCad. |  |  |
| 11↔12; each ↔ bushing; each ↔ pad 1 | Short to each other and bushing; open to sleeve pad 1. Both mounting pads are no-connect in KiCad. |  |  |

Owner reports both samples match the audio map, switch and bushing behavior. Record all other internally common terminal pairs and any temporary contact during the slow sweep: _______________________________________________.

## G-2 — J702 PJ-332A-6A

Sample 1 ID: __________. Sample 2 ID: __________. Intended TRS plug ID: __________.

| Physical pad(s) | Expected contact/state | Sample 1 reading, no plug / inserted / slow sweep | Sample 2 reading, no plug / inserted / slow sweep |
| --- | --- | --- | --- |
| 1, 2 | Sleeve / GND with TRS inserted |  |  |
| 3 | Right ring / `JACK_RP` |  |  |
| 4 | Left tip / `JACK_LP` |  |  |
| 3↔5 | Short without plug; open fully inserted. Pad 5 is no-connect in KiCad. |  |  |
| 4↔6 | Short without plug; open fully inserted. Pad 6 is no-connect in KiCad. |  |  |
| 5/6 ↔ sleeve or opposite channel | Open, including during insertion/removal |  |  |
| Metal shell ↔ pads 1–6 | Not applicable: owner reports no accessible metal shell on either J702 sample. | N/A | N/A |

Owner reports both samples match the endpoint TRS and break-contact map, and both insertion/removal sweeps show only the expected break-pair transitions without pads 5/6 contacting sleeve or the opposite channel. Record all internally common terminal pairs and any temporary contact during slow insertion/removal: _______________________________________________.

Optional future repeat: G-1 result ☐ pass ☐ fail; G-2 result ☐ pass ☐ fail. Measurement date: __________. Reviewer/signature: ____________________.

Any later discovered deviation requires schematic/footprint correction before routing. A passing ERC or netlist comparison does not verify the physical contacts.
