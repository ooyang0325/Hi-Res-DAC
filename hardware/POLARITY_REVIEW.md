# D705/D706 LED polarity correction — approved and applied

The ordered LED part numbers still conflict with the pin map in Parts List v0.9 and Schematic Design Notes v1.0 Section 6 rule 53.
On 26 September 2026 the owner approved correcting the KiCad pad-to-net mapping to the manufacturer/JLC pinout. The workbook's LED rows remain as supplied; `generate_schematic.py` applies this explicit override on regeneration.

| Ref | Ordered part / JLC code | Manufacturer and JLC pin assignment | Original workbook assignment | Corrected KiCad assignment |
| --- | --- | --- | --- | --- |
| D705 | Hubei KENTO KT-0805G / C2297 | Pad 1 = anode (+), pad 2 = cathode (−) | Pad 1 = GND (called K); pad 2 = `N7_LEDG_A` (called A) | Pad 1 = `N7_LEDG_A`; pad 2 = GND |
| D706 | Hubei KENTO KT-0603R / C2286 | Pad 1 = anode (+), pad 2 = cathode (−) | Pad 1 = GND (called K); pad 2 = `N7_LEDR_A` (called A) | Pad 1 = `N7_LEDR_A`; pad 2 = GND |

Evidence: [KT-0805G manufacturer drawing](https://datasheet.lcsc.com/datasheet/pdf/de342fde3322df0797012cd7a04e2194.pdf?productCode=C2297), page 2, and [KT-0603R manufacturer drawing](https://datasheet.lcsc.com/datasheet/pdf/011ec3e8cb1e825f6961d29bc4db4c7a.pdf?productCode=C2286), page 2, mark terminal 1 with `+` and terminal 2 with `−`. The JLCPCB symbols supplied for C2297/C2286 independently label pin 1 `A` and pin 2 `K`; their footprint polarity stripe is at pad 2.

The original pad-number and ERC checks could not catch this reversal: the pad numbers matched even though the physical LED polarity was wrong. The approved correction keeps the specified LED MPNs and net functions. `verify_schematic.py` now asserts that **only** these four pin/net assignments differ from the workbook and that KiCad matches the corrected map. Other connector and physical gates still prevent PCBA release.
