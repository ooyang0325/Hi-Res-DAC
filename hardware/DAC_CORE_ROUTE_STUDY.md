# DAC core and CPLD clock routing checkpoint

**29 September 2026 · Review only · 120 × 100 mm, four layers.** The
[integrated PCB](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb) is
the current editable partial routing candidate. Every new component position
and copper waypoint was chosen manually and recorded in the
[replay manifest](INTEGRATED_AUDIO_MANUAL_DELTA.json). It has **544
footprints, 250 named nets, 756 track/via items, zero KiCad DRC violations,
499 DRC-reported unconnected items and 896 full ratsnest links**. The current
manual delta records 121 moves, eight removed source-copper items and 729
added copper items. The
[critical-route audit](DAC_CORE_ROUTE_AUDIT.json) is the numeric evidence;
these partial-board results do not authorize a PCBA order.

## What moved and what now has copper

- U202 was rotated **270° in place**. Its physical pins 20/19/18 now face
  east in SDATA/LRCLK/BCLK order, matching U301's west-edge pin order.
  R204/R205/R206 and TP715/TP716 were hand-regrouped below it. TP712 now
  lies on the R215→U202 FAM_CLK path. C214 was moved to U202 pin 16 and
  given its own L2 GND via. U302/C302 shifted west to reserve three straight
  I²S lanes. C213→U202 pin 32, C214→pin 16 and C215→pin 6 are locally routed
  at 1.103/2.056/3.057 mm. Two U202 exposed-pad GND vias are flagged filled
  and capped. The schematic pin map and resistor values did not change.
- The five U301 100 nF capacitors C305–C309 now form a 1.45 mm pitch row
  with supply pads facing their matching DAC pins. Four 0.25 mm north-side
  source paths enter the row through 0.75 mm gaps between GND via copper.
  C303/C304 and C439/C440 were regrouped above them, and R301/R302 now
  face their analog output rails south. U301's nine perimeter GND pins join
  its exposed pad; **five 0.70/0.30 mm GND vias inside the EP are explicitly
  filled and capped** in KiCad. Across U202 and U301, seven EP vias are
  explicitly filled and capped. C312 1 µF moved beside C309, while C310
  2.2 µF remains at U303's output.
- U303, C311, C310 and its R533/R534 feedback divider now form a local
  regulator group. VIN1/VIN3, the output capacitor, divider, and their
  GND connections to the single L2 polygon have drawn copper. The L3 portion
  of the U303→DAC 1V3 link is **25.393 mm**, with two through vias. R305 was parked
  away from this group; its final reset pull-up placement and route remain
  to be reviewed with DAC_RESETB.
- Local supply-cap routes include U302 VIN→C301 at **0.875 mm** copper
  contact, U302 OUT→C302 at **2.131 mm**, and U302 OUT→FB302 at **5.025 mm**.
  Thirty-five DAC/CPLD/LDO local GND pads connect to L2 in the route audit.
- Filtered DVCC and VCCA use two short **L3** feeders from FB301/FB302
  toward the bulk capacitors, underneath continuous L2 GND. Their F.Cu
  escapes stay outside the I²S passage. The ferrites' upstream 3V3D/3V3A
  pins remain unconnected to their upstream source rails; local U303-to-DAC
  1V3 copper is now connected as measured above.

## Critical-route measurements

| Path | Current drawn result | Screen |
| --- | ---: | ---: |
| U202→R204→U301 BCLK, including resistor pad span | 22.213 mm | ≤25 mm |
| U202→R205→U301 LRCLK, including resistor pad span | 22.324 mm | ≤25 mm |
| U202→R206→U301 SDATA, including resistor pad span | 22.879 mm | ≤25 mm |
| I²S length spread | 0.666 mm | ≤5 mm |
| X201→R203→U301 MCLK | 8.381 mm (1.832 + 6.549) | 2/8/10 mm segments/total |
| R215→U202 FAM_CLK | 3.039 mm | Review, no separate limit |
| MCLK-to-DACR F.Cu track edge gap beyond U301 courtyard | 2.1468 mm | Provisional ≥2 mm |
| MCLK-to-DACR track edge gap inside the U301 fanout | 1.6264 mm | Provisional ≥1 mm |

The I²S source and output traces use **0.15 mm F.Cu with no vias**. Their
parallel central lanes have **0.45 mm copper-edge gap = 3 × trace width**
at y = 74, 76, 78 and 80 mm. Pin and component fanouts have their own
package-clearance limits. The saved filled L2 polygon lies directly below
MCLK, FAM_CLK and all six I²S net segments at 0.01 mm centreline samples
and ±0.075 mm offsets. This screen does not extract return impedance or
prove digital timing. The eight source/post segments coexist with the
regrouped DAC supply and L3 feed copper under KiCad's current rules.

The Notes contain both a 2 mm DAC/digital separation paragraph and a 1 mm
MCLK-specific clearance. This review uses **2 mm outside U301's fixed
package courtyard and 1 mm for F.Cu fanout tracks inside it**. The
[audit](DAC_CORE_ROUTE_AUDIT.json) clips the tracks at that boundary and
also checks outside MCLK pads against DAC-input tracks. The closest
external pad-to-track gap is 2.1329 mm. A different interpretation of the
Notes needs a controlled constraint update before routing freeze.

The four DAC-to-I/V input lengths are now
**4.294/6.030/6.837/4.786 mm** for DACL/DACLB/DACR/DACRB, all below the
owner-approved provisional 7 mm limit. DACR retains **0.163 mm** of that
screen. Their sampled L2 support remains complete. The separate DACL
feedback branch still has **1.9426 mm without direct L2 beneath its
centreline**; its three-dimensional return and I/V loop stability remain
unqualified.

## Electrical and manufacturing holds

1. **DVDD capacitance:** The fitted C312 is 1 µF nominal. [ESS's ES9018K2M
   datasheet](https://www.esstech.com/wp-content/uploads/2024/09/ES9018K2M-Datasheet-v3.7.pdf)
   calls for a local nominal 2.2 µF DVDD decoupler that retains at least
   1 µF at 1.2 V over operating temperature. C310 is 2.2 µF at U303 and
   must remain a local LDO output capacitor. Review a C312 2.2 µF
   schematic/BOM ECO with verified effective-capacitance data. The
   [LTspice/MATLAB passive sweep](sim/README.md) compares assumed loop
   inductances; it is not a measured supply impedance or audio result.
2. **Via and EP assembly:** [JLCPCB's via-covering guidance](https://jlcpcb.com/help/article/pcb-via-covering)
   treats filled/capped vias as suitable for via-in-pad, and asks the
   customer to identify them in the order. Two U202 and five U301 EP vias
   are flagged filled/capped in the PCB. The [via-pad process audit](INTEGRATED_AUDIO_VIA_PAD_PROCESS_AUDIT.json)
   counts 125 vias total, 20 filled/capped vias near SMT pads, and 45
   unfilled via-to-SMT-pad sites closer than 0.35 mm. It finds zero unfilled
   SMT-pad copper overlaps and zero unfilled gaps below 0.10 mm; the 45
   sites still need JLC mask/process review. Confirm via-in-pad process,
   price, stencil aperture and QFN solder result in the order preview; DRC
   does not establish acceptance.
3. **Incomplete power and return:** the listed U202 bypass and U302 local
   capacitor paths, and the U303→DAC 1V3 trunk, are drawn. Upstream ferrite
   source feeds and U401/U402 main VPOS/VNEG distribution remain open, as do
   the U401/U402 output-amplifier exposed-pad thermal routes. The 35 audited
   local GND-to-L2 connections do not mean every fitted GND pad is routed.
   Co-route and extract the L3/L4 audio returns before judging hum, RF pickup,
   crosstalk or output impedance.
4. **Clock/capture function:** The U205→R215 clock source, R228–R230
   capture taps, CPLD SPI/capture links, reset controls and most of the
   digital network remain open. Check each branch's stub/loading, final
   edge shape and timing. The all-rate post-CPLD guard is still a separate
   functional ECO with absent verified firmware/RTL.
5. **Release:** USB routing/90 Ω stackup, protection timer/reset branches,
   DACL feedback return, I/V and output-stage stability, G-3/G-4 physical
   gates, system ESD, EMI, measured jack impedance and audio/RF/hum tests
   remain open. There are 896 full ratsnest links; zero DRC violations and
   499 DRC-reported unconnected items describe partial-board status only and
   do not authorize Gerber/CPL/PCBA release.

The separate [Freerouting probe](FREEROUTING_PROBE.md) is off-board diagnostic
only. Its input copy had 753 track/via items; the imported session had 2,460,
but also 53 reported violations and lost named KiCad custom rules. It does
not replace or contribute copper to this board. Its 962→499 unrouted count
uses a different connectivity definition from the current 896 ratsnest links
and 499 DRC unconnected items.

## Review visually from the command line

```sh
KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
  bash hardware/make_review_views.sh /tmp/dac-critical-review \
  hardware/DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb

/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
  hardware/check_dac_core_routes.py \
  hardware/DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb
```

Zoom the exported F.Cu and L2 SVGs together around x = 78–95, y = 62–85 mm.
Inspect U202→R204–R206→U301, TP712/715/716, the C305–C309 returns, the
five EP vias, and the L3 DVCC/VCCA routes. The [general visual workflow](PCB_CLI_VISUAL_REVIEW.md)
also exports mirrored B.Cu and a 3D GLB. State every finding by reference,
pad, layer and board coordinate.
