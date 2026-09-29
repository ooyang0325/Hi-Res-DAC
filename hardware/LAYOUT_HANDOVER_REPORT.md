# DAC-HPA layout handover for engineering review

**Review snapshot:** 29 September 2026 · KiCad 10 · 120 × 100 mm, four layers. The layout geometry was last changed in commit [`e519cfff`](https://gitlab.com/ooyang0325/Hi-Res-DAC/-/commit/e519cffff5b0c42fc040a59689856114e9051202). Review the commit accompanying this report and record its full SHA before making findings. The [board checkpoint pipeline](https://gitlab.com/ooyang0325/Hi-Res-DAC/-/pipelines/2890924902) passed; its [review artifacts](https://gitlab.com/ooyang0325/Hi-Res-DAC/-/jobs/16790518018/artifacts/download) are available for 30 days. Later pipelines may contain this report and refreshed views.

**Release state: HOLD.** The [integrated study PCB](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb) is the current schematic-aligned layout review candidate. It is partial copper for engineering review, with **973 full ratsnest links still open**. It is not a Gerber, CPL, or JLCPCB PCBA order package. The [functional-ECO board](DAC_HPA_120x100_FUNCTIONAL_ECO_STUDY_ONLY.kicad_pcb) is the earlier placement baseline; `DAC_HPA.kicad_pcb`, the 100 × 80/100 × 100 mm boards, and the older macro studies are comparisons.

The current local checkout also contains uncommitted workbook and KiCad project-setting changes outside the pinned board revision. Review a clean checkout or the CI source archive, and run `git status --short` before treating local files as the reviewed design.

## Start the review

| Order | Open | Purpose |
| --- | --- | --- |
| 1 | [Reviewer start](REVIEWER_START_HERE.md), [nine-page schematic PDF](DAC_HPA_review_only.pdf), [schematic guide](SCHEMATIC_REVIEW_GUIDE.md) | Learn the signal chain and the v1.1-ECO1 pin map. Use [source reconciliation](SOURCE_RECONCILIATION.md) and the [functional ECO](FUNCTIONAL_ECO_2026-09-28.md) where the older Office set differs. |
| 2 | [Integrated PCB](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb), [route study](INTEGRATED_AUDIO_ROUTE_STUDY.md), [constraint disposition](CONSTRAINT_DISPOSITION_V2.md) | Inspect the actual partial routes, their returns, component access and the provisional limits. Compare the earlier functional-ECO board only when a placement change needs context. |
| 3 | [Placement review guide](PLACEMENT_REVIEW_GUIDE.md), [summary JSON](INTEGRATED_AUDIO_SUMMARY.json), [3D-model review](3D_MODEL_REVIEW.md) | Check the measured screens and their limits. The current board has 478 resolvable component bodies; four VRML film-capacitor envelopes show in KiCad's 3D Viewer but not the exported GLB. |
| 4 | [PCBA process review](PCBA_PROCESS_REVIEW.md), [JLC DFA/DFM rules](JLCPCB_DFA_DFM_RULES.md), [G-3 overlays](G3_OVERLAY_INDEX.md), [G-4 checklist](G4_POLARITY_CHECKLIST.md) | Separate physical sample and JLC order questions from KiCad geometry checks. |
| 5 | [Findings template](REVIEW_FINDINGS_TEMPLATE.md) | Return a disposition tied to the reviewed SHA, reference/pad/net, PCB coordinates and layer, evidence, and the action needed to close each issue. |

### Export and zoom into the PCB from a terminal

From the repository root, explicitly pass the **integrated** PCB. The script otherwise defaults to the older functional-ECO baseline:

```sh
git rev-parse HEAD
git status --short
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-hpa-integrated-review \
  hardware/DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb
```

On a KiCad 10 Linux installation, use `KICAD_CLI=kicad-cli`. Open `01_body_courtyard.svg`, `02_top_copper.svg`, `03_l2_ground.svg`, **`10_l3_power.svg`**, mirrored `07_bottom_copper.svg`, `08_board_3d.glb`, and `09_drc.json` in the output directory. The [CLI visual guide](PCB_CLI_VISUAL_REVIEW.md) explains mask, paste, legend, image tiling and the commands for rerunning the read-only audits. Inspect the L3 VPOS bridge together with L4, rather than inferring its coupling from the top plot. Open the PCB in KiCad's 3D Viewer for the film-capacitor envelopes omitted from GLB.

## What the present board establishes

| Checked fact | Current result and evidence boundary |
| --- | --- |
| Capture and geometry | 544 footprints, 250 named nets, 551 track/via items and one saved filled L2 GND polygon. The frozen [manual delta](INTEGRATED_AUDIO_MANUAL_DELTA.json) contains 81 footprint moves, four replaced source copper items and 520 added items; placement and waypoints were chosen manually. |
| Schematic and CAD checks | The pipeline verifies 34 documented workbook-to-schematic pin/net deltas, 0 ERC violations, pad/net identity and the manual board replay. The integrated board has **0 KiCad DRC violations**, but DRC reports **499** unconnected items and the full `pcbnew` ratsnest has **973** links. Clean partial DRC does not prove full-board routability. |
| Track shape | The integrated checker finds **0 exact 90° bends** and **0 free-copper 80–100° elbows**. It counts **eight** near-orthogonal joins at component pad centres; straight-through T/cross junctions are classified separately. Inspect both visually. |
| DAC and I/V | Four U301→U403/U404 input routes are 4.294/6.030/6.925/4.786 mm with no vias; DACR has only **0.075 mm** under the provisional 7 mm ceiling. Saved L2 lies beneath those routes at 0.01 mm centreline samples and ±0.05/0.10 mm offsets. The largest projected **2D** I/V feedback area is 4.875 mm². These screens do not extract stability or return impedance. |
| Output and ESD | Four amplifier legs reach their J701 contacts; LP/RP also branch to J702. Six named-pad TVS routes measure 3.255–4.03 mm against the provisional 4.2 mm limit. Loaded output impedance, ESD return and system tests remain open. |
| JLC/3D screens | The classified package/edge proxy and via-ring audit report zero findings. Of 463 JLC-placed references, **447** are classified by the package-spacing proxy and **16** need individual review. The model-path audit resolves 478 component bodies. None of these screens is JLC order approval or a physical fit measurement. |

The detailed measurements and conditional R-15 output-impedance model are in the [route study](INTEGRATED_AUDIO_ROUTE_STUDY.md) and [trace budget](INTEGRATED_AUDIO_TRACE_BUDGET.json). Treat those model values as planning estimates: the assumed 50 mΩ jack contact has no maker maximum, the 3.5 mm sleeve return is not extracted, and neither jack has a completed loaded measurement.

## Reviewer decisions to return

| Priority | Location and question | Evidence needed to close it |
| --- | --- | --- |
| 1 · Analog return and stability | U301 (90.5, 81), U403 (96.3, 77.2), U404 (96.3, 84.8). DACL's U403.6→C417.1 feedback branch lacks direct L2 under **1.9426 mm** of its centreline near the `N4_IVL_P` via at **(96.625, 78.170)**. The DACR input route is 6.925 mm, and VREF reaches 14.422 mm. Is the feedback, bypass and reference geometry acceptable after extraction? | Review the actual 3D feedback and return-current path, summing capacitance, VREF noise and I/V stability/step response. A new via or placement proposal must still pass the 7 mm DAC input screen, courtyard clearances and DRC. |
| 2 · Cross-layer audio and power | The `N4_IVR_P`→R409 feed is **47.752 mm**. L3 local VPOS crosses the two right I/V L4 feeds around **x = 115–121, y = 74–76 mm**. U501 is at **(72, 132)**; local copper exists but main VPOS/VNEG source feeds to U401/U402 and their exposed-pad thermal routes do not. | Co-route the rails and returns with the audio feeds, extract coupling and shared impedance, and test loaded stability, noise, THD+N and crosstalk. Examine U501 C510/C511 ground-via spacing of 8.160/6.767 mm as geometry, not an extracted loop length. |
| 3 · Remaining route feasibility | USB D+/D−, I²S, much of the power/protection network and most of the 973 ratsnest links remain. The timer's 7.91 mm Manhattan lower bound leaves little room under its 8 mm route rule. | Trial the USB 90 Ω pair against the quoted JLC stack-up, route I²S branches with L2 returns and skew checks, and draw timer/bleed/reset branches before accepting the placement. Demonstrate that critical paths coexist. |
| 4 · Connectors, DFA and JLC process | J701 (146.5, 76), J702 (150.84, 109.5), J101 (45, 75). J101 shell stakes and J702 plated slots 1/2 have **no F.Paste apertures**. J101 overhangs the left edge by 0.05 mm; J702 is 0.33 mm from the right edge. C423/C426 courtyard gaps are 0.150–0.194 mm. | Record G-3 1:1 physical overlays and remaining G-4 polarities; obtain JLC acceptance for slot soldering, enlarged lands, panel rails, mask and component access. Inspect the C437/J701/K602 corridor and 16 unclassified package references in the actual order preview. |
| 5 · Function and measured outputs | The all-rate post-CPLD capture/guard, DAC-side WS fault coverage, readback corners, attach current and system ESD are still qualification holds. R-15 depends on estimated contacts and an unextracted jack return. | Review [F01 capture proposal](MCU_SPI2_CAPTURE_ECO.md) as unimplemented, [pre-layout gates](PRELAYOUT_GATES.md), and the [PCBA process record](PCBA_PROCESS_REVIEW.md). Require operating firmware/RTL, fault tests, jack impedance measurements and ESD results before functional or order release. |

G-1/G-2 connector continuity reports were accepted by the owner for layout planning with the raw measurement log waived. **That waiver does not close G-3 footprint overlays or G-4 polarity checks.** The 3.5 mm output is for TRS plugs only; J702 pins 5/6 are unused break contacts and must remain unconnected. J701 switch pads 9/10 likewise remain unconnected in this candidate.

Return each finding as **pass**, **issue**, **needs evidence**, or **not reviewed** in the [findings template](REVIEW_FINDINGS_TEMPLATE.md). A proposal to change the board should cite the affected schematic/PCB net and controlled constraint, preserve the explicit manual route record, and rerun the integrated checker and GitLab pipeline. Do not use the historical automatic `place_board.py --force` flow to regenerate this manual candidate.
