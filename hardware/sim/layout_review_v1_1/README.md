# Layout review v1.1: PDN re-run on the reviewer's scripts

The v1.1 re-verification (`doc/DAC_HPA_Layout_Reverification_Evidence.zip`) adds U208 and a real-GND-path
check to the PDN study. These results come from those scripts, unchanged, run on the board after the
OD-14 fixes. The copper model is rebuilt from the board file with the reviewer's own parser. The evidence
code is not copied into the repository; `prepare.sh` lays it out (portable: no `sed`).

```bash
hardware/sim/layout_review_v1_1/prepare.sh doc/DAC_HPA_Layout_Reverification_Evidence.zip
cd hardware/sim/layout_review_v1_1/indrev2/power && python3 pdn_gndcheck_rev.py && python3 pdn_rev.py A && python3 pdn_rev.py B
```

| File | Script | Result |
| --- | --- | --- |
| `pdn_gndcheck_rev.json` | `power/pdn_gndcheck_rev.py` | Every decoupling cap's GND pad reaches a real, plane-connected GND via along F.Cu: C224 0.0 mm, C219 0.35 mm, C218 0.9 mm, U208 pin 4 0.5 mm |
| `results_pdn.json`, `results_pdn_transient.json` | `power/pdn_rev.py A` (method as is) | Supply spike for a 1 ns edge: U208.8 86.6 mV (was 377 mV); X201/X202/X203 59.7/61.9/54.6 mV; U201 pins 19/32/48/64 74.3/41.1/52.6/30.1 mV (unchanged) |
| `results_pdn_geodesic.json` | `power/pdn_rev.py B` (real GND path) | No pad needs the path correction (`fixed_pads_s_mm` is empty), so the numbers equal part A |

Summary: [LAYOUT_REVIEW_V1_1_RESPONSE_2026-10-14.md](../../LAYOUT_REVIEW_V1_1_RESPONSE_2026-10-14.md) §1.
