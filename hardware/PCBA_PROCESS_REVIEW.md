# Connector soldering process hold

The schematic and library files are not a PCBA release. The functional ECO raises the review BOM to 463 JLCPCB-placed parts; the original 455-part footprint scan found two connectors with plated through-hole pads and **no F.Paste apertures**. Their land patterns and process questions are unchanged:

| Ref | JLCPCB-placed land pattern | Current paste status | Required confirmation |
| --- | --- | --- | --- |
| J101 | 12 surface lands, shell slots S1–S4 plated through-hole, two non-plated locating holes | Surface lands have F.Paste; S1–S4 do not | Design notes require pin-in-paste shell stakes. Obtain JLCPCB's process approval and aperture dimensions before adding paste or ordering. |
| J702 | Pads 1/2 are 0.6 × 1.5 mm plated oval slots; pads 3–6 are surface lands; two locating pegs now have NPTH holes | Pads 1/2 have no F.Paste; 3–6 do | [JLCPCB lists C2848643 as available for assembly](https://jlcpcb.com/partdetail/Korean_HropartsElec-PJ_332A6A/C2848643), but confirm how pads 1/2 are soldered on a top-side Standard PCBA order. If JLCPCB cannot solder them, the owner hand-solders pads 1/2 from the bottom side. |

[JLCPCB's stencil guidance](https://jlcpcb.com/help/article/opening-process-standard-of-stencil) says through-hole pads do not receive paste openings by default unless they are designed on the paste layer. Availability in the parts library does not establish the soldering process for these particular slots.

The owner chose copper-only enlargement around the unchanged maker slot drills and pad centres. The current J701/J702 footprints reach ≥0.31 mm worst copper ring at JLC's +0.13 mm slot tolerance; the closest J701 pad gap is 0.25 mm. G-3 overlay and JLCPCB DFM acceptance remain open. No paste apertures have been added to the slots.

The current board has 143 vias and marks two U202 and five U301 exposed-pad
vias filled and capped. The [via-pad process audit](INTEGRATED_AUDIO_VIA_PAD_PROCESS_AUDIT.json)
finds zero unfilled SMT-pad copper overlaps and zero unfilled via gaps below
0.10 mm, but identifies **45 unfilled via-to-SMT-pad sites within 0.35 mm**
for JLC mask/process review. These are geometry screens, not order approval.
JLC's [via-covering guidance](https://jlcpcb.com/help/article/pcb-via-covering)
does not support ink plugging in or within 0.35 mm of a pad; tenting and
filled/capped processing need separate review. Identify every selected
filled/capped via by coordinate in the order remark or an annotated image;
KiCad flags alone do not specify a Gerber fabrication order. Confirm process,
price, mask web and stencil treatment in JLC's order preview.
U401/U402 output-amplifier exposed-pad thermal routes remain open and need
copper and thermal review before release; the filled/capped vias are at U202
and U301. See the [route checkpoint](DAC_CORE_ROUTE_STUDY.md).

Suggested question for JLCPCB: “For a top-side Standard PCBA order, can you solder the four plated shell slots S1–S4 of GCT USB4105-GF-A (J101) and the two plated slots 1/2 of HRO PJ-332A-6A, C2848643 (J702)? Do you require F.Paste apertures or an order remark, and what aperture geometry/hand-solder step do you recommend?”
