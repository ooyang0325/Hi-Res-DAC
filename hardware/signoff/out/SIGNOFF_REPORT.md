# Independent layout sign-off report

- Board: `DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb`
- Extracted with KiCad 10.0.1
- Copper layers: 6 (F.Cu, GND, PWR, SIG, GND5, B.Cu)
- Footprints 545, pads 1478, tracks 5172, vias 1564, nets 254
- Layer stack: from stackup (1.6 mm board)

## Verdict: WARN

0 gate(s) FAIL, 10 WARN, 9 PASS, 0 informational.

## Gate summary

| Gate | Status | Title | FAIL | WARN |
| --- | --- | --- | ---: | ---: |
| G01 | **PASS** | Fabricator process window | 0 | 0 |
| G02 | **PASS** | Electrical clearance (IPC-2221B) | 0 | 0 |
| G03 | **WARN** | Plated-hole geometry (IPC-6012) | 0 | 1 |
| G04 | **PASS** | Assembly geometry (IPC-7351B) | 0 | 0 |
| G05 | **PASS** | Fabrication documentation | 0 | 0 |
| G06 | **WARN** | Drill-to-copper clearance | 0 | 1 |
| G10 | **WARN** | Conductor ampacity (IPC-2221B) | 0 | 2 |
| G11 | **WARN** | Via ampacity | 0 | 1 |
| G12 | **PASS** | DC IR drop (solved) | 0 | 0 |
| G13 | **WARN** | Decoupling placement and mounted resonance | 0 | 40 |
| G20 | **WARN** | USB high-speed differential pair | 0 | 1 |
| G21 | **PASS** | Clock routing and aggressor spacing | 0 | 0 |
| G22 | **WARN** | Return path and reference continuity | 0 | 1 |
| G23 | **PASS** | Switching-node keep-out | 0 | 0 |
| G30 | **WARN** | Headphone output path resistance and channel matching | 0 | 1 |
| G31 | **WARN** | I/V and feedback loop geometry | 0 | 2 |
| G32 | **WARN** | External port ESD protection | 0 | 1 |
| G40 | **PASS** | Power distribution network impedance (LTspice) | 0 | 0 |
| G41 | **PASS** | Headphone output loading and damping (LTspice) | 0 | 0 |

## Gate detail

### G01 — Fabricator process window · PASS

**Criterion.** Every drawn feature is inside the JLCPCB multilayer process window, with the surcharge-free and recommended values treated as warnings.

**Sources.** JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com

**Metrics.**

- `track_width_histogram_mm` = {'0.15': 1024, '0.16': 7, '0.17': 6, '0.18': 4, '0.2': 2560, '0.25': 366, '0.3': 445, '0.36': 2, '0.4': 361, '0.5': 162, '0.6': 41, '0.8': 62, '1.0': 111, '1.15': 1, '1.2': 14, '1.5': 6}
- `min_track_width_mm` = 0.15
- `via_specs` = {'0.5/0.2': 133, '0.6/0.2': 1367, '0.7/0.3': 45, '0.8/0.4': 19}
- `via_count` = 1564
- `min_hole_to_hole_mm` = 0.2827
- `min_hole_to_hole_between` = ['via@[115.25, 46.42]', 'via@[114.78, 46.53]']
- `min_copper_to_edge_mm` = 0.58
- `min_copper_to_edge_at` = via GND @ [65.92, 139.12]
- `npth_count` = 6
- `min_silk_stroke_mm` = 0.15
- `min_silk_text_mm` = 1.0

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

- `WARN` **ASPECT_RATIO_TIGHT** — 1500 via(s) sit at or above 8.0:1 aspect ratio (1.6 mm board). Barrel plating thickness must be confirmed with the fabricator.

### G04 — Assembly geometry (IPC-7351B) · PASS

**Criterion.** Component courtyards do not overlap and nothing intrudes on the board edge keepout.

**Sources.** IPC-7351B (land pattern and courtyard requirements)

**Metrics.**

- `footprints_total` = 545
- `footprints_with_courtyard` = 488
- `courtyard_overlap_pairs` = 0

### G05 — Fabrication documentation · PASS

**Criterion.** The board carries the data a fabricator needs to build it to spec: a defined stackup, an impedance specification for any controlled-impedance net class, and a readable legend.

**Sources.** JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com; IPC-2581 / IPC-D-325 fabrication data requirements

**Metrics.**

- `copper_layers` = ['F.Cu', 'GND', 'PWR', 'SIG', 'GND5', 'B.Cu']
- `copper_layer_count` = 6
- `stackup_defined` = True
- `differential_netclasses` = ['AUDIO_OUTPUT', 'POWER', 'USB_DIFF']
- `silkscreen_text_items` = 261
- `silkscreen_items` = 1644
- `fiducial_candidates` = ['FID1', 'FID4', 'FID7', 'FID3', 'FID6', 'FID2', 'FID5']

### G06 — Drill-to-copper clearance · WARN

**Criterion.** Every drilled hole keeps the fabricator's minimum clearance to copper it is not connected to, so the drill tolerance cannot break out into a neighbouring net.

**Sources.** JLCPCB capability sheet (multilayer, 1 oz outer / 0.5 oz inner), jlcpcb.com; IPC-6012 (qualification and performance, rigid boards)

**Assumptions.**

- Drill and copper are compared at their drawn positions; the fabricator's drill registration tolerance is additional to this gap.

**Metrics.**

- `hole_to_copper_limit_mm` = 0.28
- `min_hole_to_copper_mm` = 0.3001
- `min_hole_to_copper_between` = ['J101.', 'J101.A1/B12', 'F.Cu']

**Findings.**

- `WARN` **HOLE_TO_COPPER_TIGHT** — 55 hole/copper pair(s) sit between the 0.28 mm minimum and the 0.35 mm recommended clearance.

### G10 — Conductor ampacity (IPC-2221B) · WARN

**Criterion.** Every power conductor is wide enough to carry its budgeted DC current at a 10 K rise, on the layer it is drawn on.

**Sources.** IPC-2221B eq. 6-4, I = k*dT^0.44*A^0.725 (k=0.048 external, 0.024 internal); IPC-2152 (current capacity; 2221 retained as the conservative floor)

**Assumptions.**

- Copper weights taken from the board stackup.
- DC current budgets are the declared values in design_intent.RAILS and are upper bounds, not measurements. Where a rail declares its loads, each conductor is held to the current the solved copper network puts through it with every load at its maximum; otherwise to the full rail budget.

**Metrics.**

- `delta_t_k` = 10.0
- `layer_copper_mm` = {'F.Cu': 0.03503, 'GND': 0.01521, 'PWR': 0.01521, 'SIG': 0.01521, 'GND5': 0.01521, 'B.Cu': 0.03503}
- `rails` = {'VBUS': {'budget_a': 0.77, 'conductor_current_a': np.float64(0.69), 'current_basis': 'solved per segment', 'narrowest_mm': 0.36, 'layer': 'F.Cu', 'required_mm': np.float64(0.1799), 'capacity_a': 1.1411, 'margin_x': np.float64(1.654), 'capacity_at_double_copper_a': None}, 'VBUS_SENSE': {'budget_a': 0.001, 'conductor_current_a': 0.001, 'current_basis': 'full rail budget', 'narrowest_mm': 0.15, 'layer': 'F.Cu', 'required_mm': 0.0, 'capacity_a': 0.6049, 'margin_x': 604.867, 'capacity_at_double_copper_a': None}, '5V_SYS': {'budget_a': 0.69, 'conductor_current_a': np.float64(0.66), 'current_basis': 'solved per segment', 'narrowest_mm': 1.15, 'layer': 'PWR', 'required_mm': np.float64(1.0139), 'capacity_a': 0.7231, 'margin_x': np.float64(1.096), 'capacity_at_double_copper_a': None}, '5V_ANA': {'budget_a': 0.49, 'conductor_current_a': np.float64(0.49), 'current_basis': 'solved per segment', 'narrowest_mm': 0.8, 'layer': 'PWR', 'required_mm': np.float64(0.6723), 'capacity_a': 0.5558, 'margin_x': np.float64(1.134), 'capacity_at_double_copper_a': None}, '5V_ANA_F': {'budget_a': 0.49, 'conductor_current_a': np.float64(0.491), 'current_basis': 'solved per segment', 'narrowest_mm': 0.8, 'layer': 'F.Cu', 'required_mm': np.float64(0.1125), 'capacity_a': 2.0358, 'margin_x': np.float64(4.146), 'capacity_at_double_copper_a': None}, 'VPOS': {'budget_a': 0.25, 'conductor_current_a': np.float64(0.2679), 'current_basis': 'solved per segment', 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': np.float64(0.0488), 'capacity_a': 0.7451, 'margin_x': np.float64(2.781), 'capacity_at_double_copper_a': None}, 'VNEG': {'budget_a': 0.25, 'conductor_current_a': np.float64(0.2345), 'current_basis': 'solved per segment', 'narrowest_mm': 0.6, 'layer': 'PWR', 'required_mm': np.float64(0.2433), 'capacity_a': 0.4512, 'margin_x': np.float64(1.924), 'capacity_at_double_copper_a': None}, 'N4_VPOS_IV': {'budget_a': 0.02, 'conductor_current_a': 0.02, 'current_basis': 'full rail budget', 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0014, 'capacity_a': 0.7451, 'margin_x': 37.257, 'capacity_at_double_copper_a': None}, 'N4_VNEG_IV': {'budget_a': 0.02, 'conductor_current_a': 0.02, 'current_basis': 'full rail budget', 'narrowest_mm': 0.25, 'layer': 'PWR', 'required_mm': 0.0082, 'capacity_a': 0.2392, 'margin_x': 11.959, 'capacity_at_double_copper_a': None}, '3V3D': {'budget_a': 0.17, 'conductor_current_a': 0.17, 'current_basis': 'full rail budget', 'narrowest_mm': 0.4, 'layer': 'PWR', 'required_mm': 0.1561, 'capacity_a': 0.3363, 'margin_x': 1.978, 'capacity_at_double_copper_a': None}, '3V3A': {'budget_a': 0.025, 'conductor_current_a': 0.025, 'current_basis': 'full rail budget', 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0111, 'capacity_a': 0.273, 'margin_x': 10.919, 'capacity_at_double_copper_a': None}, '3V3M': {'budget_a': 0.09, 'conductor_current_a': 0.09, 'current_basis': 'full rail budget', 'narrowest_mm': 0.4, 'layer': 'PWR', 'required_mm': 0.0649, 'capacity_a': 0.3363, 'margin_x': 3.736, 'capacity_at_double_copper_a': None}, 'N2_V33_CPLD': {'budget_a': 0.04, 'conductor_current_a': 0.04, 'current_basis': 'full rail budget', 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0212, 'capacity_a': 0.273, 'margin_x': 6.824, 'capacity_at_double_copper_a': None}, 'N2_J201_3V3': {'budget_a': 0.05, 'conductor_current_a': 0.05, 'current_basis': 'full rail budget', 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0048, 'capacity_a': 0.7451, 'margin_x': 14.903, 'capacity_at_double_copper_a': None}, '1V3': {'budget_a': 0.06, 'conductor_current_a': 0.06, 'current_basis': 'full rail budget', 'narrowest_mm': 0.4, 'layer': 'PWR', 'required_mm': 0.0371, 'capacity_a': 0.3363, 'margin_x': 5.605, 'capacity_at_double_copper_a': None}, 'DVCC': {'budget_a': 0.015, 'conductor_current_a': 0.015, 'current_basis': 'full rail budget', 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0055, 'capacity_a': 0.273, 'margin_x': 18.198, 'capacity_at_double_copper_a': None}, 'VCCA': {'budget_a': 0.003, 'conductor_current_a': 0.003, 'current_basis': 'full rail budget', 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0006, 'capacity_a': 0.273, 'margin_x': 90.992, 'capacity_at_double_copper_a': None}, 'AVCC_L': {'budget_a': 0.008, 'conductor_current_a': 0.008, 'current_basis': 'full rail budget', 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0023, 'capacity_a': 0.273, 'margin_x': 34.122, 'capacity_at_double_copper_a': None}, 'AVCC_R': {'budget_a': 0.008, 'conductor_current_a': 0.008, 'current_basis': 'full rail budget', 'narrowest_mm': 0.3, 'layer': 'PWR', 'required_mm': 0.0023, 'capacity_a': 0.273, 'margin_x': 34.122, 'capacity_at_double_copper_a': None}, 'VREF': {'budget_a': 0.001, 'conductor_current_a': 0.001, 'current_basis': 'full rail budget', 'narrowest_mm': 0.2, 'layer': 'PWR', 'required_mm': 0.0001, 'capacity_a': 0.2035, 'margin_x': 203.45, 'capacity_at_double_copper_a': None}, 'N5_CP': {'budget_a': 0.36, 'conductor_current_a': 0.36, 'current_basis': 'full rail budget', 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0733, 'capacity_a': 0.7451, 'margin_x': 2.07, 'capacity_at_double_copper_a': None}, 'N5_C1P': {'budget_a': 0.36, 'conductor_current_a': 0.36, 'current_basis': 'full rail budget', 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0733, 'capacity_a': 0.7451, 'margin_x': 2.07, 'capacity_at_double_copper_a': None}, 'N5_C1N': {'budget_a': 0.36, 'conductor_current_a': 0.36, 'current_basis': 'full rail budget', 'narrowest_mm': 0.2, 'layer': 'F.Cu', 'required_mm': 0.0733, 'capacity_a': 0.7451, 'margin_x': 2.07, 'capacity_at_double_copper_a': None}}

**Findings.**

- `WARN` **AMPACITY_MARGIN** — 5V_SYS: narrowest conductor has only 1.10x margin over the 0.66 A it carries (solved per segment).
- `WARN` **AMPACITY_MARGIN** — 5V_ANA: narrowest conductor has only 1.13x margin over the 0.49 A it carries (solved per segment).

### G11 — Via ampacity · WARN

**Criterion.** Each rail has enough plated barrel area at every layer transition to carry its budgeted current.

**Sources.** IPC-2221B eq. 6-4, I = k*dT^0.44*A^0.725 (k=0.048 external, 0.024 internal); JLCPCB: 18 um average through-hole plating

**Assumptions.**

- Barrel plating assumed 18 um (fabricator stated average).
- A via barrel is evaluated with the IPC-2221B internal constant because it is enclosed by laminate.

**Metrics.**

- `single_via_capacity_a` = {'0.2': 0.5272, '0.3': 0.7073, '0.4': 0.8714}
- `rails` = {'VBUS': {'budget_a': 0.77, 'via_current_a': np.float64(0.2293), 'current_basis': 'solved per via', 'weakest_via_capacity_a': 0.8714, 'margin_x': np.float64(3.8), 'at': [48.9, 72.6]}, 'VBUS_SENSE': {'budget_a': 0.001, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 527.18, 'at': [45.65, 83.8]}, '5V_SYS': {'budget_a': 0.69, 'via_current_a': np.float64(0.66), 'current_basis': 'solved per via', 'weakest_via_capacity_a': 0.8714, 'margin_x': np.float64(1.32), 'at': [49.6, 121.5]}, '5V_ANA': {'budget_a': 0.49, 'via_current_a': np.float64(0.49), 'current_basis': 'solved per via', 'weakest_via_capacity_a': 0.8714, 'margin_x': np.float64(1.78), 'at': [63.3, 127.3875]}, '5V_ANA_F': {'budget_a': 0.49, 'via_current_a': np.float64(0.49), 'current_basis': 'solved per via', 'weakest_via_capacity_a': 0.8714, 'margin_x': np.float64(1.78), 'at': [65.0, 125.25]}, 'VPOS': {'budget_a': 0.25, 'via_current_a': np.float64(0.2679), 'current_basis': 'solved per via', 'weakest_via_capacity_a': 0.5272, 'margin_x': np.float64(1.97), 'at': [67.55, 128.949999]}, 'VNEG': {'budget_a': 0.25, 'via_current_a': np.float64(0.2533), 'current_basis': 'solved per via', 'weakest_via_capacity_a': 0.5272, 'margin_x': np.float64(2.08), 'at': [75.35, 136.45]}, 'N4_VPOS_IV': {'budget_a': 0.02, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 26.36, 'at': [103.85, 98.1]}, 'N4_VNEG_IV': {'budget_a': 0.02, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 26.36, 'at': [137.9, 118.8]}, '3V3D': {'budget_a': 0.17, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 3.1, 'at': [86.85, 55.75]}, '3V3A': {'budget_a': 0.025, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 21.09, 'at': [102.9159, 82.0523]}, '3V3M': {'budget_a': 0.09, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 5.86, 'at': [43.7, 63.55]}, 'N2_V33_CPLD': {'budget_a': 0.04, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 13.18, 'at': [86.91, 53.6]}, '1V3': {'budget_a': 0.06, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 8.79, 'at': [53.79, 135.2]}, 'DVCC': {'budget_a': 0.015, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 35.15, 'at': [88.41, 65.0]}, 'VCCA': {'budget_a': 0.003, 'weakest_transition_a': 0.7073, 'via_count': 1, 'margin_x': 235.78, 'at': [82.0, 70.5]}, 'AVCC_L': {'budget_a': 0.008, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 65.9, 'at': [90.7, 65.4625]}, 'AVCC_R': {'budget_a': 0.008, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 65.9, 'at': [94.7, 88.175]}, 'VREF': {'budget_a': 0.001, 'weakest_transition_a': 0.5272, 'via_count': 1, 'margin_x': 527.18, 'at': [95.05, 79.0]}}

**Findings.**

- `WARN` **VIA_AMPACITY_MARGIN** — 5V_SYS: weakest via has 1.32x margin (0.660 A solved).

### G12 — DC IR drop (solved) · PASS

**Criterion.** Static voltage drop from each rail's source to its loads stays inside the rail budget, solved as a nodal network on the actual copper.

**Sources.** Nodal analysis of the extracted copper graph; IPC-2152 (conductor resistance basis)

**Assumptions.**

- Return-path (GND) drop is excluded: GND is a filled plane on four layers and its spreading resistance is not extracted here.
- The rail current budget is distributed equally across the rail's load pads; R_eff values reported per pad are independent of that split.
- Copper resistivity 1.724e-8 ohm*m at 20 C.

**Metrics.**

- `rails` = {'VBUS': {'source': 'U102', 'load_pads': 8, 'connected_pads': 8, 'open_pads': 0, 'worst_pad': 'U502.1', 'worst_r_eff_ohm': 0.01535, 'worst_drop_mv': 1.477, 'budget_mv': 150.0, 'budget_pct': 3.0, 'nodes': 64}, 'VBUS_SENSE': {'source': 'U201', 'load_pads': 4, 'connected_pads': 4, 'open_pads': 0, 'worst_pad': 'C103.1', 'worst_r_eff_ohm': 0.09021, 'worst_drop_mv': 0.023, 'budget_mv': 50.0, 'budget_pct': 1.0, 'nodes': 31}, '5V_SYS': {'source': 'U503', 'load_pads': 12, 'connected_pads': 12, 'open_pads': 0, 'worst_pad': 'K603.1', 'worst_r_eff_ohm': 0.13786, 'worst_drop_mv': 7.927, 'budget_mv': 150.0, 'budget_pct': 3.0, 'nodes': 150}, '5V_ANA': {'source': 'U503', 'load_pads': 4, 'connected_pads': 4, 'open_pads': 0, 'worst_pad': 'FB501.1', 'worst_r_eff_ohm': 0.02671, 'worst_drop_mv': 3.272, 'budget_mv': 100.0, 'budget_pct': 2.0, 'nodes': 45}, '5V_ANA_F': {'source': 'U501', 'load_pads': 5, 'connected_pads': 5, 'open_pads': 0, 'worst_pad': 'R535.1', 'worst_r_eff_ohm': 0.01443, 'worst_drop_mv': 1.414, 'budget_mv': 100.0, 'budget_pct': 2.0, 'nodes': 48}, 'VPOS': {'source': 'U501', 'load_pads': 66, 'connected_pads': 66, 'open_pads': 0, 'worst_pad': 'TP707.1', 'worst_r_eff_ohm': 0.2851, 'worst_drop_mv': 1.08, 'budget_mv': 38.5, 'budget_pct': 1.0, 'nodes': 638}, 'VNEG': {'source': 'U501', 'load_pads': 42, 'connected_pads': 42, 'open_pads': 0, 'worst_pad': 'C659.2', 'worst_r_eff_ohm': 0.17915, 'worst_drop_mv': 1.066, 'budget_mv': 38.5, 'budget_pct': 1.0, 'nodes': 410}, 'N4_VPOS_IV': {'source': 'U403', 'load_pads': 7, 'connected_pads': 7, 'open_pads': 0, 'worst_pad': 'D411.1', 'worst_r_eff_ohm': 0.07964, 'worst_drop_mv': 0.228, 'budget_mv': 35.0, 'budget_pct': 1.0, 'nodes': 69}, 'N4_VNEG_IV': {'source': 'U403', 'load_pads': 7, 'connected_pads': 7, 'open_pads': 0, 'worst_pad': 'C443.2', 'worst_r_eff_ohm': 0.10707, 'worst_drop_mv': 0.306, 'budget_mv': 35.0, 'budget_pct': 1.0, 'nodes': 80}, '3V3D': {'source': 'U504', 'load_pads': 32, 'connected_pads': 32, 'open_pads': 0, 'worst_pad': 'J202.1', 'worst_r_eff_ohm': 0.12539, 'worst_drop_mv': 0.666, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 280}, '3V3A': {'source': 'U302', 'load_pads': 20, 'connected_pads': 20, 'open_pads': 0, 'worst_pad': 'R631.2', 'worst_r_eff_ohm': 0.1838, 'worst_drop_mv': 0.23, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 229}, '3V3M': {'source': 'U201', 'load_pads': 33, 'connected_pads': 33, 'open_pads': 0, 'worst_pad': 'R528.1', 'worst_r_eff_ohm': 0.22857, 'worst_drop_mv': 0.623, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 317}, 'N2_V33_CPLD': {'source': 'FB202', 'load_pads': 9, 'connected_pads': 9, 'open_pads': 0, 'worst_pad': 'U202.16', 'worst_r_eff_ohm': 0.05287, 'worst_drop_mv': 0.235, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 66}, 'N2_J201_3V3': {'source': 'R241', 'load_pads': 1, 'connected_pads': 1, 'open_pads': 0, 'worst_pad': 'J201.1', 'worst_r_eff_ohm': 0.01, 'worst_drop_mv': 0.5, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 4}, '1V3': {'source': 'U301', 'load_pads': 8, 'connected_pads': 8, 'open_pads': 0, 'worst_pad': 'R530.1', 'worst_r_eff_ohm': 0.25598, 'worst_drop_mv': 1.92, 'budget_mv': 13.0, 'budget_pct': 1.0, 'nodes': 113}, 'DVCC': {'source': 'U301', 'load_pads': 4, 'connected_pads': 4, 'open_pads': 0, 'worst_pad': 'R305.2', 'worst_r_eff_ohm': 0.069, 'worst_drop_mv': 0.259, 'budget_mv': 99.0, 'budget_pct': 3.0, 'nodes': 33}, 'VCCA': {'source': 'U301', 'load_pads': 3, 'connected_pads': 3, 'open_pads': 0, 'worst_pad': 'FB302.2', 'worst_r_eff_ohm': 0.05079, 'worst_drop_mv': 0.051, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 23}, 'AVCC_L': {'source': 'U301', 'load_pads': 6, 'connected_pads': 6, 'open_pads': 0, 'worst_pad': 'D405.2', 'worst_r_eff_ohm': 0.07051, 'worst_drop_mv': 0.094, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 55}, 'AVCC_R': {'source': 'U301', 'load_pads': 5, 'connected_pads': 5, 'open_pads': 0, 'worst_pad': 'D408.2', 'worst_r_eff_ohm': 0.09268, 'worst_drop_mv': 0.148, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 44}, 'VREF': {'source': 'U403', 'load_pads': 8, 'connected_pads': 8, 'open_pads': 0, 'worst_pad': 'TP709.1', 'worst_r_eff_ohm': 0.07998, 'worst_drop_mv': 0.01, 'budget_mv': 33.0, 'budget_pct': 1.0, 'nodes': 85}, 'N5_CP': {'source': 'U501', 'load_pads': 1, 'connected_pads': 1, 'open_pads': 0, 'worst_pad': 'C509.1', 'worst_r_eff_ohm': 0.00526, 'worst_drop_mv': 1.894, 'budget_mv': 100.0, 'budget_pct': 2.0, 'nodes': 4}, 'N5_C1P': {'source': 'U501', 'load_pads': 1, 'connected_pads': 1, 'open_pads': 0, 'worst_pad': 'C508.1', 'worst_r_eff_ohm': 0.00591, 'worst_drop_mv': 2.128, 'budget_mv': 100.0, 'budget_pct': 2.0, 'nodes': 4}, 'N5_C1N': {'source': 'U501', 'load_pads': 1, 'connected_pads': 1, 'open_pads': 0, 'worst_pad': 'C508.2', 'worst_r_eff_ohm': 0.00591, 'worst_drop_mv': 2.128, 'budget_mv': 100.0, 'budget_pct': 2.0, 'nodes': 4}}

### G13 — Decoupling placement and mounted resonance · WARN

**Criterion.** Every device supply pin has a high-frequency bypass capacitor close enough that the mounted loop inductance keeps its self-resonance above the frequencies the device actually needs decoupled.

**Sources.** C. R. Paul, Inductance: Loop and Partial, Wiley 2010, ch. 5; Ott, Electromagnetic Compatibility Engineering, ch. 11

**Assumptions.**

- Capacitor values are parsed from the footprint Value field.
- Mounting inductance counts the via pair under the capacitor plus the pad-to-via run; the capacitor's own ESL is taken as 0.6 nH for 0402 and 0.9 nH for 0603, typical MLCC values.

**Metrics.**

- `capacitors_parsed` = 147
- `pins_checked` = 78
- `worst_by_distance` = [{'pin': 'U102.6', 'net': 'VBUS', 'cap': 'C102', 'cap_value': '2.2 µF', 'distance_mm': 19.76, 'mount_inductance_nh': 1.621, 'mounted_srf_mhz': 2.02, 'local_vias': False}, {'pin': 'U606.12', 'net': 'VNEG', 'cap': 'C636', 'cap_value': '100 nF', 'distance_mm': 11.902, 'mount_inductance_nh': 0.288, 'mounted_srf_mhz': 16.89, 'local_vias': True}, {'pin': 'U603.3', 'net': 'VPOS', 'cap': 'C618', 'cap_value': '100 nF', 'distance_mm': 11.484, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U612.12', 'net': 'VNEG', 'cap': 'C619', 'cap_value': '100 nF', 'distance_mm': 11.414, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U603.12', 'net': 'VNEG', 'cap': 'C656', 'cap_value': '100 nF', 'distance_mm': 11.335, 'mount_inductance_nh': 0.288, 'mounted_srf_mhz': 16.89, 'local_vias': True}, {'pin': 'U505.5', 'net': '3V3M', 'cap': 'C515', 'cap_value': '100 nF', 'distance_mm': 11.213, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U606.3', 'net': 'VPOS', 'cap': 'C618', 'cap_value': '100 nF', 'distance_mm': 11.068, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U201.64', 'net': '3V3M', 'cap': 'C204', 'cap_value': '100 nF', 'distance_mm': 9.23, 'mount_inductance_nh': 0.288, 'mounted_srf_mhz': 16.89, 'local_vias': True}, {'pin': 'U201.32', 'net': '3V3M', 'cap': 'C221', 'cap_value': '1 µF', 'distance_mm': 8.504, 'mount_inductance_nh': 0.35, 'mounted_srf_mhz': 4.5, 'local_vias': True}, {'pin': 'U101.5', 'net': '3V3M', 'cap': 'C502', 'cap_value': '2.2 µF', 'distance_mm': 8.331, 'mount_inductance_nh': 1.489, 'mounted_srf_mhz': 2.2, 'local_vias': False}, {'pin': 'U503.4', 'net': '5V_SYS', 'cap': 'C501', 'cap_value': '1 µF', 'distance_mm': 7.701, 'mount_inductance_nh': 0.26, 'mounted_srf_mhz': 4.67, 'local_vias': True}, {'pin': 'U611.12', 'net': 'VNEG', 'cap': 'C619', 'cap_value': '100 nF', 'distance_mm': 7.143, 'mount_inductance_nh': 1.172, 'mounted_srf_mhz': 11.96, 'local_vias': False}, {'pin': 'U201.19', 'net': '3V3M', 'cap': 'C205', 'cap_value': '100 nF', 'distance_mm': 6.956, 'mount_inductance_nh': 0.288, 'mounted_srf_mhz': 16.89, 'local_vias': True}, {'pin': 'U201.1', 'net': '3V3M', 'cap': 'C204', 'cap_value': '100 nF', 'distance_mm': 6.497, 'mount_inductance_nh': 0.288, 'mounted_srf_mhz': 16.89, 'local_vias': True}, {'pin': 'U619.4', 'net': 'VNEG', 'cap': 'C665', 'cap_value': '100 nF', 'distance_mm': 6.475, 'mount_inductance_nh': 1.199, 'mounted_srf_mhz': 11.87, 'local_vias': False}]
- `median_distance_mm` = 3.201

**Findings.**

- `WARN` **BYPASS_DISTANCE** — U303.1 (3V3D): nearest bypass C311 (1 µF) is 3.20 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U608.7 (3V3D): nearest bypass C630 (100 nF) is 3.17 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U614.4 (VNEG): nearest bypass C660 (100 nF) is 5.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U614.8 (VPOS): nearest bypass C660 (100 nF) is 3.98 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U618.4 (VNEG): nearest bypass C664 (100 nF) is 5.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U618.8 (VPOS): nearest bypass C664 (100 nF) is 3.98 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U616.4 (VNEG): nearest bypass C662 (100 nF) is 5.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U616.8 (VPOS): nearest bypass C662 (100 nF) is 3.98 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.1 (3V3M): nearest bypass C204 (100 nF) is 6.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.13 (3V3M): nearest bypass C204 (100 nF) is 3.87 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.19 (3V3M): nearest bypass C205 (100 nF) is 6.96 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.32 (3V3M): nearest bypass C221 (1 µF) is 8.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U201.64 (3V3M): nearest bypass C204 (100 nF) is 9.23 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U619.4 (VNEG): nearest bypass C665 (100 nF) is 6.47 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U404.4 (N4_VNEG_IV): nearest bypass C426 (100 nF) is 4.13 mm away, beyond the 3.0 mm high-frequency guideline.
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
- `WARN` **BYPASS_DISTANCE** — U503.4 (5V_SYS): nearest bypass C501 (1 µF) is 7.70 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U606.3 (VPOS): nearest bypass C618 (100 nF) is 11.07 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U606.12 (VNEG): nearest bypass C636 (100 nF) is 11.90 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U620.4 (VNEG): nearest bypass C666 (100 nF) is 5.50 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U620.8 (VPOS): nearest bypass C666 (100 nF) is 3.98 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U604.8 (3V3D): nearest bypass C622 (100 nF) is 4.28 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U205.5 (3V3D): nearest bypass C222 (100 nF) is 3.08 mm away, beyond the 3.0 mm high-frequency guideline.
- `WARN` **BYPASS_DISTANCE** — U607.5 (3V3D): nearest bypass C223 (100 nF) is 3.60 mm away, beyond the 3.0 mm high-frequency guideline.

### G20 — USB high-speed differential pair · WARN

**Criterion.** The USB 2.0 high-speed pair is routed as a matched, tightly coupled pair with a continuous reference and the intra-pair skew well inside the specification limit.

**Sources.** USB 2.0 specification rev 2.0 §7.1.1.3 and USB-IF HS layout guidance; IPC-2251 (design guide for high-speed interconnect)

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
- `pair_track_widths_mm` = [0.16, 0.17, 0.18, 0.2]
- `spacing_to_others_rule_mm` = 0.48
- `min_spacing_to_other_signal_mm` = 0.31
- `min_spacing_offender` = ['CC1', 'F.Cu']
- `usb_sections` = [{'kind': 'coupled', 'width_mm': 0.17, 'edge_gap_mm': 0.215, 'length_mm': 10.02, 'zdiff_ohm': {'nominal': 89.2, 'prepreg -10 %, er +0.2, copper +5 um': 82.3, 'prepreg +10 %, er -0.2, copper -5 um': 96.8}}, {'kind': 'coupled', 'width_mm': 0.18, 'edge_gap_mm': 0.32, 'length_mm': 2.47, 'zdiff_ohm': {'nominal': 90.0, 'prepreg -10 %, er +0.2, copper +5 um': 82.2, 'prepreg +10 %, er -0.2, copper -5 um': 98.1}}, {'kind': 'split', 'width_mm': 0.2, 'length_mm': 0.4, 'zdiff_ohm': {'nominal': 88.7, 'prepreg -10 %, er +0.2, copper +5 um': 81.8, 'prepreg +10 %, er -0.2, copper -5 um': 97.9}}, {'kind': 'pin escape', 'width_mm': 0.16, 'length_mm': 3.05, 'zdiff_ohm': {'nominal': 99.3, 'prepreg -10 %, er +0.2, copper +5 um': 92.1, 'prepreg +10 %, er -0.2, copper -5 um': 109.9}}, {'kind': 'pin escape', 'width_mm': 0.2, 'length_mm': 8.07, 'zdiff_ohm': {'nominal': 88.7, 'prepreg -10 %, er +0.2, copper +5 um': 81.8, 'prepreg +10 %, er -0.2, copper -5 um': 97.9}}]
- `usb_impedance_basis` = 2-D field solve (tline.py): F.Cu over 0.0994 mm 3313 prepreg er 4.1, mask 0.015 mm; build corners +/-10 % prepreg, +/-0.2 er, +/-5 um copper

**Findings.**

- `WARN` **USB_SKEW_MARGIN** — Intra-pair skew 2.15 mm uses more than half of the 3.81 mm budget.

_2 informational finding(s) in the JSON result._

### G21 — Clock routing and aggressor spacing · PASS

**Criterion.** Clock nets are routed short, with few layer changes, and keep enough distance from analog audio nets that crosstalk stays below the audio noise floor.

**Sources.** H. Ott, Electromagnetic Compatibility Engineering, ch. 10-12; IPC-2251 (design guide for high-speed interconnect)

**Assumptions.**

- Crosstalk is judged by edge-to-edge spacing on shared or adjacent layers, not by a solved coupled-line model; a full extraction needs the dielectric build.

**Metrics.**

- `clock_to_audio_rule_mm` = 1.0
- `clock_nets_present` = 29
- `audio_nets_present` = 36
- `min_clock_to_audio_mm` = 1.0461
- `min_clock_to_audio_between` = ['N2_CAP_CK', 'N4_IVL_N', 'F.Cu']
- `clock_via_limit` = 4
- `clock_lengths_mm` = {'LRCLK_FB': 39.79, 'N2_CAP_CK': 37.41, 'N2_CAP_WS': 30.19, 'LINK_SCK': 27.91, 'N2_LINK_SCK_BUF': 27.79, 'CPLD_JTCK': 26.16, 'N2_CAP_SD': 24.72, 'SWCLK': 20.83, 'BCLK': 16.64, 'LRCLK': 15.9, 'SDATA': 15.2, 'N2_HSE_OUT': 15.02, 'N2_HSE_IN': 12.47, 'N6_REFMCK': 11.96, 'N6_MCK_BUF': 10.68}

### G22 — Return path and reference continuity · WARN

**Criterion.** Signal layers are referenced to a ground plane, and vias that change reference have a stitching via close enough to carry the return current.

**Sources.** H. Ott, Electromagnetic Compatibility Engineering, ch. 10-12; IPC-2251 §5 (reference planes and return current)

**Metrics.**

- `copper_layers` = ['F.Cu', 'GND', 'PWR', 'SIG', 'GND5', 'B.Cu']
- `zone_nets_by_layer` = {'F.Cu': ['GND'], 'B.Cu': ['GND'], 'GND': ['GND'], 'PWR': ['GND'], 'SIG': ['GND'], 'GND5': ['GND']}
- `ground_plane_layers` = ['F.Cu', 'GND', 'PWR', 'SIG', 'GND5', 'B.Cu']
- `ground_stitching_vias` = 751
- `stitching_distance_rule_mm` = 2.0
- `signal_vias_checked` = 241
- `worst_stitching_distance_mm` = 4.68
- `worst_stitching_net` = LINK_MOSI

**Findings.**

- `WARN` **RETURN_PATH_STITCHING** — 99 layer-changing signal via(s) have no ground via within 2.0 mm, so the return current must detour.

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
- Each net is measured along its load-current path between the parts in design_intent.OUTPUT_SERIES_TERMINALS; the high-value sense-divider taps on LEG_xx carry no headphone current and are excluded.

**Metrics.**

- `load_ohm` = 32.0
- `trace_resistance_budget_ohm` = 0.1
- `channel_mismatch_budget_ohm` = 0.02
- `output_net_resistance_ohm` = {'JACK_LN': 0.03112, 'JACK_LP': 0.02537, 'JACK_RN': 0.00871, 'JACK_RP': 0.02286, 'LEG_LN': 0.00211, 'LEG_LP': 0.00211, 'LEG_RN': 0.0029, 'LEG_RP': 0.00249, 'N4_LN_OUT': 0.02033, 'N4_LP_OUT': 0.01841, 'N4_RN_OUT': 0.01998, 'N4_RP_OUT': 0.02585}
- `worst_damping_factor` = 1028.4
- `worst_damping_net` = JACK_LN
- `channel_mismatch_ohm` = {'JACK_LP/JACK_RP': 0.00251, 'JACK_LN/JACK_RN': 0.0224, 'LEG_LP/LEG_RP': 0.00038, 'LEG_LN/LEG_RN': 0.00079}

**Findings.**

- `WARN` **CHANNEL_MISMATCH** — 1 channel pair(s) differ by more than 0.02 ohm of copper.

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
- `ports` = {'CC1': {'parts': ['J101', 'R101', 'R103', 'TP726', 'U103'], 'protection': ['U103'], 'connector': ['J101'], 'stub_mm': 8.41}, 'CC2': {'parts': ['J101', 'R102', 'R104', 'TP727', 'U103'], 'protection': ['U103'], 'connector': ['J101'], 'stub_mm': 18.71}, 'JACK_LN': {'parts': ['D703', 'J701', 'K602'], 'protection': ['D703'], 'connector': ['J701'], 'stub_mm': 4.03}, 'JACK_LP': {'parts': ['D701', 'D708', 'J701', 'J702', 'K601'], 'protection': ['D701', 'D708'], 'connector': ['J701', 'J702'], 'stub_mm': 3.35}, 'JACK_RN': {'parts': ['D704', 'J701', 'K604'], 'protection': ['D704'], 'connector': ['J701'], 'stub_mm': 4.03}, 'JACK_RP': {'parts': ['D702', 'D707', 'J701', 'J702', 'K603'], 'protection': ['D702', 'D707'], 'connector': ['J701', 'J702'], 'stub_mm': 3.86}, 'N1_SHIELD': {'parts': ['C101', 'J101', 'R107'], 'protection': [], 'connector': ['J101'], 'ground_bond': ['C101', 'R107']}, 'USB_DN': {'parts': ['J101', 'U101', 'U201'], 'protection': ['U101'], 'connector': ['J101'], 'stub_mm': 4.56}, 'USB_DP': {'parts': ['J101', 'U101', 'U201'], 'protection': ['U101'], 'connector': ['J101'], 'stub_mm': 7.95}, 'VBUS': {'parts': ['C102', 'D102', 'J101', 'R109', 'TP736', 'TP753', 'U102', 'U502'], 'protection': ['D102'], 'connector': ['J101'], 'ground_bond': ['C102'], 'stub_mm': 6.21}}

**Findings.**

- `WARN` **ESD_STUB_LONG** — 1 port net(s) reach their clamp through more than 10.0 mm of copper, so stub inductance raises the ESD let-through.

### G40 — Power distribution network impedance (LTspice) · PASS

**Criterion.** At the hardest-to-decouple pin of each rail, the simulated PDN impedance stays below the target impedance across the control band, using capacitor and interconnect parasitics extracted from the layout.

**Sources.** L. Smith / E. Bogatin, Principles of Power Integrity (target impedance and decoupling); C. R. Paul, Inductance: Loop and Partial (via-pair loop inductance)

**Assumptions.**

- The outer-to-plane dielectric height is not declared by the board, so each rail is simulated at 0.09, 0.12 and 0.2 mm and the gate reports the worst case.
- Capacitor ESR/ESL come from the placed package size; the regulator is modelled as an ideal source behind the solved copper resistance and the loop inductance of the feed path.

**Metrics.**

- `band_hz` = [100000.0, 100000000.0]
- `plane_height_sweep_mm` = {'min': 0.09, 'typical': 0.12, 'max': 0.2}
- `rails` = {'1V3': {'z_at_mclk_ohm': 0.1821, 'z_target_ohm': 0.2167, 'z_max_in_band_ohm': 0.8648, 'z_at_100khz_ohm': 0.0117, 'z_at_100mhz_ohm': 0.8648, 'decoupling_bandwidth_hz': 26311700, 'cap_count': 3, 'local_cap_count': 2, 'total_capacitance_uf': 3.3, 'worst_pin': 'U301.21', 'nearest_cap_mm': 2.36, 'margin_db_at_mclk': 1.51, 'assumed_current_a': 0.06, 'passes_if_transient_below_a': 0.0714, 'track_width_mm': 0.4}, '3V3D': {'z_at_mclk_ohm': 0.2519, 'z_target_ohm': 0.9706, 'z_max_in_band_ohm': 1.1533, 'z_at_100khz_ohm': 0.0851, 'z_at_100mhz_ohm': 1.1533, 'decoupling_bandwidth_hz': 84216694, 'cap_count': 11, 'local_cap_count': 2, 'total_capacitance_uf': 11.81, 'worst_pin': 'U208.8', 'nearest_cap_mm': 8.49, 'margin_db_at_mclk': 11.72, 'assumed_current_a': 0.17, 'passes_if_transient_below_a': 0.6551, 'track_width_mm': 0.4}, '3V3M': {'z_at_mclk_ohm': 0.4278, 'z_target_ohm': 1.8333, 'z_max_in_band_ohm': 1.9215, 'z_at_100khz_ohm': 0.1435, 'z_at_100mhz_ohm': 1.9215, 'decoupling_bandwidth_hz': 95415938, 'cap_count': 14, 'local_cap_count': 0, 'total_capacitance_uf': 6.5, 'worst_pin': 'U505.5', 'nearest_cap_mm': 16.42, 'margin_db_at_mclk': 12.64, 'assumed_current_a': 0.09, 'passes_if_transient_below_a': 0.3857, 'track_width_mm': 0.4}, '5V_ANA_F': {'z_at_mclk_ohm': 0.2482, 'z_target_ohm': 0.4, 'z_max_in_band_ohm': 1.0991, 'z_at_100khz_ohm': 0.0113, 'z_at_100mhz_ohm': 1.0991, 'decoupling_bandwidth_hz': 36389774, 'cap_count': 1, 'local_cap_count': 1, 'total_capacitance_uf': 10.0, 'worst_pin': 'U501.8', 'nearest_cap_mm': 6.18, 'margin_db_at_mclk': 4.14, 'assumed_current_a': 0.25, 'passes_if_transient_below_a': 0.4028, 'track_width_mm': 0.8}, '5V_SYS': {'z_at_mclk_ohm': 0.1641, 'z_target_ohm': 1.4706, 'z_max_in_band_ohm': 0.7415, 'z_at_100khz_ohm': 0.0111, 'z_at_100mhz_ohm': 0.7415, 'decoupling_bandwidth_hz': None, 'cap_count': 3, 'local_cap_count': 1, 'total_capacitance_uf': 3.3, 'worst_pin': 'U503.4', 'nearest_cap_mm': 8.96, 'margin_db_at_mclk': 19.05, 'assumed_current_a': 0.17, 'passes_if_transient_below_a': 1.5233, 'track_width_mm': 1.0}, 'AVCC_L': {'z_at_mclk_ohm': 0.2243, 'z_target_ohm': 4.125, 'z_max_in_band_ohm': 1.1056, 'z_at_100khz_ohm': 0.0123, 'z_at_100mhz_ohm': 1.1056, 'decoupling_bandwidth_hz': None, 'cap_count': 2, 'local_cap_count': 2, 'total_capacitance_uf': 2.3, 'worst_pin': 'U301.15', 'nearest_cap_mm': 2.44, 'margin_db_at_mclk': 25.29, 'assumed_current_a': 0.008, 'passes_if_transient_below_a': 0.1471, 'track_width_mm': 0.3}, 'AVCC_R': {'z_at_mclk_ohm': 0.195, 'z_target_ohm': 4.125, 'z_max_in_band_ohm': 0.9757, 'z_at_100khz_ohm': 0.0123, 'z_at_100mhz_ohm': 0.9757, 'decoupling_bandwidth_hz': None, 'cap_count': 2, 'local_cap_count': 2, 'total_capacitance_uf': 2.3, 'worst_pin': 'U301.16', 'nearest_cap_mm': 2.05, 'margin_db_at_mclk': 26.51, 'assumed_current_a': 0.008, 'passes_if_transient_below_a': 0.1692, 'track_width_mm': 0.3}, 'DVCC': {'z_at_mclk_ohm': 0.2562, 'z_target_ohm': 11.0, 'z_max_in_band_ohm': 1.2369, 'z_at_100khz_ohm': 0.0128, 'z_at_100mhz_ohm': 1.2369, 'decoupling_bandwidth_hz': None, 'cap_count': 2, 'local_cap_count': 2, 'total_capacitance_uf': 2.3, 'worst_pin': 'U301.18', 'nearest_cap_mm': 2.53, 'margin_db_at_mclk': 32.66, 'assumed_current_a': 0.015, 'passes_if_transient_below_a': 0.6441, 'track_width_mm': 0.25}, 'N4_VNEG_IV': {'z_at_mclk_ohm': 0.2203, 'z_target_ohm': 1.75, 'z_max_in_band_ohm': 1.0396, 'z_at_100khz_ohm': 0.0178, 'z_at_100mhz_ohm': 1.0396, 'decoupling_bandwidth_hz': None, 'cap_count': 3, 'local_cap_count': 1, 'total_capacitance_uf': 220.2, 'worst_pin': 'U404.4', 'nearest_cap_mm': 5.44, 'margin_db_at_mclk': 18.0, 'assumed_current_a': 0.02, 'passes_if_transient_below_a': 0.1588, 'track_width_mm': 0.5}, 'N4_VPOS_IV': {'z_at_mclk_ohm': 0.2647, 'z_target_ohm': 1.75, 'z_max_in_band_ohm': 1.2523, 'z_at_100khz_ohm': 0.0111, 'z_at_100mhz_ohm': 1.2523, 'decoupling_bandwidth_hz': None, 'cap_count': 3, 'local_cap_count': 1, 'total_capacitance_uf': 220.2, 'worst_pin': 'U403.8', 'nearest_cap_mm': 4.06, 'margin_db_at_mclk': 16.4, 'assumed_current_a': 0.02, 'passes_if_transient_below_a': 0.1322, 'track_width_mm': 0.4}, 'VBUS': {'z_at_mclk_ohm': 0.2752, 'z_target_ohm': 0.9615, 'z_max_in_band_ohm': 1.2192, 'z_at_100khz_ohm': 0.0111, 'z_at_100mhz_ohm': 1.2192, 'decoupling_bandwidth_hz': 78867722, 'cap_count': 1, 'local_cap_count': 0, 'total_capacitance_uf': 2.2, 'worst_pin': 'U102.6', 'nearest_cap_mm': 23.64, 'margin_db_at_mclk': 10.86, 'assumed_current_a': 0.26, 'passes_if_transient_below_a': 0.9083, 'track_width_mm': 1.0}, 'VCCA': {'z_at_mclk_ohm': 0.2208, 'z_target_ohm': 11.0, 'z_max_in_band_ohm': 1.0915, 'z_at_100khz_ohm': 0.0128, 'z_at_100mhz_ohm': 1.0915, 'decoupling_bandwidth_hz': None, 'cap_count': 2, 'local_cap_count': 2, 'total_capacitance_uf': 2.3, 'worst_pin': 'U301.17', 'nearest_cap_mm': 1.99, 'margin_db_at_mclk': 33.95, 'assumed_current_a': 0.003, 'passes_if_transient_below_a': 0.1494, 'track_width_mm': 0.25}, 'VNEG': {'z_at_mclk_ohm': 0.3431, 'z_target_ohm': 1.1, 'z_max_in_band_ohm': 1.5415, 'z_at_100khz_ohm': 0.0455, 'z_at_100mhz_ohm': 1.5415, 'decoupling_bandwidth_hz': 71413019, 'cap_count': 19, 'local_cap_count': 0, 'total_capacitance_uf': 31.6, 'worst_pin': 'U606.12', 'nearest_cap_mm': 22.84, 'margin_db_at_mclk': 10.12, 'assumed_current_a': 0.035, 'passes_if_transient_below_a': 0.1122, 'track_width_mm': 0.4}, 'VPOS': {'z_at_mclk_ohm': 0.3446, 'z_target_ohm': 1.0694, 'z_max_in_band_ohm': 1.5488, 'z_at_100khz_ohm': 0.0481, 'z_at_100mhz_ohm': 1.5488, 'decoupling_bandwidth_hz': 69109830, 'cap_count': 19, 'local_cap_count': 0, 'total_capacitance_uf': 31.6, 'worst_pin': 'U603.3', 'nearest_cap_mm': 20.73, 'margin_db_at_mclk': 9.84, 'assumed_current_a': 0.036, 'passes_if_transient_below_a': 0.1117, 'track_width_mm': 0.4}}
- `criterion_frequency_hz` = 22579200.0

_1 informational finding(s) in the JSON result._

### G41 — Headphone output loading and damping (LTspice) · PASS

**Criterion.** With the solved output-path resistance in circuit, the amplifier still meets its damping-factor target into the rated load and the two channels stay matched.

**Sources.** D. Self, Audio Power Amplifier Design

**Assumptions.**

- The amplifier is modelled as an ideal source, so the simulated damping factor is the ceiling the copper allows; the active stage can only reduce it.

**Metrics.**

- `load_ohm` = 32.0
- `min_damping_factor` = 100.0
- `outputs` = {'JACK_LN': {'r_copper_ohm': 0.03112, 'insertion_loss_db': -0.0084, 'damping_factor': 1028.4}, 'JACK_LP': {'r_copper_ohm': 0.02537, 'insertion_loss_db': -0.0069, 'damping_factor': 1261.2}, 'JACK_RN': {'r_copper_ohm': 0.00871, 'insertion_loss_db': -0.0024, 'damping_factor': 3673.5}, 'JACK_RP': {'r_copper_ohm': 0.02286, 'insertion_loss_db': -0.0062, 'damping_factor': 1399.6}, 'LEG_LN': {'r_copper_ohm': 0.00211, 'insertion_loss_db': -0.0006, 'damping_factor': 15179.6}, 'LEG_LP': {'r_copper_ohm': 0.00211, 'insertion_loss_db': -0.0006, 'damping_factor': 15158.4}, 'LEG_RN': {'r_copper_ohm': 0.0029, 'insertion_loss_db': -0.0008, 'damping_factor': 11024.5}, 'LEG_RP': {'r_copper_ohm': 0.00249, 'insertion_loss_db': -0.0007, 'damping_factor': 12866.4}, 'N4_LN_OUT': {'r_copper_ohm': 0.02033, 'insertion_loss_db': -0.0055, 'damping_factor': 1574.3}, 'N4_LP_OUT': {'r_copper_ohm': 0.01841, 'insertion_loss_db': -0.005, 'damping_factor': 1738.2}, 'N4_RN_OUT': {'r_copper_ohm': 0.01998, 'insertion_loss_db': -0.0054, 'damping_factor': 1601.5}, 'N4_RP_OUT': {'r_copper_ohm': 0.02585, 'insertion_loss_db': -0.007, 'damping_factor': 1238.0}}
- `worst_damping_factor` = 1028.4
- `worst_net` = JACK_LN

_1 informational finding(s) in the JSON result._

