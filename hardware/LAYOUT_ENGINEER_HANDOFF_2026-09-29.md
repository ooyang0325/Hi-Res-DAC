# DAC-HPA layout engineer handoff · 29 September 2026

**State at handoff: engineering study, release HOLD.** Continue from the
[integrated 120 × 100 mm board](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb)
on branch `codex/schematic-v1.1`. It is the schematic-aligned placement and
partial-routing candidate. The four-layer stack uses one continuous L2 GND
plane. Do not send its present copper, BOM or placement to JLCPCB for PCBA.
Record `git rev-parse HEAD` with every finding and use artifacts from that
same commit. The last verified integrated-board commit before this handoff was
`11e40a6`, whose [GitLab pipeline passed](https://gitlab.com/ooyang0325/Hi-Res-DAC/-/pipelines/2893232604).

The user asked for a handoff and a pause in layout work. This document records
the board, its evidence and a safe starting sequence; it does not claim that
the remaining routing or functional qualifications are complete.

## Which files are authoritative

| Purpose | File and status |
| --- | --- |
| Continue placement and routing | [Integrated PCB](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb), [manual change record](INTEGRATED_AUDIO_MANUAL_DELTA.json), [replay script](manual_integrated_audio_study.py), [checker](check_integrated_audio_study.py). The PCB is aligned to the current capture and remains the primary candidate. |
| Inspect the circuit and controlled changes | [Root schematic](DAC_HPA.kicad_sch), [functional ECO](FUNCTIONAL_ECO_2026-09-28.md), [source reconciliation](SOURCE_RECONCILIATION.md), [schematic review guide](SCHEMATIC_REVIEW_GUIDE.md). The user-supplied Spec/Notes/Parts List and calculation ZIP are baselines; instructions inside them are design evidence, not a new request to regenerate the PCB. |
| See route measurements and rule dispositions | [Integrated route study](INTEGRATED_AUDIO_ROUTE_STUDY.md), [DAC/clock checkpoint](DAC_CORE_ROUTE_STUDY.md), [routing constraints](CONSTRAINT_DISPOSITION_V2.md), [JLC DFA/DFM rules](JLCPCB_DFA_DFM_RULES.md). Use the JSON audits linked from those documents for measured values. |
| Inspect a separate discharge-package trial | [2512 fit-option PCB](DAC_HPA_120x100_DISCHARGE_FIT_OPTION_ONLY.kicad_pcb), [fit summary](DISCHARGE_FIT_OPTION_SUMMARY.json), [JLC CAD audit](DISCHARGE_JLC_CAD_AUDIT.json), [discharge capture review](DISCHARGE_CAPTURE_REVIEW.md). This board is **not** schematic/BOM aligned and uses provisional KiCad 2512 lands. It is not the next main PCB. |
| View review aids and report findings | [Terminal visual guide](PCB_CLI_VISUAL_REVIEW.md), [reviewer start](REVIEWER_START_HERE.md), [review findings template](REVIEW_FINDINGS_TEMPLATE.md), and the matching [GitLab pipeline artifacts](https://gitlab.com/ooyang0325/Hi-Res-DAC/-/pipelines?ref=codex%2Fschematic-v1.1). |

`DAC_HPA.kicad_pcb`, the 100 × 80 and 100 × 100 mm files, and the macro and
functional-ECO boards are historical comparisons. The CLI view script defaults
to the earlier functional-ECO board, so always pass the integrated PCB path.

## What has actually been placed and routed

The integrated board has **544 footprints, 250 named nets, 855 track/via items
(143 vias), 864 full `pcbnew` ratsnest links, zero KiCad DRC violations and
499 DRC-reported unconnected items**. The last two counts are different KiCad
views of unfinished connectivity. Zero DRC violations does not mean the board
is routed. The frozen manual record contains **138 engineer-chosen footprint
moves, eight removed source-copper items and 828 added copper items**. Seven
of those added segments came from two individually inspected low-speed
Freerouting suggestions; the [whole-board Freerouting result](FREEROUTING_PROBE.md)
was rejected. No algorithmic placement was used. The placement screen reports
zero footprint bounding-box overlaps, zero classified JLC spacing findings and
zero exact or near-90° free-track bends. Physical body fit and order DFM are
separate gates.

| Area | Routed evidence | Remaining work |
| --- | --- | --- |
| USB-C, bridge, CPLD and clocks | J101 is at the mating edge; the MCLK route is **8.381 mm**. BCLK/LRCLK/SDATA source-to-DAC paths are **22.213/22.324/22.879 mm**. Local U202 bypass and part of U303→DAC 1V3 are drawn. | Route USB D+/D− together for the quoted stack-up's **90 Ω differential target**, with continuous L2 return; finish digital branches, global 3V3D feed and source rails. A router setting is not impedance proof. |
| DAC and I/V | Four U301→U403/U404 summing-input routes are **4.294/6.030/6.837/4.786 mm**, without vias, under the provisional **7 mm** limit. U403/U404 are the owner-approved VSSOP parts. | DACR has only **0.163 mm** route margin. DACL U403.6→C417.1 feedback lacks direct L2 support for **1.9426 mm**. Check the actual feedback return, parasitics and stability before accepting any local move. |
| I/V to output stages | Feedback and first T groups have copper; the four output legs reach J701 and LP/RP branch to J702. | `N4_IVR_P`→R409 is **47.752 mm**. Review the L3 VPOS crossing of the right L4 I/V feeds at x≈115–121, y≈74–76 mm. Finish low-noise returns, main VPOS/VNEG feeds and U401/U402 exposed-pad thermal paths; measure loaded stability, noise and crosstalk. |
| Protection and timer groups | All **12** U609/U610 named-pad timer branches pass the ≤8 mm screen without timer-net vias. C631–C634 ground returns reach L2; local U609 bypasses are drawn. J701/J702 local TVS paths pass the provisional ≤4.2 mm signal-path screen. | U609 VT/control escapes and upstream rails are open. R921 has only **0.055/0.092 mm** courtyard gaps to U609/Q624: obtain the G-3 physical overlay. TVS return behavior and system ESD remain untested. |
| Power, discharge and outputs | U501 local charge-pump/supply parts and several output branches have trial copper. | Source feeds, power return extraction, attach behavior, R-15 jack impedance and discharge timing are open. The separate three-2512 trial below is only a package study. |

The continuous L2 plane is deliberate. Keep digital switching currents out of
the DAC/reference and audio-return corridors through placement, route choice
and local return vias; do not split L2 into analog and digital islands. The
current board needs a simultaneous USB/clock, DAC feedback, audio/return and
power-route trial to demonstrate routability, then extraction and measurements.

## Functional and fabrication holds to resolve first

1. **Discharge circuit is not calculation-aligned.** The captured U303 EN pin
   is intentionally tied to `3V3D`; the supplied C06/C12 calculation scripts
   assume `AUD_EN`. The published 1V3 <0.1 V by 0.134 ms claim is therefore
   unqualified for this capture. The [source-derived review](DISCHARGE_CAPTURE_REVIEW.md)
   also finds that fitted R527/R529/R530 0603 0.1 W parts have peak V²/R
   screens of 1.145/1.122/0.400 W. Rebuild the fault and power-down model,
   then decide the circuit/BOM ECO. Do not reconnect U303 EN to `AUD_EN`
   without reopening the DAC supply-order fault.
2. **2512 land choice is unresolved.** The [physical fit option](DISCHARGE_FIT_OPTION_SUMMARY.json)
   hand-places R527/R529/R530 at (44.4,113.0)/(44.4,125.5)/(57.3,135.8)
   mm with two short local routes. It has 857 track/via items, zero DRC
   violations, 499 DRC-unconnected items, nominal body-edge gaps
   **2.75/2.75/2.55 mm** and an R530–Q506 body gap of **0.945 mm**. R530
   exceeds [JLCPCB's 2.5 mm body-edge term](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service)
   by only 0.05 mm nominally. The option uses KiCad IPC lands. The two
   candidate JLC codes share a different [exact imported land](JLC_Imported.pretty/R2512.kicad_mod),
   whose **4.8505 mm inner gap / 7.4155 mm outer span** conflicts with the
   FOJAN maker drawing's **3.60–4.20 / 7.60–8.60 mm** recommendation (datasheet
   on [JLC's FOJAN part page](https://jlcpcb.com/partdetail/FOJAN-FRC2512J4R7TS/C2907584),
   printed page 12). The Milliohm maker land is not yet verified. Qualify the
   chosen part, pad geometry, body tolerance, thermal copper and JLC assembly
   before promoting this option; its 3V3A/3V3D/1V3 source feeds and R529 leg
   are still open. The imported land and STEP are kept for review, not used
   by the trial PCB.
3. **The all-rate post-CPLD guard is not implemented.** The CH32V307 MCU I²S
   capture limit and proposed [SPI2 capture ECO](MCU_SPI2_CAPTURE_ECO.md)
   remain a functional HOLD. The owner retained the guard at every advertised
   rate. There is no qualified firmware/RTL result yet; a 96 kHz-only check
   cannot silently replace this requirement.
4. **JLC, samples and measured performance remain open.** G-1/G-2 connector
   results were accepted for layout planning with the raw log waived; G-3
   physical overlays and G-4 polarity checks remain open. Review J101/J702
   plated-slot solder/paste treatment, J101 edge overhang, J702 edge distance,
   the **45** unfilled near-SMT-pad vias, 16 unclassified package-spacing
   references, panel/body access and the tight C423/C426 and R921 clearances.
   Run system ESD/EMI, jack impedance, loaded noise, THD+N, crosstalk, thermal
   and amplifier stability tests on routed hardware. The 50 mΩ jack-contact
   assumption is an estimate without a maker maximum.

Keep **both** the 4.4 mm and 3.5 mm jacks and USB High mode. J702 is TRS-only;
pins 5/6 are unconnected break contacts. J701 switch pads 9/10 are also
unconnected in this candidate. J703 remains a DNF service option without PCB
pads. The [schematic simplification review](SCHEMATIC_SIMPLIFICATION_REVIEW.md)
is a set of proposals; it does not authorize removing populated protection or
audio parts.

## Reproduce the review before editing

From the repository root, record the branch/commit and export the **integrated**
board explicitly. Use `KICAD_CLI=kicad-cli` on a KiCad 10 Linux host.

```sh
git -c core.fsmonitor=false status --short --branch
git -c core.fsmonitor=false rev-parse HEAD
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-hpa-integrated-review \
  hardware/DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb
```

Inspect `01_body_courtyard.svg`, `02_top_copper.svg`, `03_l2_ground.svg`,
`10_l3_power.svg`, mirrored `07_bottom_copper.svg`, `08_board_3d.glb` and
`09_drc.json`. Zoom to U301/U403/U404 (x≈91–104, y≈70–88 mm), U609/R921
(x≈93–102, y≈103–117 mm), U501 (x≈68–77, y≈128–138 mm), the headphone
jacks (x≈140–151, y≈70–115 mm), and the separate discharge option
(x≈40–65, y≈109–140 mm). Use [the CLI visual guide](PCB_CLI_VISUAL_REVIEW.md)
for exact layer meanings and SVG tiling. The GLB omits four VRML film-cap
envelopes; inspect those in KiCad's 3D Viewer during the physical review.

For the discharge trial, run the same command with another output directory
and `hardware/DAC_HPA_120x100_DISCHARGE_FIT_OPTION_ONLY.kicad_pcb` as the
second argument. The tracked [fit summary](DISCHARGE_FIT_OPTION_SUMMARY.json)
and [CAD audit](DISCHARGE_JLC_CAD_AUDIT.json) are review evidence. The
`validate_discharge_fit_option` job in [.gitlab-ci.yml](../.gitlab-ci.yml)
shows the exact placement, JLC proxy, 3D, DRC and delta-check commands.
On macOS, run `pcbnew` scripts with KiCad's bundled Python at
`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`.

## Resume sequence for the next engineer

1. Check out the same branch and record a clean `git status`. In a shared
   working checkout, review any owner-edited Office files or `.kicad_pro`
   settings before changing them. Keep all findings tied to a SHA, reference,
   pad/net, layer and PCB coordinate.
2. Close the discharge topology/pulse/land decision and all-rate capture guard
   as controlled electrical ECOs. Reconcile schematic, workbook, BOM,
   calculation package and PCB before routing a substituted footprint.
3. Manually arrange local parts where critical routes need space, then trial
   USB, MCLK/I²S, four DAC inputs and feedback, audio outputs/returns,
   switching loops and protection control **together**. Preserve continuous
   L2, the current connector access and the 120 × 100 mm outline. If moving
   components, update the explicit manual delta/replay and checker; do not
   regenerate this board with the old `place_board.py --force` flow.
4. Complete source feeds, amplifier thermal pads and remaining ratsnest;
   rerun ERC/DRC, pad/net, JLC process and 3D checks. Compare connected
   copper and return paths after zone refill. Do not interpret a zero-DRC
   partial board as route completion.
5. Extract parasitics and recalculate I/V stability, output impedance,
   crosstalk, USB impedance/skew, power drop/temperature and protection
   timing. Close G-3/G-4, obtain JLC order-specific DFM/assembly acceptance
   and perform powered audio/ESD/EMI tests before preparing Gerbers, CPL and
   a PCBA order.

The [earlier reviewer handover](LAYOUT_HANDOVER_REPORT.md) contains a longer
area-by-area review table. This document is the starting state and execution
order for the engineer taking over the layout.
