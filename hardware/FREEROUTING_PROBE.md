# Freerouting routeability probe

**29 September 2026 · Off-board diagnostic only.** A copy of the 120 × 100 mm
integrated study was exported through KiCad 10's Specctra DSN API and routed
with locally installed Freerouting 2.4.1. The `.ses` result was imported into
another temporary PCB for inspection. No Freerouting copper was promoted to
the [review board](DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb).

| Probe measure | Input copy | Imported session |
| --- | ---: | ---: |
| Fully pad-connected nets with at least two pads | 44 / 249 | 112 / 249 |
| KiCad connectivity links | 896 | 472 |
| Tracks and vias | 753 | 2,460 |
| Vias | 125 | 228 |

The one-pass, no-fanout, no-optimizer run started with 962 Freerouting
unrouted items and ended with **499 unrouted and 53 Freerouting-reported
violations** after 3 min 10 s. Peak Java heap was about 1.22 GB. These counts
use different connectivity definitions from KiCad's partial-board DRC and are
not interchangeable. The protected-wire DSN experiment produced the same
session apart from its header; it did not preserve existing copper.

The result is **not a routable replacement**. The exported DSN has the four
layers, a GND plane, and four basic net classes, but omits the project's
named `.kicad_dru` constraints. In the imported copy, `LEG_LP` and `LEG_LN`
each gained two vias and B.Cu traces despite the L1-only rule. Some new
`VBUS` and `5V_SYS` tracks are below the required 1.0 mm width. Freerouting
also changed 57 existing copper items. Its new vias left the original saved
L2 zone fill stale until KiCad refilled it. The imported board has no
successful KiCad DRC: the temporary headless DRC crashed in macOS AppKit.

The probe is useful as a **congestion signal**: even with custom rules lost,
137 of 249 multi-pad nets remained incomplete. The next placement pass should
inspect the failed corridors and move complete subcircuits manually. A later
automatic-routing trial can exclude critical audio, clock, USB and power
classes and validate every imported route under KiCad rules before use.

## Reproduce on a disposable copy

KiCad's Python API exports DSN on this host; the `kicad-cli pcb export` menu
does not expose Specctra. The command-line flags follow the
[Freerouting CLI documentation](https://github.com/freerouting/freerouting/blob/master/docs/command_line_arguments.md)
and [settings reference](https://github.com/freerouting/freerouting/blob/master/docs/settings.md).

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 - <<'PY'
import pcbnew
board = pcbnew.LoadBoard('hardware/DAC_HPA_120x100_INTEGRATED_AUDIO_STUDY_ONLY.kicad_pcb')
pcbnew.ExportSpecctraDSN(board, '/tmp/dac-route-probe.dsn')
PY

/Applications/freerouting.app/Contents/runtime/Contents/Home/bin/java \
  -Djava.awt.headless=true -Xmx4g \
  -jar /Applications/freerouting.app/Contents/app/freerouting-executable.jar \
  -de /tmp/dac-route-probe.dsn -do /tmp/dac-route-probe.ses \
  --gui.enabled=false --router.fanout.enabled=false \
  --router.optimizer.enabled=false -mp 1 -mt 1
```

Keep the output outside the repository and import it into a disposable KiCad
board only. Refill L2 and apply the project DRC, placement, via-process and
critical-route audits before interpreting any proposed copper.
