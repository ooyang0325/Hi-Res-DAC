# G-4 polarity and pin-1 record — design set v1.1

Check two physical samples of each applicable part against tape-pocket/body marks, the maker pinout, the KiCad footprint and the captured net. Use a DMM diode test where applicable; use markings and pin mapping for capacitors and ICs. Enter sample IDs, readings and reviewer before G-4 passes. `POLARITY_REVIEW.md` records the owner-approved D705/D706 correction; those LEDs have **physical pad 1 = anode and pad 2 = cathode** even though the versioned Notes §9.6 still state the earlier reversed LED expectation.

| Part(s) | Required physical check | Sample IDs / actual readings / result |
| --- | --- | --- |
| D705, D706 | Owner reports diode tests on two samples each: pad 1 anode (+), pad 2 cathode (−). Record raw readings and tape/body marks. |  |
| D405–D408 BAT54S | Pin-1 and diode junction orientation match the KiCad pad/net map. |  |
| D102 SMDJ12A | Cathode band faces VBUS; part is owner-fitted before first USB plug-in. |  |
| D104, D105 | Pin 1 A matches regulator OUT in the netlist. |  |
| D411, D412 | Cathode band matches D411 → `N4_VPOS_IV`, D412 → `VNEG`. |  |
| D609, D610 | Diode junction/pin-1 match the captured pin map; D609 pin 1 a1 = GND. |  |
| C442, C443 | Positive band: C442 + → `N4_VPOS_IV`; C443 + → GND. |  |
| K601–K604 | Physical pin 1 matches owner-fitted land and silkscreen mark. |  |
| X201–X203 | Physical pin 1 matches each 2520 land and placement orientation; include X201 second source. |  |
| U206, U208 | Pin-1 body/tape marks match footprints and captured pin 1. |  |
| U605–U607 | Pin-1 body/tape marks match footprints and captured pin 1. |  |
| U608–U620 | Pin-1 body/tape marks match footprints and captured pin 1; U613–U620 use TI DGK. |  |
| Q623–Q627 | Pin 1 base, pin 3 collector, matching the onsemi MMBT3904LT1G SOT-23 land and netlist. |  |

Also inspect JLCPCB's 3D placement preview for these polarities at order review. Silkscreen pin-1/polarity marks are checked again on the placed board before the G-5 freeze.

G-4 result: ☐ pass ☐ fail. Measurement date: __________. Reviewer/signature: ____________________.
