# Response to layout review v1.1 · 14 October 2026

Review: `doc/DAC_HPA_Layout_Review_v1.1_Reverification_and_Decisions.docx` with
`doc/DAC_HPA_Layout_Reverification_Evidence.zip` (14 October 2026). It confirmed T1–T7, recorded the
owner decisions OD-3 to OD-14, and listed four small layout fixes (OD-14a–d) and one check before
order (N8). The owner left the remaining open items to the layout engineer's judgement.

Board: [DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb).
After the changes below:
- KiCad DRC with schematic parity: 0 violations, 0 unconnected, 0 parity issues ([INTEGRATED_AUDIO_DRC_PARITY.json](INTEGRATED_AUDIO_DRC_PARITY.json)). No net changed: OD-14 moves parts and copper only.
- The integrated-board CI job, replayed locally: pass.
- The reviewer's PDN scripts from the v1.1 evidence package, run unchanged on the final board: [sim/layout_review_v1_1/](sim/layout_review_v1_1/README.md).

**Owner decisions on this response (OD-14 conditions, OD-15 to OD-20, 14 Oct 2026; the owner's
decision record, folded into Spec v1.3 / Notes v1.2 / Parts List v1.1 at the G-5 freeze):**
- **OD-14:** accepted, pending the reviewer's re-run on the final commit.
- **OD-15:** the X201 release test of §3 is **replaced**. The duty at 0.4 and 0.8 V cannot meet 45–55 % for any oscillator (a 0.4 ns part gives up to 62.8 % at 0.4 V). The release test is 45–55 % at 1.2, 1.65 and 2.05 V on two samples; if one fails, two SiT8208 samples are tested.
- **OD-16:** the "sample LINK_SCK as data" option of §4 is **rejected**: 36 MHz sampled at 45–49 MHz gives about 1.3 samples per period. LINK_SCK must be a clock. An AGM Supra fit must close at 36 MHz before the PCBA order; the fallback is an 18 MHz link (192 kHz maximum). The fit skeleton, constraints and test are in [cpld/](cpld/README.md).
- **OD-17:** G-4 accepted at netlist level.
- **OD-18:** the G-5 freeze is conditional on the reviewer's re-run, the OD-16 fit and the OD-15 measurement.
- **OD-19:** two JLCPCB questions are added: the J201/J202 assembly fixture and its cost, and 90 Ω USB impedance control.
- **OD-20:** the re-quote adds the cleaning remark and the fixture.
- The OD-11 silk and the library-type workaround are accepted. The workaround is removed at the next library cleanup.

## 1. OD-14 small fixes

| Item | Change | Reviewer (14 Oct) | Now, same scripts |
| --- | --- | --- | --- |
| **a** C224 at U208 pin 8 (N3) | C224 sits in the 1 mm strip west of U208, with pad 1 on the 3V3D feed between the feed via and pin 8 (1.6 mm routed). Pad 2 carries its own filled GND via. The feed via touches pad 1, so it is filled too. The LINK_MOSI via moves 0.25 mm north-east to make room (line length −0.02 mm). U303 shifts 0.07 mm west so the placement audit's bounding boxes clear. U208 pin 4 (VSS) gets a GND via at the end of its stub, 0.5 mm along F.Cu. C224's old 3V3D via and In3 stub are gone | U208.8 spike 377 mV (419 mV with the real GND path); loop 5.01 nH; compact reference 118 mV | **86.6 mV** (compact layout 88.3 mV, same script); loop **1.14 nH**; impedance target crossing 66 → **282 MHz**. C224 GND: 3.45 → **0.0 mm** to a real via; U208.4: 4.3 → **0.5 mm** |
| **b** C218/C219 GND vias (N4) | C218: own GND via 0.9 mm along F.Cu (it lands in R218's GND pad, so it is filled). C219: own filled GND via 0.35 mm from its pad | X201/X202/X203 spike 60.3/69.9/**82.8** mV with the real GND path | **59.7/61.9/54.6 mV**. The real-path and method-faithful runs now agree: no pad needs the path correction. Every oscillator cap has a real GND via (In1/In4 ring ≥ 11/12) within 0.9 mm |
| **c** Owner-fitted parts (N5) | The board generator excludes every part whose schematic `Assembly` field is `Owner` from the position files: K601–K604, J701, D102, R509 | Not excluded | Excluded. The position file holds **476** footprints: the 469 JLC BOM parts plus FID1–FID7. A new CI assertion requires its parts to equal the JLC BOM designators exactly |
| **d** Component type (N6) | The generator types every BOM footprint by its pads: plated holes → through-hole, otherwise SMD | 85 JLC parts + J701 untyped | **0 untyped**: 541 SMD and 3 through-hole (J101, J701, J702). MH1–MH4 stay untyped; they are off the BOM and the position file. CI asserts this |

**Library copies.** The shared `JLC_Imported`/`DAC_HPA` library footprints are untyped, and the
frozen study boards are checked against them for a clean DRC, so the libraries were not edited.
KiCad therefore reports 86 `lib_footprint_mismatch` warnings on the integrated board. Neither check
waves these through:
- [check_integrated_parity.py](check_integrated_parity.py) gives the scratch copy of each untyped library footprint the board's type before it runs DRC. Every other difference from the library is still reported, and the result is 0/0/0.
- [check_integrated_audio_study.py](check_integrated_audio_study.py) accepts a library mismatch only if the library copy, given the board's type, matches the board footprint in KiCad's own DRC comparison. All 86 pass. Any other DRC violation still fails the job.

The `.kicad_pro` still ignores `footprint_type_mismatch`, because project files are not edited here;
the 0-untyped assertion stands in for it.

## 2. OD-11 silkscreen (Spec R17)

These are drawn as board silk texts (manifest `silk.texts`; 1.0 × 0.15 mm, the board's legend size),
placed by the legend tool with every pad, body, via and silk item as an obstacle:
- `OWNER` beside K601, K602, K603, K604, J701, D102 and R509.
- `TRS only` beside J702.
- "R509 owner-fitted — eFuse off without it", on two lines. No free silk area of that size exists within 12 mm of R509, so the note sits 13 mm north of it, above U503. It names R509, and the R509 `OWNER` mark is at the part.

The R509 mark took the place of R510's optional legend, and no other site exists for that legend.
The board now carries **256** designator legends; R510 is on the F.Fab drawing.

## 3. N8 — X201 edge rate: decision

**Datasheet check (done before order).** Kyocera's specification for the fitted part
(KC2520K80.0000C1GE00, drawing TNY1T-H1-SEE01-06, 29 Jun 2026) guarantees:
- rise/fall ≤ 4.5 ns (10–90 %, 15 pF, 2.8–3.63 V);
- symmetry 45–55 %;
- phase jitter ≤ 1 ps (12 kHz–20 MHz).

So the reviewer's 4.5 ns case applies.

**Alternatives checked.** No pin-compatible 2520 oscillator at 80.000 MHz guarantees ≤ 1.5 ns edges
without giving up the jitter that matters more for this DAC:

| Part | Edge (max) | Phase jitter | Verdict |
| --- | --- | --- | --- |
| Kyocera KC2520Z80.0000C1KX00 (same footprint and stand-by pin) | 1 ns, 20–80 % | **49 ps** (the low-jitter "Y" type stops at 72 MHz) | Rejected. At 20 kHz, 49 ps limits the output to about 104 dB SNR, against the ES9018K2M's ~127 dB |
| SiTime SiT8208 (MEMS, same pinout, ST option) | 2 ns, 10–90 % (1.2 ns typ.) | 0.5 ps typ. | Rejected: not ≤ 1.5 ns guaranteed, and a MEMS part's close-in phase noise is the wrong trade for a DAC master clock |
| SiTime SiT8209 | 2 ns | 0.5 ps typ. | Out of range: starts above 80 MHz |
| NDK NZ2520SH | 5 ns, 10–90 % | 0.1 ps typ. | No better on edges |
| Microchip DSC1101 | 2 ns, 20–80 % | — | 6-pin package; not ≤ 1.5 ns |

A 1.5 ns part would not close the item either. The reviewer's own corner envelope with edges
≤ 1.5 ns is 41.2–67.0 %, because the duty depends on the unknown ES9018K2M XI threshold more than on
the edge rate. At a mid-supply threshold every edge rate gives about 50 %.

**Decision.** Keep X201 = KC2520K80.0000C1GE00, because its quartz phase jitter is what sets the
DAC's output. Retire the risk **before** ordering the PCBA, not at bring-up:
1. ~~Measure duty at 0.4–2.05 V~~ **Superseded by OD-15.** Measure two samples (≥ 1 GHz scope, 15 pF, 3.3 V) before the PCBA release: 10–90 % edges, and duty at 1.2, 1.65 and 2.05 V. Release when the duty is 45–55 % at all three, on both samples.
2. If a sample fails, measure two SiT8208AI-…-33S-80.000000 samples the same way. Change X201 only if those pass (OD-15).
3. Bring-up keeps the OD-6 conditions: duty at U301 XI within 45–55 %, and re-fit 33 Ω at R203 only if XI rings.

## 4. Remaining open items: decisions

| Item | Decision / status |
| --- | --- |
| **CPLD pin-constraint file and fitter run** (F06–F09) | There is no CPLD RTL in the repository, so the fitter cannot run here. The netlist pin map the constraint file must follow is below. Two requirements go into the constraint file: ≤ 8 mA drive or slow slew on pins 28 (LINK_MISO) and 13 (LRCLK_FB), per review R2. **LINK_SCK is on pin 9, which is not a global-buffer pin**; the only `IO_GB` pin is pin 1 (FAM_CLK). The fitter report must therefore show LINK_SCK promoted to a global clock through internal routing (OD-16; sampling it as data is rejected). Fit skeleton, `.asf` pins, SDC and a passing functional test: [cpld/](cpld/README.md). **Fit run 15 Oct 2026** (Supra 2026.09.b0, native flow, AGRV2KQ32; details in [cpld/README.md](cpld/README.md#fit-result-15-oct-2026)): LINK_SCK lands on a global clock network (`LINK_SCK_i|o~ALTA_GCLK`; Supra reports 4 of 5 GCLKs, but the datasheet gives 4 global clock lines, so none is spare for the product RTL); at 36 MHz the worst setup slack is +8.98 ns (Fmax 102 MHz) and the worst hold slack +0.29 ns, the worst of repeat runs (FAM_CLK: +12.06 / +0.62 ns at 49.152 MHz); audio data enters FAM_CLK only through the FIFO (4 M9K). Pins 28 and 13 get slow slew (`CFG_SLR` = 1, only on those two pins); the 8 mA drive setting has no effect in this Supra, so slow slew is how R2 is met. The functional test passes on the RTL as edited for the fit and on Supra's routed netlist. OD-16 closes at 36 MHz on the skeleton, so the 18 MHz fallback is not needed |
| **G-3** overlays | Physical, with the owner's samples. Add the X201 edge and duty measurement (§3) |
| **G-4** polarity | Netlist level, done: every listed part's pin functions land on the intended nets. D102 K = VBUS; D104/D105 (BAT54) A → K = 5V_SYS; D411/D412 (PMEG2010) K on the positive side; D609 (BAS70-04) 1 A1 = GND, 2 K2 = N6_MCK_RC, 3 K1/A2 = N6_PMP; C442 + on N4_VPOS_IV, C443 + on GND; D705/D706 pad 1 = anode (owner override). The silk-mark-to-part check stays physical, with G-3 |
| **G-5** netlist and BOM freeze | OD-14 changed no net and no value (parity 0/0/0; the schematic is unchanged). This commit is the freeze candidate. OD-18 conditions: (1) the reviewer's re-run on `ba1f315`: open; (2) the CPLD fit: **met** 15 Oct (36 MHz closes, no fallback); (3) the X201 samples: open |
| **G-6** JLCPCB answers | Ask JLCPCB in writing: (1) the J101 S1–S4 stake slots and the J702 pads 1/2: pin-in-paste, or hand-solder; (2) the J201/J202 placement preview, per OD-10; (3) filling and capping of the 59 via-in-pad / near-pad vias; (4) the OD-9 wash and cleanliness record; (5) whether C631–C634 stay ≤ 95 s above 220 °C; (6) the J201/J202 assembly fixture and its cost; (7) 90 Ω differential impedance control for the USB pair, or an order without impedance control (OD-19); (8) that U202 (LCSC C18208899, BOM MPN AGRV2KQ32) arrives marked `AG32VF?03K?U6`, so the placement preview and incoming check accept that marking (handback, 15 Oct). The order remarks are in Spec v1.2 G-6. Text to send, without internal codes: [JLCPCB_QUESTIONS_2026-10-15.md](JLCPCB_QUESTIONS_2026-10-15.md). **Answered 15 Oct:** six of eight closed; the slots stay unpasted and are hand-soldered (R01 fallback); cleaning has no JLCPCB test report (owner decision); see the reply table in that file |
| **Cost re-quote** | Owner, with JLCPCB. Quote inputs: 120 × 100 mm, 6 layers JLC06161H-3313, ENIG, 1578 vias (59 filled and capped), 469 JLC-placed parts, 2 JLC through-hole parts (J101, J702) |

U202 (AGRV2KQ32) pins in use, from the schematic netlist:

| Pin | Net | Pin | Net |
| --- | --- | --- | --- |
| 1 (IO_GB) | FAM_CLK | 19 | N2_LRCLK_SRC |
| 3 | CPLD_IRQ | 20 | N2_SDATA_SRC |
| 4 (NRST) | CPLD_NRST | 21 | N2_CPY_CK |
| 8 | OSC44_EN | 22 | N2_CPY_SD |
| 9 | LINK_SCK | 23 | MCLK_EN |
| 13 | LRCLK_FB (≤ 8 mA / slow slew) | 24 / 25 (JTAG) | CPLD_JTMS / CPLD_JTCK |
| 18 | N2_BCLK_SRC | 26 / 27 / 28 | LINK_FRAME / LINK_MOSI / LINK_MISO (28: ≤ 8 mA / slow slew) |
| 31 | OSC48_EN | 6, 16, 32 / 17, 30, EP | N2_V33_CPLD / GND |

Pins 2, 5, 7, 10, 11, 12, 14, 15 and 29 are not connected.

## 5. Corrections and records

- **The reviewer's corrections are accepted:** 1.57 pF hold-node capacitance (N1); leakage exposure up, not down (N2); LINK_SCK stub 2.32 mm; LINK_FRAME 16.46 mm with 3 vias. The 13 October response carries a corrections note.
- **X201 resonance** (N7, OD-13): unchanged. The impedance target is crossed at 23 MHz; X201 jitter is measured at bring-up.
- **J201/J202 pin-1 silk circles** overlap pad 1 by 0.035 mm. They are library silk; JLC clips silk from exposed copper. Recorded, not changed.
- **Via counts:** 1578 vias, 59 filled and capped ([JLCPCB_DFA_DFM_RULES.md](JLCPCB_DFA_DFM_RULES.md)).
- **First independent sign-off suite**, re-run on this board: 0 FAIL / 10 WARN / 9 PASS, unchanged ([signoff/out/SIGNOFF_REPORT.md](signoff/out/SIGNOFF_REPORT.md)). Its `kicad_drc.json` (all severities) now lists the 86 type-only library warnings.
