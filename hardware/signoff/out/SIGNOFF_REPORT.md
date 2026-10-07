# Independent layout sign-off report

- Board: `DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb`
- Extracted with KiCad 10.0.6
- Copper layers: 6 (F.Cu, GND, PWR, SIG, GND5, B.Cu)
- Footprints 544, pads 1476, tracks 5139, vias 1524, nets 253
- Layer stack: ASSUMED (1.6 mm board)

## Verdict: FAIL

5 gate(s) FAIL, 10 WARN, 4 PASS, 0 informational.

## Gate summary

| Gate | Status | Title | FAIL | WARN |
| --- | --- | --- | ---: | ---: |
| G01 | **WARN** | Fabricator process window | 0 | 1 |
| G02 | **PASS** | Electrical clearance (IPC-2221B) | 0 | 0 |
| G03 | **WARN** | Plated-hole geometry (IPC-6012) | 0 | 1 |
| G04 | **PASS** | Assembly geometry (IPC-7351B) | 0 | 0 |
| G05 | **FAIL** | Fabrication documentation | 2 | 1 |
| G06 | **FAIL** | Drill-to-copper clearance | 1 | 0 |
| G10 | **FAIL** | Conductor ampacity (IPC-2221B) | 2 | 4 |
| G11 | **WARN** | Via ampacity | 0 | 3 |
| G12 | **PASS** | DC IR drop (solved) | 0 | 0 |
| G13 | **WARN** | Decoupling placement and mounted resonance | 0 | 48 |
| G20 | **FAIL** | USB high-speed differential pair | 1 | 2 |
| G21 | **WARN** | Clock routing and aggressor spacing | 0 | 1 |
| G22 | **WARN** | Return path and reference continuity | 0 | 1 |
| G23 | **PASS** | Switching-node keep-out | 0 | 0 |
| G30 | **WARN** | Headphone output path resistance and channel matching | 0 | 3 |
| G31 | **WARN** | I/V and feedback loop geometry | 0 | 2 |
| G32 | **WARN** | External port ESD protection | 0 | 1 |
| G40 | **FAIL** | Power distribution network impedance (LTspice) | 1 | 1 |
| G41 | **WARN** | Headphone output loading and damping (LTspice) | 0 | 1 |

## Gate detail

### G01 — Fabricator process window · WARN

**Criterion.** Every drawn feature is inside the JLCPCB multilayer process window, with the surcharge-free and recommended values treated as warnings.

**Sources.** JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com

**Metrics.**

- `track_width_histogram_mm` = {'0.15': 1024, '0.16': 30, '0.2': 2517, '0.25': 370, '0.3': 443, '0.4': 361, '0.5': 162, '0.6': 41, '0.8': 61, '1.0': 110, '1.2': 14, '1.5': 6}
- `min_track_width_mm` = 0.15
- `via_specs` = {'0.5/0.2': 133, '0.6/0.2': 1330, '0.7/0.3': 43, '0.8/0.4': 18}
- `via_count` = 1524
- `min_hole_to_hole_mm` = 0.2827
- `min_hole_to_hole_between` = ['via@[98.25, 46.42]', 'via@[97.78, 46.53]']
- `min_copper_to_edge_mm` = 0.58
- `min_copper_to_edge_at` = via GND @ [65.92, 139.12]
- `npth_count` = 6
- `min_silk_stroke_mm` = 0.1

**Findings.**

- `WARN` **SILK_LINE_THIN** — 907 silkscreen stroke(s) below 0.15 mm (thinnest 0.1 mm); these may not render.

_1 informational finding(s) in the JSON result._

### G02 — Electrical clearance (IPC-2221B) · PASS

**Criterion.** Every net class enforces at least the IPC-2221B Table 6-1 clearance for the worst-case peak potential across the gap, and at least the fabricator's etch minimum.

**Sources.** IPC-2221B Table 6-1 (electrical conductor spacing); JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com

**Assumptions.**

- Worst-case conductor pair is VPOS (+15 V) against VNEG (-15 V) = 30 V peak; no mains or high-voltage net is present.
- Soldermask is treated as a permanent polymer coating (IPC-2221B column B4) for external layers; exposed pads and test points fall back to B2.

**Metrics.**

- `worst_case_delta_v` = 30.0
- `ipc2221_required_mm` = {'internal_B1': 0.05, 'external_coated_B4': 0.05, 'external_uncoated_B2': 0.1}
- `governing_minimum_mm` = 0.09
- `board_min_clearance_rule_mm` = 0.15
- `netclass_clearances_mm` = {'Default': 0.2, 'USB_DIFF': 0.15, 'POWER': 0.2, 'AUDIO_OUTPUT': 0.2, 'FINE_ESCAPE': 0.15}

### G03 — Plated-hole geometry (IPC-6012) · WARN

**Criterion.** Annular ring meets IPC-6012 Class 2 and the fabricator minimum; drill aspect ratio stays inside the plating window.

**Sources.** IPC-6012 (qualification and performance, rigid boards); JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com

**Metrics.**

- `board_thickness_mm` = 1.6
- `worst_via_aspect_ratio` = 8.0
- `worst_via_aspect_drill_mm` = 0.2
- `min_via_annular_ring_mm` = 0.15
- `min_pth_annular_ring_mm` = 0.27
- `min_pth_annular_at` = J101.S1

**Findings.**

- `WARN` **ASPECT_RATIO_TIGHT** — 1463 via(s) sit at or above 8.0:1 aspect ratio (1.6 mm board). Barrel plating thickness must be confirmed with the fabricator.

### G04 — Assembly geometry (IPC-7351B) · PASS

**Criterion.** Component courtyards do not overlap and nothing intrudes on the board edge keepout.

**Sources.** IPC-7351B (land pattern and courtyard requirements)

**Metrics.**

- `footprints_total` = 544
- `footprints_with_courtyard` = 487
- `courtyard_overlap_pairs` = 0

### G05 — Fabrication documentation · FAIL

**Criterion.** The board carries the data a fabricator needs to build it to spec: a defined stackup, an impedance specification for any controlled-impedance net class, and a readable legend.

**Sources.** JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com; IPC-2581 / IPC-D-325 fabrication data requirements

**Metrics.**

- `copper_layers` = ['F.Cu', 'GND', 'PWR', 'SIG', 'GND5', 'B.Cu']
- `copper_layer_count` = 6
- `stackup_defined` = False
- `differential_netclasses` = ['AUDIO_OUTPUT', 'POWER', 'USB_DIFF']
- `silkscreen_text_items` = 0
- `silkscreen_items` = 1381
- `fiducial_candidates` = ['FID1', 'FID4', 'FID7', 'FID3', 'FID6', 'FID2', 'FID5']

**Findings.**

- `FAIL` **NO_STACKUP** — No physical stackup is defined for this 6-layer board. Dielectric heights, copper weights and the impedance build are left to the fabricator, so no controlled-impedance target can be held and the inner-layer copper weight that the ampacity and IR-drop results depend on is unconfirmed.
- `FAIL` **IMPEDANCE_UNSPECIFIABLE** — Net class(es) ['AUDIO_OUTPUT', 'POWER', 'USB_DIFF'] are routed as differential pairs but no stackup exists to specify their impedance to the fabricator.
- `WARN` **NO_SILK_REFDES** — No reference designators are printed on the silkscreen. The assembled board cannot be inspected, reworked or serviced against the schematic without a separate assembly drawing.

### G06 — Drill-to-copper clearance · FAIL

**Criterion.** Every drilled hole keeps the fabricator's minimum clearance to copper it is not connected to, so the drill tolerance cannot break out into a neighbouring net.

**Sources.** JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com; IPC-6012 (qualification and performance, rigid boards)

**Assumptions.**

- Drill and copper are compared at their drawn positions; the fabricator's drill registration tolerance is additional to this gap.

**Metrics.**

- `hole_to_copper_limit_mm` = 0.28
- `min_hole_to_copper_mm` = 0.1301
- `min_hole_to_copper_between` = ['J101.', 'J101.A1/B12', 'F.Cu']

**Findings.**

- `FAIL` **HOLE_TO_COPPER** — 4 hole/copper pair(s) are closer than the 0.28 mm drill-to-copper minimum; the drill can break out into copper it is not connected to.

### G10 — Conductor ampacity (IPC-2221B) · FAIL

**Criterion.** Every power conductor is wide enough to carry its budgeted DC current at a 10 K rise, on the layer it is drawn on.

**Sources.** IPC-2221B eq. 6-4, I = k*dT^0.44*A^0.725 (k=0.048 external, 0.024 internal); IPC-2152 (current capacity; 2221 retained as the conservative floor)

**Assumptions.**

- Copper weights assumed 1.0 oz outer / 0.5 oz inner (fabricator default); no stackup is defined on the board.
- DC current budgets are the declared values in design_intent.RAILS and are upper bounds, not measurements.

**Metrics.**

- `delta_t_k` = 10.0
- `layer_copper_mm` = {'F.Cu': 0.03472, 'GND': 0.01736, 'PWR': 0.01736, 'SIG': 0.01736, 'GND5': 0.01736, 'B.Cu': 0.03472}
- `rails` = {'VBUS': {'budget_a': 0.5, 'narrowest_mm': 1.0, 'layer': 'PWR', 'required_mm': 0.6056, 'capacity_a': 0.7193, 'margin_x': 1.439, 'capacity_at_double_copper_a': 1.1889}, 'VBUS_SENSE': {'budget_a': 0.001, 'narrowest_mm': 0.15, 'layer': 'F.Cu', 'required_mm': 0.0, 'capacity_a': 0.601, 'margin_x': 600.951, 'capacity_at_double_copper_a': None}, '5V_SYS': {'budget_a': 0.5, 'narrowest_mm': 1.0, 'layer': 'PWR', 'required_mm': 0.6056, 'capacity_a': 0.7193, 'margin_x': 1.439, 'capacity_at_double_copper_a': 1.1889}, '5V_ANA': {'budget_a': 0.3, 'narrowest_mm': 0.8, 'layer': 'PWR', 'required_mm': 0.2993, 'capacity_a': 0.6118, 'margin_x': 2.039, 'capacity_at_double_copper_a': 1.0112}, '5V_ANA_F': {'budget_a': 0.3, 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0575, 'capacity_a': 0.7403, 'margin_x': 2.468, 'capacity_at_double_copper_a': None}, 'VPOS': {'budget_a': 0.4, 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.4451, 'capacity_a': 0.3005, 'margin_x': 0.751, 'capacity_at_double_copper_a': 0.4967}, 'VNEG': {'budget_a': 0.4, 'narrowest_mm': 0.2, 'layer': 'PWR', 'required_mm': 0.4451, 'capacity_a': 0.2239, 'margin_x': 0.56, 'capacity_at_double_copper_a': 0.3701}, 'N4_VPOS_IV': {'budget_a': 0.1, 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0126, 'capacity_a': 0.7403, 'margin_x': 7.403, 'capacity_at_double_copper_a': None}, 'N4_VNEG_IV': {'budget_a': 0.1, 'narrowest_mm': 0.25, 'layer': 'PWR', 'required_mm': 0.0658, 'capacity_a': 0.2633, 'margin_x': 2.633, 'capacity_at_double_copper_a': 0.4352}, '3V3D': {'budget_a': 0.25, 'narrowest_mm': 0.4, 'layer': 'PWR', 'required_mm': 0.2328, 'capacity_a': 0.3702, 'margin_x': 1.481, 'capacity_at_double_copper_a': 0.6119}, '3V3A': {'budget_a': 0.1, 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0658, 'capacity_a': 0.3005, 'margin_x': 3.005, 'capacity_at_double_copper_a': 0.4967}, '3V3M': {'budget_a': 0.1, 'narrowest_mm': 0.4, 'layer': 'PWR', 'required_mm': 0.0658, 'capacity_a': 0.3702, 'margin_x': 3.702, 'capacity_at_double_copper_a': 0.6119}, 'N2_V33_CPLD': {'budget_a': 0.1, 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0658, 'capacity_a': 0.3005, 'margin_x': 3.005, 'capacity_at_double_copper_a': 0.4967}, 'N2_J201_3V3': {'budget_a': 0.05, 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0049, 'capacity_a': 0.7403, 'margin_x': 14.806, 'capacity_at_double_copper_a': None}, '1V3': {'budget_a': 0.3, 'narrowest_mm': 0.4, 'layer': 'PWR', 'required_mm': 0.2993, 'capacity_a': 0.3702, 'margin_x': 1.234, 'capacity_at_double_copper_a': 0.6119}, 'DVCC': {'budget_a': 0.1, 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0658, 'capacity_a': 0.3005, 'margin_x': 3.005, 'capacity_at_double_copper_a': 0.4967}, 'VCCA': {'budget_a': 0.05, 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0253, 'capacity_a': 0.3005, 'margin_x': 6.01, 'capacity_at_double_copper_a': 0.4967}, 'AVCC_L': {'budget_a': 0.08, 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0484, 'capacity_a': 0.3005, 'margin_x': 3.756, 'capacity_at_double_copper_a': 0.4967}, 'AVCC_R': {'budget_a': 0.08, 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0484, 'capacity_a': 0.3005, 'margin_x': 3.756, 'capacity_at_double_copper_a': 0.4967}, 'VREF': {'budget_a': 0.01, 'narrowest_mm': 0.2, 'layer': 'PWR', 'required_mm': 0.0027, 'capacity_a': 0.2239, 'margin_x': 22.395, 'capacity_at_double_copper_a': 0.3701}, 'N5_CP': {'budget_a': 0.4, 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0856, 'capacity_a': 0.7403, 'margin_x': 1.851, 'capacity_at_double_copper_a': None}, 'N5_C1P': {'budget_a': 0.4, 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0856, 'capacity_a': 0.7403, 'margin_x': 1.851, 'capacity_at_double_copper_a': None}, 'N5_C1N': {'budget_a': 0.4, 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0856, 'capacity_a': 0.7403, 'margin_x': 1.851, 'capacity_at_double_copper_a': None}}

**Findings.**

- `WARN` **AMPACITY_MARGIN** — VBUS: narrowest conductor has only 1.44x margin over the 0.5 A budget.
- `WARN` **AMPACITY_MARGIN** — 5V_SYS: narrowest conductor has only 1.44x margin over the 0.5 A budget.
- `FAIL` **AMPACITY** — VPOS: narrowest conductor 0.3 mm on PWR carries 0.3005 A but the rail budget is 0.4 A (needs 0.4451 mm). At 1 oz inner copper the same conductor would carry 0.4967 A, which would clear the budget, so confirm the stackup before acting.
- `FAIL` **AMPACITY** — VNEG: narrowest conductor 0.2 mm on PWR carries 0.2239 A but the rail budget is 0.4 A (needs 0.4451 mm). At 1 oz inner copper the same conductor would carry 0.3701 A, which would still miss the budget, so confirm the stackup before acting.
- `WARN` **AMPACITY_MARGIN** — 3V3D: narrowest conductor has only 1.48x margin over the 0.25 A budget.
- `WARN` **AMPACITY_MARGIN** — 1V3: narrowest conductor has only 1.23x margin over the 0.3 A budget.

### G11 — Via ampacity · WARN

**Criterion.** Each rail has enough plated barrel area at every layer transition to carry its budgeted current.

**Sources.** IPC-2221B eq. 6-4, I = k*dT^0.44*A^0.725 (k=0.048 external, 0.024 internal); JLCPCB: 18 um average through-hole plating

**Assumptions.**

- Barrel plating assumed 18 um (fabricator stated average).
- A via barrel is evaluated with the IPC-2221B internal constant because it is enclosed by laminate.

**Metrics.**

- `single_via_capacity_a` = {'0.2': 0.5272, '0.3': 0.7073, '0.4': 0.8714}
- `rails` = {'VBUS': {'budget_a': 0.5, 'weakest_transition_a': 0.8714, 'via_count': 1, 'margin_x': 1.74, 'at': [53.03, 84.05]}, 'VBUS_SENSE': {'budget_a': 0.001, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 527.18, 'at': [67.95, 70.0]}, '5V_SYS': {'budget_a': 0.5, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 1.05, 'at': [91.34, 88.4]}, '5V_ANA': {'budget_a': 0.3, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 1.76, 'at': [59.9, 126.975]}, '5V_ANA_F': {'budget_a': 0.3, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 1.76, 'at': [71.75, 133.8]}, 'VPOS': {'budget_a': 0.4, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 1.32, 'at': [100.1, 126.3]}, 'VNEG': {'budget_a': 0.4, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 1.32, 'at': [88.35, 111.8]}, 'N4_VPOS_IV': {'budget_a': 0.1, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 5.27, 'at': [94.1, 63.0]}, 'N4_VNEG_IV': {'budget_a': 0.1, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 5.27, 'at': [97.78, 96.94]}, '3V3D': {'budget_a': 0.25, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 2.11, 'at': [52.92, 114.13]}, '3V3A': {'budget_a': 0.1, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 5.27, 'at': [54.19, 81.9]}, '3V3M': {'budget_a': 0.1, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 5.27, 'at': [50.6, 72.75]}, 'N2_V33_CPLD': {'budget_a': 0.1, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 5.27, 'at': [86.91, 53.6]}, '1V3': {'budget_a': 0.3, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 1.76, 'at': [92.0, 95.0]}, 'DVCC': {'budget_a': 0.1, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 5.27, 'at': [88.41, 65.0]}, 'VCCA': {'budget_a': 0.05, 'weakest_transition_a': 0.7073, 'via_count': 1, 'margin_x': 14.15, 'at': [82.0, 70.5]}, 'AVCC_L': {'budget_a': 0.08, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 6.59, 'at': [91.7, 68.9125]}, 'AVCC_R': {'budget_a': 0.08, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 6.59, 'at': [102.3, 89.575]}, 'VREF': {'budget_a': 0.01, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 52.72, 'at': [95.05, 79.0]}}

**Findings.**

- `WARN` **VIA_AMPACITY_MARGIN** — 5V_SYS: weakest via transition has 1.05x margin (1 via(s), 0.5 A budget).
- `WARN` **VIA_AMPACITY_MARGIN** — VPOS: weakest via transition has 1.32x margin (1 via(s), 0.4 A budget).
- `WARN` **VIA_AMPACITY_MARGIN** — VNEG: weakest via transition has 1.32x margin (1 via(s), 0.4 A budget).

### G12 — DC IR drop (solved) · PASS

**Criterion.** Static voltage drop from each rail's source to its loads stays inside the rail budget, solved as a nodal network on the actual copper.

**Sources.** Nodal analysis of the extracted copper graph; IPC-2152 (conductor resistance basis)

**Assumptions.**

- Return-path (GND) drop is excluded: GND is a filled plane on four layers and its spreading resistance is not extracted here.
- The rail current budget is distributed equally across the rail's load pads; R_eff values reported per pad are independent of that split.
- Copper resistivity 1.724e-8 ohm*m at 20 C.

**Metrics.**

- `rails` = {'VBUS': {'source': 'U102', 'load_pads': 8, 'connected_pads': 8, 'open_pads': 0, 'worst_pad': 'U502.1', 'worst_r_eff_ohm': 0.01536, 'worst_drop_mv': 0.96, 'budget_mv': 150.0, 'budget_pct': 3.0, 'nodes': 63}, 'VBUS_SENSE': {'source': 'U201', 'load_pads': 4, 'connected_pads': 4, 'open_pads': 0, 'worst_pad': 'C103.1', 'worst_r_eff_ohm': 0.09098, 'worst_drop_mv': 0.023, 'budget_mv': 50.0, 'budget_pct': 1.0, 'nodes': 31}, '5V_SYS': {'source': 'U503', 'load_pads': 12, 'connected_pads': 12, 'open_pads': 0, 'worst_pad': 'K603.1', 'worst_r_eff_ohm': 0.12917, 'worst_drop_mv': 5.382, 'budget_mv': 150.0, 'budget_pct': 3.0, 'nodes': 148}, '5V_ANA': {'source': 'U503', 'load_pads': 4, 'connected_pads': 4, 'open_pads': 0, 'worst_pad': 'FB501.1', 'worst_r_eff_ohm': 0.02498, 'worst_drop_mv': 1.873, 'budget_mv': 50.0, 'budget_pct': 1.0, 'nodes': 39}, '5V_ANA_F': {'source': 'U501', 'load_pads': 5, 'connected_pads': 5, 'open_pads': 0, 'worst_pad': 'R535.1', 'worst_r_eff_ohm': 0.01455, 'worst_drop_mv': 0.873, 'budget_mv': 50.0, 'budget_pct': 1.0, 'nodes': 48}, 'VPOS': {'source': 'U501', 'load_pads': 66, 'connected_pads': 66, 'open_pads': 0, 'worst_pad': 'TP707.1', 'worst_r_eff_ohm': 0.2586, 'worst_drop_mv': 1.567, 'budget_mv': 150.0, 'budget_pct': 1.0, 'nodes': 638}, 'VNEG': {'source': 'U501', 'load_pads': 42, 'connected_pads': 42, 'open_pads': 0, 'worst_pad': 'C659.2', 'worst_r_eff_ohm': 0.16637, 'worst_drop_mv': 1.584, 'budget_mv': 150.0, 'budget_pct': 1.0, 'nodes': 410}, 'N4_VPOS_IV': {'source': 'U403', 'load_pads': 7, 'connected_pads': 7, 'open_pads': 0, 'worst_pad': 'D411.1', 'worst_r_eff_ohm': 0.08031, 'worst_drop_mv': 1.147, 'budget_mv': 150.0, 'budget_pct': 1.0, 'nodes': 69}, 'N4_VNEG_IV': {'source': 'U403', 'load_pads': 7, 'connected_pads': 7, 'open_pads': 0, 'worst_pad': 'C443.2', 'worst_r_eff_ohm': 0.1057, 'worst_drop_mv': 1.51, 'budget_mv': 150.0, 'budget_pct': 1.0, 'nodes': 80}, '3V3D': {'source': 'U504', 'load_pads': 32, 'connected_pads': 32, 'open_pads': 0, 'worst_pad': 'C623.1', 'worst_r_eff_ohm': 0.12364, 'worst_drop_mv': 0.966, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 288}, '3V3A': {'source': 'U302', 'load_pads': 20, 'connected_pads': 20, 'open_pads': 0, 'worst_pad': 'R631.2', 'worst_r_eff_ohm': 0.16241, 'worst_drop_mv': 0.812, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 229}, '3V3M': {'source': 'U201', 'load_pads': 33, 'connected_pads': 33, 'open_pads': 0, 'worst_pad': 'R528.1', 'worst_r_eff_ohm': 0.20133, 'worst_drop_mv': 0.61, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 317}, 'N2_V33_CPLD': {'source': 'FB202', 'load_pads': 9, 'connected_pads': 9, 'open_pads': 0, 'worst_pad': 'U202.16', 'worst_r_eff_ohm': 0.04842, 'worst_drop_mv': 0.538, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 66}, 'N2_J201_3V3': {'source': 'R241', 'load_pads': 1, 'connected_pads': 1, 'open_pads': 0, 'worst_pad': 'J201.1', 'worst_r_eff_ohm': 0.01009, 'worst_drop_mv': 0.504, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 4}, '1V3': {'source': 'U301', 'load_pads': 8, 'connected_pads': 8, 'open_pads': 0, 'worst_pad': 'R530.1', 'worst_r_eff_ohm': 0.22973, 'worst_drop_mv': 8.615, 'budget_mv': 13.0, 'budget_pct': 1.0, 'nodes': 113}, 'DVCC': {'source': 'U301', 'load_pads': 4, 'connected_pads': 4, 'open_pads': 0, 'worst_pad': 'R305.2', 'worst_r_eff_ohm': 0.06437, 'worst_drop_mv': 1.609, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 33}, 'VCCA': {'source': 'U301', 'load_pads': 3, 'connected_pads': 3, 'open_pads': 0, 'worst_pad': 'FB302.2', 'worst_r_eff_ohm': 0.04705, 'worst_drop_mv': 0.784, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 23}, 'AVCC_L': {'source': 'U301', 'load_pads': 6, 'connected_pads': 6, 'open_pads': 0, 'worst_pad': 'D405.2', 'worst_r_eff_ohm': 0.06823, 'worst_drop_mv': 0.91, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 55}, 'AVCC_R': {'source': 'U301', 'load_pads': 5, 'connected_pads': 5, 'open_pads': 0, 'worst_pad': 'D408.2', 'worst_r_eff_ohm': 0.08936, 'worst_drop_mv': 1.43, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 44}, 'VREF': {'source': 'U403', 'load_pads': 8, 'connected_pads': 8, 'open_pads': 0, 'worst_pad': 'TP709.1', 'worst_r_eff_ohm': 0.07301, 'worst_drop_mv': 0.091, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 85}, 'N5_CP': {'source': 'U501', 'load_pads': 1, 'connected_pads': 1, 'open_pads': 0, 'worst_pad': 'C509.1', 'worst_r_eff_ohm': 0.00531, 'worst_drop_mv': 2.123, 'budget_mv': 100.0, 'budget_pct': 2.0, 'nodes': 4}, 'N5_C1P': {'source': 'U501', 'load_pads': 1, 'connected_pads': 1, 'open_pads': 0, 'worst_pad': 'C508.1', 'worst_r_eff_ohm': 0.00596, 'worst_drop_mv': 2.386, 'budget_mv': 100.0, 'budget_pct': 2.0, 'nodes': 4}, 'N5_C1N': {'source': 'U501', 'load_pads': 1, 'connected_pads': 1, 'open_pads': 0, 'worst_pad': 'C508.2', 'worst_r_eff_ohm': 0.00596, 'worst_drop_mv': 2.386, 'budget_mv': 100.0, 'budget_pct': 2.0, 'nodes': 4}}

### G13 — Decoupling placement and mounted resonance · WARN

**Criterion.** Every device supply pin has a high-frequency bypass capacitor close enough that the mounted loop inductance keeps its self-resonance above the frequencies the device actually needs decoupled.

**Sources.** C. R. Paul, Inductance: Loop and Partial, Wiley 2010, ch. 5; Ott, Electromagnetic Compatibility Engineering, ch. 11

**Assumptions.**

- Capacitor values are parsed from the footprint Value field.
- Mounting inductance counts the via pair under the capacitor plus the pad-to-via run; the capacitor's own ESL is taken as 0.6 nH for 0402 and 0.9 nH for 0603, typical MLCC values.

**Metrics.**

- `capacitors_parsed` = 147
- `pins_checked` = 92
- `worst_by_distance` = [{'pin': 'U102.1', 'net': '5V_SYS', 'cap': 'C505', 'cap_value': '100 nF', 'distance_mm': 32.414, 'mount_inductance_nh': 0.195, 'mounted_srf_mhz': 17.85, 'local_vias': True}, {'pin': 'U201.15', 'net': 'VBUS_SENSE', 'cap': 'C103', 'cap_value': '100 pF', 'distance_mm': 30.364, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 378.11, 'local_vias': False}, {'pin': 'U504.2', 'net': '3V3D', 'cap': 'C512', 'cap_value': '10 µF', 'distance_mm': 20.412, 'mount_inductance_nh': 1.621, 'mounted_srf_mhz': 0.95, 'local_vias': False}, {'pin': 'U504.1', 'net': '3V3D', 'cap': 'C512', 'cap_value': '10 µF', 'distance_mm': 19.775, 'mount_inductance_nh': 1.621, 'mounted_srf_mhz': 0.95, 'local_vias': False}, {'pin': 'U102.6', 'net': 'VBUS', 'cap': 'C102', 'cap_value': '2.2 µF', 'distance_mm': 19.76, 'mount_inductance_nh': 1.621, 'mounted_srf_mhz': 2.02, 'local_vias': False}, {'pin': 'U504.6', 'net': '5V_SYS', 'cap': 'C501', 'cap_value': '1 µF', 'distance_mm': 13.471, 'mount_inductance_nh': 1.489, 'mounted_srf_mhz': 3.26, 'local_vias': False}, {'pin': 'U606.12', 'net': 'VNEG', 'cap': 'C636', 'cap_value': '100 nF', 'distance_mm': 11.902, 'mount_inductance_nh': 0.288, 'mounted_srf_mhz': 16.89, 'local_vias': True}, {'pin': 'U603.3', 'net': 'VPOS', 'cap': 'C618', 'cap_value': '100 nF', 'distance_mm': 11.484, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U612.12', 'net': 'VNEG', 'cap': 'C619', 'cap_value': '100 nF', 'distance_mm': 11.414, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U603.12', 'net': 'VNEG', 'cap': 'C656', 'cap_value': '100 nF', 'distance_mm': 11.335, 'mount_inductance_nh': 0.288, 'mounted_srf_mhz': 16.89, 'local_vias': True}, {'pin': 'U505.5', 'net': '3V3M', 'cap': 'C515', 'cap_value': '100 nF', 'distance_mm': 11.213, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U606.3', 'net': 'VPOS', 'cap': 'C618', 'cap_value': '100 nF', 'distance_mm': 11.068, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U404.5', 'net': 'VREF', 'cap': 'C421', 'cap_value': '33 pF', 'distance_mm': 10.341, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 658.2, 'local_vias': False}, {'pin': 'U201.64', 'net': '3V3M', 'cap': 'C204', 'cap_value': '100 nF', 'distance_mm': 9.23, 'mount_inductance_nh': 0.288, 'mounted_srf_mhz': 16.89, 'local_vias': True}, {'pin': 'U403.3', 'net': 'VREF', 'cap': 'C421', 'cap_value': '33 pF', 'distance_mm': 8.841, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 658.2, 'local_vias': False}]
- `median_distance_mm` = 3.825

**Findings.**

- `WARN` **BYPASS_DISTANCE** — U303.1 (3V3D): nearest bypass C311 (1 µF) is 3.20 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U403.3 (VREF): nearest bypass C421 (33 pF) is 8.84 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U403.5 (VREF): nearest bypass C421 (33 pF) is 7.90 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U608.7 (3V3D): nearest bypass C630 (100 nF) is 3.17 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U614.4 (VNEG): nearest bypass C660 (100 nF) is 5.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U614.8 (VPOS): nearest bypass C660 (100 nF) is 3.98 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U618.4 (VNEG): nearest bypass C664 (100 nF) is 5.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U618.8 (VPOS): nearest bypass C664 (100 nF) is 3.98 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U504.6 (5V_SYS): nearest bypass C501 (1 µF) is 13.47 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U616.4 (VNEG): nearest bypass C662 (100 nF) is 5.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U616.8 (VPOS): nearest bypass C662 (100 nF) is 3.98 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.1 (3V3M): nearest bypass C204 (100 nF) is 6.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.13 (3V3M): nearest bypass C204 (100 nF) is 3.87 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.15 (VBUS_SENSE): nearest bypass C103 (100 pF) is 30.36 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.19 (3V3M): nearest bypass C205 (100 nF) is 6.96 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.32 (3V3M): nearest bypass C221 (1 µF) is 8.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.64 (3V3M): nearest bypass C204 (100 nF) is 9.23 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U619.4 (VNEG): nearest bypass C665 (100 nF) is 6.47 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U404.3 (VREF): nearest bypass C421 (33 pF) is 7.61 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U404.4 (N4_VNEG_IV): nearest bypass C426 (100 nF) is 4.13 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U404.5 (VREF): nearest bypass C421 (33 pF) is 10.34 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U609.12 (VNEG): nearest bypass C636 (100 nF) is 3.78 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U613.4 (VNEG): nearest bypass C659 (100 nF) is 6.47 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U401.8 (VPOS): nearest bypass C409 (100 nF) is 4.56 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U401.PAD (VNEG): nearest bypass C410 (100 nF) is 3.00 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U208.8 (3V3D): nearest bypass C224 (100 nF) is 5.13 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U505.5 (3V3M): nearest bypass C515 (100 nF) is 11.21 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U603.3 (VPOS): nearest bypass C618 (100 nF) is 11.48 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U603.12 (VNEG): nearest bypass C656 (100 nF) is 11.33 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U611.3 (VPOS): nearest bypass C618 (100 nF) is 4.37 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U611.12 (VNEG): nearest bypass C619 (100 nF) is 7.14 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U612.3 (VPOS): nearest bypass C626 (100 nF) is 3.91 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U612.12 (VNEG): nearest bypass C619 (100 nF) is 11.41 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U615.4 (VNEG): nearest bypass C661 (100 nF) is 6.47 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U617.4 (VNEG): nearest bypass C663 (100 nF) is 6.47 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U402.2 (VPOS): nearest bypass C411 (100 nF) is 3.08 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U402.8 (VPOS): nearest bypass C411 (100 nF) is 3.51 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U402.PAD (VNEG): nearest bypass C412 (100 nF) is 3.00 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U503.4 (5V_SYS): nearest bypass C501 (1 µF) is 5.09 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U503.5 (5V_ANA): nearest bypass C506 (1 µF) is 8.71 mm away, beyond the 3.0 mm high-frequency guideline.
- … 8 more at this severity in the JSON result.

### G20 — USB high-speed differential pair · FAIL

**Criterion.** The USB 2.0 high-speed pair is routed as a matched, tightly coupled pair with a continuous reference and the intra-pair skew well inside the specification limit.

**Sources.** USB 2.0 specification rev 2.0 §7.1.1.3 and USB-IF HS layout guidance; IPC-2251 (design guide for high-speed interconnect)

**Assumptions.**

- Impedance is therefore not evaluated numerically.

**Metrics.**

- `dp_length_mm` = 25.85
- `dn_length_mm` = 23.697
- `intra_pair_skew_mm` = 2.153
- `skew_limit_mm` = 3.81
- `longest_leg_mm` = 25.85
- `dp_vias` = 0
- `dn_vias` = 0
- `layers_used` = ['F.Cu']
- `median_pair_centre_gap_mm` = 0.5
- `pair_track_widths_mm` = [0.16]
- `spacing_to_others_rule_mm` = 0.48
- `min_spacing_to_other_signal_mm` = 0.2775
- `min_spacing_offender` = ['VBUS', 'F.Cu']

**Findings.**

- `WARN` **USB_SKEW_MARGIN** — Intra-pair skew 2.15 mm uses more than half of the 3.81 mm budget.
- `WARN` **USB_3W_SPACING** — 4 other net(s) come closer to the USB pair than the 3.0W (0.48 mm) screen.
- `FAIL` **USB_IMPEDANCE_UNVERIFIABLE** — The board declares a USB_DIFF controlled-impedance netclass, but no stackup defines the dielectric height or Er. The 90.0 ohm +/-15.0% target cannot be computed here, nor specified to the fabricator.

### G21 — Clock routing and aggressor spacing · WARN

**Criterion.** Clock nets are routed short, with few layer changes, and keep enough distance from analog audio nets that crosstalk stays below the audio noise floor.

**Sources.** H. Ott, Electromagnetic Compatibility Engineering, ch. 10-12; IPC-2251 (design guide for high-speed interconnect)

**Assumptions.**

- Crosstalk is judged by edge-to-edge spacing on shared or adjacent layers, not by a solved coupled-line model; a full extraction needs the dielectric build.

**Metrics.**

- `clock_to_audio_rule_mm` = 1.0
- `clock_nets_present` = 30
- `audio_nets_present` = 36
- `min_clock_to_audio_mm` = 1.0461
- `min_clock_to_audio_between` = ['N2_CAP_CK', 'N4_IVL_N', 'F.Cu']
- `clock_via_limit` = 4
- `clock_lengths_mm` = {'N6_MCK_RC': 68.41, 'LRCLK_FB': 39.79, 'N2_CAP_CK': 37.41, 'N2_CAP_WS': 30.19, 'LINK_SCK': 27.91, 'N2_LINK_SCK_BUF': 27.79, 'CPLD_JTCK': 26.16, 'N2_CAP_SD': 24.72, 'SWCLK': 20.83, 'BCLK': 16.64, 'LRCLK': 15.9, 'SDATA': 15.2, 'N2_HSE_OUT': 15.02, 'N2_HSE_IN': 12.47, 'N6_REFMCK': 11.96}

**Findings.**

- `WARN` **CLOCK_VIAS** — 1 clock net(s) use more than 4 vias, adding reference discontinuities to a jitter-critical net.

### G22 — Return path and reference continuity · WARN

**Criterion.** Signal layers are referenced to a ground plane, and vias that change reference have a stitching via close enough to carry the return current.

**Sources.** H. Ott, Electromagnetic Compatibility Engineering, ch. 10-12; IPC-2251 §5 (reference planes and return current)

**Metrics.**

- `copper_layers` = ['F.Cu', 'GND', 'PWR', 'SIG', 'GND5', 'B.Cu']
- `zone_nets_by_layer` = {'F.Cu': ['GND'], 'B.Cu': ['GND'], 'GND': ['GND'], 'PWR': ['GND'], 'SIG': ['GND'], 'GND5': ['GND']}
- `ground_plane_layers` = ['F.Cu', 'GND', 'PWR', 'SIG', 'GND5', 'B.Cu']
- `ground_stitching_vias` = 716
- `stitching_distance_rule_mm` = 2.0
- `signal_vias_checked` = 249
- `worst_stitching_distance_mm` = 6.321
- `worst_stitching_net` = N4_IVR_N

**Findings.**

- `WARN` **RETURN_PATH_STITCHING** — 138 layer-changing signal via(s) have no ground via within 2.0 mm, so the return current must detour.

### G23 — Switching-node keep-out · PASS

**Criterion.** The charge-pump and regulator switching nodes keep clear of analog audio and high-impedance nets, so switching noise is not injected into the signal path.

**Sources.** H. Ott, Electromagnetic Compatibility Engineering, ch. 10-12; TI SLVA959 / LM27762 layout guidance

**Assumptions.**

- The switching-node keep-out is the digital-to-analog minimum gap (0.75 mm) applied as a floor, not a switcher-specific limit.

**Metrics.**

- `switcher_keepout_mm` = 0.75
- `switching_net_segments` = 24

### G30 — Headphone output path resistance and channel matching · WARN

**Criterion.** Series copper resistance in the balanced headphone output stays small against the load so the damping factor is preserved, and the two channels match closely enough not to shift the stereo image.

**Sources.** D. Self, Audio Power Amplifier Design (output impedance / damping)

**Assumptions.**

- Only drawn copper is included: connector contact, relay contact and amplifier output impedance are additional to these numbers.

**Metrics.**

- `load_ohm` = 32.0
- `trace_resistance_budget_ohm` = 0.1
- `channel_mismatch_budget_ohm` = 0.02
- `output_net_resistance_ohm` = {'JACK_LN': 0.0354, 'JACK_LP': 0.04094, 'JACK_RN': 0.01082, 'JACK_RP': 0.02459, 'LEG_LN': 0.32669, 'LEG_LP': 0.4852, 'LEG_RN': 0.34017, 'LEG_RP': 0.26434, 'N4_LN_OUT': 0.02683, 'N4_LP_OUT': 0.0249, 'N4_RN_OUT': 0.01567, 'N4_RP_OUT': 0.0324}
- `worst_damping_factor` = 66.0
- `worst_damping_net` = LEG_LP
- `channel_mismatch_ohm` = {'JACK_LP/JACK_RP': 0.01635, 'JACK_LN/JACK_RN': 0.02458, 'LEG_LP/LEG_RP': 0.22086, 'LEG_LN/LEG_RN': 0.01347}

**Findings.**

- `WARN` **OUTPUT_RESISTANCE** — 4 output net(s) exceed the 0.1 ohm copper budget; damping factor into 32.0 ohm is reduced.
- `WARN` **DAMPING_FACTOR** — LEG_LP alone limits the damping factor to 66, below the 100 target.
- `WARN` **CHANNEL_MISMATCH** — 2 channel pair(s) differ by more than 0.02 ohm of copper.

### G31 — I/V and feedback loop geometry · WARN

**Criterion.** The inverting summing node and its feedback loop are kept physically small, since that node is the highest-impedance point in the signal path.

**Sources.** H. Ott, Electromagnetic Compatibility Engineering, ch. 11-12; TI SBOA015 / OPA.. inverting-input layout guidance

**Metrics.**

- `feedback_loop_area_budget_mm2` = 25.0
- `feedback_trace_budget_mm` = 15.0
- `summing_node_budget_mm` = 10.0
- `feedback_net_lengths_mm` = {'N4_IVR_N': 90.45, 'N4_IVR_P': 83.59, 'N4_IVL_N': 53.67, 'N4_IVL_P': 47.46, 'N4_LP_INP': 11.72, 'N4_LP_INN': 9.99, 'N4_LP_TN': 8.64, 'N4_RP_TN': 7.66, 'N4_LN_INP': 7.65, 'N4_RN_TP': 7.25, 'N4_RN_INN': 7.14, 'N4_RP_INN': 7.09, 'N4_RN_INP': 6.87, 'N4_LN_INN': 6.68, 'N4_RP_INP': 6.57}
- `feedback_loop_areas_mm2` = {'N4_IVR_N': 479.91, 'N4_IVR_P': 417.06, 'N4_IVL_N': 207.92, 'N4_IVL_P': 121.04, 'N4_LP_INP': 12.72, 'N4_LP_INN': 12.62, 'N4_LP_TN': 8.37, 'N4_RN_INN': 7.27, 'N4_RN_TP': 7.0, 'N4_RP_TN': 6.88, 'N4_LN_INN': 5.96, 'N4_RN_INP': 5.51, 'N4_RP_INN': 5.19, 'N4_LN_INP': 4.31, 'N4_RP_INP': 4.22}

**Findings.**

- `WARN` **FEEDBACK_TRACE_LONG** — 5 feedback/summing net(s) are longer than their budget, raising noise pickup at a high-impedance node.
- `WARN` **FEEDBACK_LOOP_AREA** — 4 feedback net(s) enclose more than 25.0 mm^2, so the loop is a larger magnetic antenna.

### G32 — External port ESD protection · WARN

**Criterion.** Every externally exposed pin reaches its protection device through a short stub, so the let-through voltage from stub inductance stays bounded.

**Sources.** IEC 61000-4-2 (ESD immunity) with TVS stub-inductance let-through

**Assumptions.**

- The stub is the shortest copper path from the connector pin to the nearest clamp, which is what the strike current actually traverses; copper beyond the clamp is downstream and is not counted.

**Metrics.**

- `esd_stub_budget_mm` = 10.0
- `ports` = {'CC1': {'parts': ['J101', 'R101', 'R103', 'TP726', 'U103'], 'protection': ['U103'], 'connector': ['J101'], 'stub_mm': 8.41}, 'CC2': {'parts': ['J101', 'R102', 'R104', 'TP727', 'U103'], 'protection': ['U103'], 'connector': ['J101'], 'stub_mm': 18.71}, 'JACK_LN': {'parts': ['D703', 'J701', 'K602'], 'protection': ['D703'], 'connector': ['J701'], 'stub_mm': 4.03}, 'JACK_LP': {'parts': ['D701', 'D708', 'J701', 'J702', 'K601'], 'protection': ['D701', 'D708'], 'connector': ['J701', 'J702'], 'stub_mm': 3.35}, 'JACK_RN': {'parts': ['D704', 'J701', 'K604'], 'protection': ['D704'], 'connector': ['J701'], 'stub_mm': 4.03}, 'JACK_RP': {'parts': ['D702', 'D707', 'J701', 'J702', 'K603'], 'protection': ['D702', 'D707'], 'connector': ['J701', 'J702'], 'stub_mm': 3.86}, 'N1_SHIELD': {'parts': ['C101', 'J101', 'R107'], 'protection': [], 'connector': ['J101'], 'ground_bond': ['C101', 'R107']}, 'USB_DN': {'parts': ['J101', 'U101', 'U201'], 'protection': ['U101'], 'connector': ['J101'], 'stub_mm': 4.56}, 'USB_DP': {'parts': ['J101', 'U101', 'U201'], 'protection': ['U101'], 'connector': ['J101'], 'stub_mm': 7.95}, 'VBUS': {'parts': ['C102', 'D102', 'J101', 'R109', 'TP736', 'TP753', 'U102', 'U502'], 'protection': ['D102'], 'connector': ['J101'], 'ground_bond': ['C102'], 'stub_mm': 6.29}}

**Findings.**

- `WARN` **ESD_STUB_LONG** — 1 port net(s) reach their clamp through more than 10.0 mm of copper, so stub inductance raises the ESD let-through.

### G40 — Power distribution network impedance (LTspice) · FAIL

**Criterion.** At the hardest-to-decouple pin of each rail, the simulated PDN impedance stays below the target impedance across the control band, using capacitor and interconnect parasitics extracted from the layout.

**Sources.** L. Smith / E. Bogatin, Principles of Power Integrity (target impedance and decoupling); C. R. Paul, Inductance: Loop and Partial (via-pair loop inductance)

**Assumptions.**

- The outer-to-plane dielectric height is not declared by the board, so each rail is simulated at 0.09, 0.12 and 0.2 mm and the gate reports the worst case.
- Capacitor ESR/ESL come from the placed package size; the regulator is modelled as an ideal source behind the solved copper resistance and the loop inductance of the feed path.

**Metrics.**

- `band_hz` = [100000.0, 100000000.0]
- `plane_height_sweep_mm` = {'min': 0.09, 'typical': 0.12, 'max': 0.2}
- `rails` = {'1V3': {'z_at_mclk_ohm': 0.1821, 'z_target_ohm': 0.0433, 'z_max_in_band_ohm': 0.8648, 'z_at_100khz_ohm': 0.0118, 'z_at_100mhz_ohm': 0.8648, 'decoupling_bandwidth_hz': 1074313, 'cap_count': 3, 'local_cap_count': 2, 'total_capacitance_uf': 3.3, 'worst_pin': 'U301.21', 'nearest_cap_mm': 2.36, 'margin_db_at_mclk': -12.47, 'assumed_current_a': 0.3, 'passes_if_transient_below_a': 0.0714, 'track_width_mm': 0.4}, '3V3A': {'z_at_mclk_ohm': 0.3132, 'z_target_ohm': 0.33, 'z_max_in_band_ohm': 1.3905, 'z_at_100khz_ohm': 0.0118, 'z_at_100mhz_ohm': 1.3905, 'decoupling_bandwidth_hz': 23783818, 'cap_count': 2, 'local_cap_count': 1, 'total_capacitance_uf': 3.2, 'worst_pin': 'U302.5', 'nearest_cap_mm': 2.63, 'margin_db_at_mclk': 0.45, 'assumed_current_a': 0.1, 'passes_if_transient_below_a': 0.1054, 'track_width_mm': 0.4}, '3V3D': {'z_at_mclk_ohm': 0.3995, 'z_target_ohm': 0.66, 'z_max_in_band_ohm': 1.781, 'z_at_100khz_ohm': 0.0045, 'z_at_100mhz_ohm': 1.781, 'decoupling_bandwidth_hz': 37136571, 'cap_count': 11, 'local_cap_count': 0, 'total_capacitance_uf': 11.81, 'worst_pin': 'U504.2', 'nearest_cap_mm': 27.94, 'margin_db_at_mclk': 4.36, 'assumed_current_a': 0.25, 'passes_if_transient_below_a': 0.413, 'track_width_mm': 0.4}, '3V3M': {'z_at_mclk_ohm': 0.4267, 'z_target_ohm': 1.65, 'z_max_in_band_ohm': 1.9168, 'z_at_100khz_ohm': 0.1353, 'z_at_100mhz_ohm': 1.9168, 'decoupling_bandwidth_hz': 86103848, 'cap_count': 14, 'local_cap_count': 0, 'total_capacitance_uf': 6.5, 'worst_pin': 'U505.5', 'nearest_cap_mm': 16.42, 'margin_db_at_mclk': 11.75, 'assumed_current_a': 0.1, 'passes_if_transient_below_a': 0.3867, 'track_width_mm': 0.4}, '5V_ANA': {'z_at_mclk_ohm': 0.3153, 'z_target_ohm': 0.1667, 'z_max_in_band_ohm': 1.3982, 'z_at_100khz_ohm': 0.0112, 'z_at_100mhz_ohm': 1.3982, 'decoupling_bandwidth_hz': 11978022, 'cap_count': 1, 'local_cap_count': 0, 'total_capacitance_uf': 1.0, 'worst_pin': 'U503.5', 'nearest_cap_mm': 18.36, 'margin_db_at_mclk': -5.54, 'assumed_current_a': 0.3, 'passes_if_transient_below_a': 0.1586, 'track_width_mm': 0.8}, '5V_ANA_F': {'z_at_mclk_ohm': 0.2482, 'z_target_ohm': 0.1667, 'z_max_in_band_ohm': 1.0991, 'z_at_100khz_ohm': 0.0114, 'z_at_100mhz_ohm': 1.0991, 'decoupling_bandwidth_hz': 15154284, 'cap_count': 1, 'local_cap_count': 1, 'total_capacitance_uf': 10.0, 'worst_pin': 'U501.8', 'nearest_cap_mm': 6.18, 'margin_db_at_mclk': -3.46, 'assumed_current_a': 0.3, 'passes_if_transient_below_a': 0.2014, 'track_width_mm': 0.8}, '5V_SYS': {'z_at_mclk_ohm': 0.5175, 'z_target_ohm': 0.5, 'z_max_in_band_ohm': 2.3052, 'z_at_100khz_ohm': 0.0374, 'z_at_100mhz_ohm': 2.3052, 'decoupling_bandwidth_hz': 21823338, 'cap_count': 3, 'local_cap_count': 0, 'total_capacitance_uf': 3.3, 'worst_pin': 'U102.1', 'nearest_cap_mm': 35.81, 'margin_db_at_mclk': -0.3, 'assumed_current_a': 0.5, 'passes_if_transient_below_a': 0.4831, 'track_width_mm': 1.0}, 'AVCC_L': {'z_at_mclk_ohm': 0.2243, 'z_target_ohm': 0.4125, 'z_max_in_band_ohm': 1.1056, 'z_at_100khz_ohm': 0.0123, 'z_at_100mhz_ohm': 1.1056, 'decoupling_bandwidth_hz': 5329505, 'cap_count': 2, 'local_cap_count': 2, 'total_capacitance_uf': 2.3, 'worst_pin': 'U301.15', 'nearest_cap_mm': 2.44, 'margin_db_at_mclk': 5.29, 'assumed_current_a': 0.08, 'passes_if_transient_below_a': 0.1471, 'track_width_mm': 0.3}, 'AVCC_R': {'z_at_mclk_ohm': 0.1951, 'z_target_ohm': 0.4125, 'z_max_in_band_ohm': 0.9757, 'z_at_100khz_ohm': 0.0123, 'z_at_100mhz_ohm': 0.9757, 'decoupling_bandwidth_hz': 5837938, 'cap_count': 2, 'local_cap_count': 2, 'total_capacitance_uf': 2.3, 'worst_pin': 'U301.16', 'nearest_cap_mm': 2.05, 'margin_db_at_mclk': 6.51, 'assumed_current_a': 0.08, 'passes_if_transient_below_a': 0.1692, 'track_width_mm': 0.3}, 'DVCC': {'z_at_mclk_ohm': 0.2562, 'z_target_ohm': 1.65, 'z_max_in_band_ohm': 1.2369, 'z_at_100khz_ohm': 0.0128, 'z_at_100mhz_ohm': 1.2369, 'decoupling_bandwidth_hz': None, 'cap_count': 2, 'local_cap_count': 2, 'total_capacitance_uf': 2.3, 'worst_pin': 'U301.18', 'nearest_cap_mm': 2.53, 'margin_db_at_mclk': 16.18, 'assumed_current_a': 0.1, 'passes_if_transient_below_a': 0.6441, 'track_width_mm': 0.25}, 'N4_VNEG_IV': {'z_at_mclk_ohm': 0.2203, 'z_target_ohm': 1.5, 'z_max_in_band_ohm': 1.0398, 'z_at_100khz_ohm': 0.0179, 'z_at_100mhz_ohm': 1.0398, 'decoupling_bandwidth_hz': None, 'cap_count': 3, 'local_cap_count': 1, 'total_capacitance_uf': 220.2, 'worst_pin': 'U404.4', 'nearest_cap_mm': 5.44, 'margin_db_at_mclk': 16.66, 'assumed_current_a': 0.1, 'passes_if_transient_below_a': 0.6808, 'track_width_mm': 0.5}, 'N4_VPOS_IV': {'z_at_mclk_ohm': 0.2647, 'z_target_ohm': 1.5, 'z_max_in_band_ohm': 1.2523, 'z_at_100khz_ohm': 0.0111, 'z_at_100mhz_ohm': 1.2523, 'decoupling_bandwidth_hz': None, 'cap_count': 3, 'local_cap_count': 1, 'total_capacitance_uf': 220.2, 'worst_pin': 'U403.8', 'nearest_cap_mm': 4.06, 'margin_db_at_mclk': 15.07, 'assumed_current_a': 0.1, 'passes_if_transient_below_a': 0.5666, 'track_width_mm': 0.4}, 'VBUS': {'z_at_mclk_ohm': 0.2767, 'z_target_ohm': 0.5, 'z_max_in_band_ohm': 1.2255, 'z_at_100khz_ohm': 0.0111, 'z_at_100mhz_ohm': 1.2255, 'decoupling_bandwidth_hz': 40799882, 'cap_count': 1, 'local_cap_count': 0, 'total_capacitance_uf': 2.2, 'worst_pin': 'U102.6', 'nearest_cap_mm': 23.82, 'margin_db_at_mclk': 5.14, 'assumed_current_a': 0.5, 'passes_if_transient_below_a': 0.9036, 'track_width_mm': 1.0}, 'VCCA': {'z_at_mclk_ohm': 0.2208, 'z_target_ohm': 0.66, 'z_max_in_band_ohm': 1.0915, 'z_at_100khz_ohm': 0.0128, 'z_at_100mhz_ohm': 1.0915, 'decoupling_bandwidth_hz': 61010712, 'cap_count': 2, 'local_cap_count': 2, 'total_capacitance_uf': 2.3, 'worst_pin': 'U301.17', 'nearest_cap_mm': 1.99, 'margin_db_at_mclk': 9.51, 'assumed_current_a': 0.05, 'passes_if_transient_below_a': 0.1494, 'track_width_mm': 0.25}, 'VNEG': {'z_at_mclk_ohm': 0.3436, 'z_target_ohm': 0.375, 'z_max_in_band_ohm': 1.5438, 'z_at_100khz_ohm': 0.043, 'z_at_100mhz_ohm': 1.5438, 'decoupling_bandwidth_hz': 24583651, 'cap_count': 19, 'local_cap_count': 0, 'total_capacitance_uf': 31.6, 'worst_pin': 'U606.12', 'nearest_cap_mm': 22.84, 'margin_db_at_mclk': 0.76, 'assumed_current_a': 0.4, 'passes_if_transient_below_a': 0.4366, 'track_width_mm': 0.4}, 'VPOS': {'z_at_mclk_ohm': 0.3449, 'z_target_ohm': 0.375, 'z_max_in_band_ohm': 1.5501, 'z_at_100khz_ohm': 0.0457, 'z_at_100mhz_ohm': 1.5501, 'decoupling_bandwidth_hz': 24492972, 'cap_count': 19, 'local_cap_count': 0, 'total_capacitance_uf': 31.6, 'worst_pin': 'U603.3', 'nearest_cap_mm': 20.98, 'margin_db_at_mclk': 0.73, 'assumed_current_a': 0.4, 'passes_if_transient_below_a': 0.4349, 'track_width_mm': 0.4}, 'VREF': {'z_at_mclk_ohm': 1.7462, 'z_target_ohm': 3.3, 'z_max_in_band_ohm': 10.4553, 'z_at_100khz_ohm': 0.0475, 'z_at_100mhz_ohm': 10.4553, 'decoupling_bandwidth_hz': 41753517, 'cap_count': 1, 'local_cap_count': 0, 'total_capacitance_uf': 0.0, 'worst_pin': 'U404.5', 'nearest_cap_mm': 22.9, 'margin_db_at_mclk': 5.53, 'assumed_current_a': 0.01, 'passes_if_transient_below_a': 0.0189, 'track_width_mm': 0.2}}
- `criterion_frequency_hz` = 22579200.0

**Findings.**

- `WARN` **PDN_NOT_EVALUATED** — 1 rail(s) could not be simulated.
- `FAIL` **PDN_OVER_TARGET** — 4 of 17 rail(s) exceed their target impedance at the 22.58 MHz master clock, where the board's dominant switching current sits. The target scales with the assumed transient current, so each entry also reports the current at which it would pass.

### G41 — Headphone output loading and damping (LTspice) · WARN

**Criterion.** With the solved output-path resistance in circuit, the amplifier still meets its damping-factor target into the rated load and the two channels stay matched.

**Sources.** D. Self, Audio Power Amplifier Design

**Assumptions.**

- The amplifier is modelled as an ideal source, so the simulated damping factor is the ceiling the copper allows; the active stage can only reduce it.

**Metrics.**

- `load_ohm` = 32.0
- `min_damping_factor` = 100.0
- `outputs` = {'JACK_LN': {'r_copper_ohm': 0.0314, 'insertion_loss_db': -0.0085, 'damping_factor': 1019.2}, 'JACK_LP': {'r_copper_ohm': 0.04475, 'insertion_loss_db': -0.0121, 'damping_factor': 715.1}, 'JACK_RN': {'r_copper_ohm': 0.00879, 'insertion_loss_db': -0.0024, 'damping_factor': 3640.7}, 'JACK_RP': {'r_copper_ohm': 0.02859, 'insertion_loss_db': -0.0078, 'damping_factor': 1119.2}, 'LEG_LN': {'r_copper_ohm': 0.32669, 'insertion_loss_db': -0.0882, 'damping_factor': 98.0}, 'LEG_LP': {'r_copper_ohm': 0.4852, 'insertion_loss_db': -0.1307, 'damping_factor': 66.0}, 'LEG_RN': {'r_copper_ohm': 0.34017, 'insertion_loss_db': -0.0918, 'damping_factor': 94.1}, 'LEG_RP': {'r_copper_ohm': 0.26434, 'insertion_loss_db': -0.0715, 'damping_factor': 121.1}, 'N4_LN_OUT': {'r_copper_ohm': 0.02683, 'insertion_loss_db': -0.0073, 'damping_factor': 1192.6}, 'N4_LP_OUT': {'r_copper_ohm': 0.0249, 'insertion_loss_db': -0.0068, 'damping_factor': 1285.2}, 'N4_RN_OUT': {'r_copper_ohm': 0.01567, 'insertion_loss_db': -0.0043, 'damping_factor': 2042.4}, 'N4_RP_OUT': {'r_copper_ohm': 0.0324, 'insertion_loss_db': -0.0088, 'damping_factor': 987.5}}
- `worst_damping_factor` = 66.0
- `worst_net` = LEG_LP

**Findings.**

- `WARN` **DAMPING_BELOW_TARGET** — 3 output net(s) hold the damping factor below 100 through copper resistance alone.

