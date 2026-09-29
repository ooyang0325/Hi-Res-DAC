# DAC 1V3 bypass sensitivity (review model)

This study compares the fitted C312 1 µF bulk capacitor in the old remote
placement with the hand-moved position beside U301/C309. The old position was
**unrouted**: its straight pad-to-U301 distance was about 16.3 mm. The trial
position has about 4.3 mm of drawn C312→C309→U301 F.Cu centreline. C310
2.2 µF stays beside regulator U303, so its regulator output capacitance is
preserved. C309 is the DAC's local 100 nF part. The routes and filled L2
ground must be inspected on the current PCB study; these distances alone do
not specify branch inductance.

The latest [DAC/core route audit](../DAC_CORE_ROUTE_AUDIT.json) also reports
a connected U303→DAC 1V3 link whose L3 portion is 25.393 mm, with two
vias, 35 local DAC/CPLD/LDO GND pads connected to L2, and short
U302-to-capacitor routes.
These drawn connections do not supply the upstream ferrite rails or measure
the regulator, capacitor, or return impedance; the simulations below remain
assumption-based sensitivity results.

The [LTspice deck](dac_1v3_bypass.cir) and
[MATLAB sweep](dac_1v3_bypass.m) use three passive capacitor branches at
U301 pin 21. They assume C309 100 nF/50 mΩ/2 nH, C312 1 µF/50 mΩ with
either 5 nH (local) or 20 nH (remote), and C310 2.2 µF/60 mΩ/20 nH.
Inductances include **assumed** capacitor, trace and return effects; they
were not extracted from a quoted stackup or measured board. The 1 GΩ DC
bleeders in LTspice only define the operating point. A 1 A AC test source
therefore makes its simulated node-voltage magnitude equal to impedance in
ohms.

| Frequency | Local 5 nH, MATLAB | Remote 20 nH, MATLAB | LTspice check |
| --- | ---: | ---: | --- |
| 100 kHz | 0.4778 Ω | 0.4769 Ω | Within 0.01% |
| 1 MHz | 0.0832 Ω | 0.0431 Ω | Within 0.57% |
| 10 MHz | 0.0654 Ω | 0.0631 Ω | Within 1.36% |
| 80 MHz | 0.6619 Ω | 0.8249 Ω | Within 0.01% |

Across 100 kHz–80 MHz, the remote case has an **illustrative** 1.045 Ω
antiresonance near 4.66 MHz; the local case's largest sampled value is
0.662 Ω at the 80 MHz upper boundary. Moving a capacitor can also shift a
resonance unfavourably: the local case is higher at 1 MHz. See the
[MATLAB plot](dac_1v3_bypass_sweep.png),
[sweep data](dac_1v3_bypass_sweep.csv), and
[LTspice log](dac_1v3_bypass_ltspice.log).

The model excludes the regulator's output impedance, power-plane geometry,
MLCC capacitance versus bias/temperature, DAC load spectrum, other rail
coupling, dielectric loss and any audio transfer function. It does not
predict hum, RF ingress, jitter, or THD+N. Extract the routed supply and
ground loop, obtain capacitor impedance/derating data and measure ripple at
U301 under operating loads before accepting the rail.

There is a separate **component-value hold**. [ESS's ES9018K2M datasheet,
DVDD Supply](https://www.esstech.com/wp-content/uploads/2024/09/ES9018K2M-Datasheet-v3.7.pdf)
recommends a 2.2 µF ±20% local DVDD decoupler that retains at least 1 µF
at 1.2 V over operating temperature. Fitted C312 is 1 µF nominal. The
remote C310 is 2.2 µF, but cannot establish a local high-frequency return
by capacitance alone. Review a 2.2 µF C312 ECO or another local bulk part,
using verified effective-capacitance data and an updated schematic/BOM.
The captured 2.2 µF Samsung part is a 0603 X5R 16 V MLCC; its [manufacturer
page](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do) lists the
nominal ratings but does not establish the required effective capacitance
at this board's bias and temperature.

## Reproduce

On macOS with the installed tools, run from the repository root:

```sh
cp hardware/sim/dac_1v3_bypass.cir /tmp/dac_1v3_bypass.cir
/Applications/LTspice.app/Contents/MacOS/LTspice -b /tmp/dac_1v3_bypass.cir
/Applications/MATLAB_R2025a.app/bin/matlab -batch "run('hardware/sim/dac_1v3_bypass.m')"
```

The LTspice log reports AC magnitude in dB; convert with `10^(dB/20)` to
obtain ohms for its 1 A source. LTspice 26.0.2 and MATLAB R2025a completed
on 29 September 2026. Direct simulator invocation required normal macOS app
registration on this host; a sandboxed CLI launch had failed before either
simulation started.
