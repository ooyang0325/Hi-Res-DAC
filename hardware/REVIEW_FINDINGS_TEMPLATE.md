# DAC-HPA peer-review findings

Copy this file for each review response. Keep findings tied to a single Git revision and give enough location/evidence for another engineer to reproduce them.

| Review metadata | Entry |
| --- | --- |
| Reviewed Git commit SHA / branch |  |
| Reviewer and discipline |  |
| Review date |  |
| Files actually inspected |  |
| Scope not inspected |  |

## Disposition

| Area | Pass / issue / needs evidence / not reviewed | Evidence or finding IDs |
| --- | --- | --- |
| Schematic pin and net mapping |  |  |
| Power, clock, analog and protection behavior |  |  |
| Connector and polarized-part physical mapping (G-3/G-4) |  |  |
| Placement and simultaneous route feasibility |  |  |
| Ground returns, noise, crosstalk and EMI |  |  |
| JLCPCB fabrication and assembly |  |  |

**Overall recommendation for routing:** ☐ proceed with conditions ☐ hold for corrections ☐ needs more review. List the conditions or blockers: ________________________________________________.

## Findings

Use one block per issue. Severity: **blocker** means likely wrong electrical/physical behavior or impossible routing/assembly; **major** needs correction before layout freeze; **minor** can be resolved during layout; **question** needs evidence before disposition.

### Finding ID: ___ — short title

- **Severity / review area:**
- **Location:** schematic sheet/page and ref.pin/net, or PCB (x, y) mm, side/layer and references.
- **Expected condition and source:** design requirement, manufacturer pinout, calculation or JLC policy link/version.
- **Observed condition:** exact net/pad, dimension, route obstruction, waveform, DRC marker or image.
- **Why it matters:** failure mode or review consequence.
- **Reproduction / evidence:** KiCad measurement, screenshot, script output, datasheet page, sample ID or JLC response.
- **Suggested disposition:** concrete design change, route trial, physical measurement or owner decision.
- **Owner response / status:** open, accepted, rejected with reason, or closed with commit and retest evidence.

## Gate and decision follow-up

| Gate or decision | Evidence obtained | Still required | Responsible person |
| --- | --- | --- | --- |
| G-3 physical overlay and jack copper/pegs |  |  |  |
| G-4 polarity and pin-1 samples |  |  |  |
| J101/J702 plated-slot soldering and edge/panel approval |  |  |  |
| Provisional 7 mm I/V and 4.2 mm J701 ESD limits |  |  |  |
| MCLK TP711, timer, I²S, USB and output route feasibility |  |  |  |
| Audio/EMI return topology |  |  |  |

Keep an unmeasured condition as **needs evidence**. The G-1/G-2 raw connector log was explicitly waived for layout planning; do not infer that the separate G-3/G-4 physical gates passed. Record the reviewed SHA again if findings are carried into a later revision.
