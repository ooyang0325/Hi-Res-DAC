# Layout review v1.0 — re-verification on the reviewer's own solvers

The independent review (`doc/DAC_HPA_Independent_Layout_Review_v1.0.docx`) ships its solvers in
`doc/DAC_HPA_Independent_Review_Evidence.zip`. These wrappers run that code, unchanged, on the revised
board; the copper model is rebuilt from the board file with the reviewer's parser (`geometry/sexp.py`,
`geometry/model.py`). The evidence code is not copied into the repository; `prepare.sh` lays it out.

```bash
hardware/sim/layout_review_v1/prepare.sh doc/DAC_HPA_Independent_Review_Evidence.zip
```

| File | Study | Finding |
| --- | --- | --- |
| `verify_s2.py` → `detector_s2_results.json` | `analog/s2_mclk.py` MNA model with the as-built path lengths after block b25 (geometry `V2` in the wrapper) | T1 |
| `verify_si.py` → `link_si_results.json` | `si/sim_nets.py` transients of LINK_SCK/MOSI/FRAME through R247–R249 (27-corner factorial on SCK) | T2 |
| `verify_thermal.py` → `thermal_results.json` | `power/thermal_run.py` normal envelope and F1 (U503 1.24 W) states, as built | T4, R3 |
| `pw/power/pdn_transient.py` → `pdn_droop_results.json` | PDN droop at the U201 and X201–X203 supply pins (`..._reviewer_asrouted.json` is the reviewer's original) | T5, T6 |

Summary of the numbers: [LAYOUT_REVIEW_RESPONSE_2026-10-13.md](../../LAYOUT_REVIEW_RESPONSE_2026-10-13.md) §1.
