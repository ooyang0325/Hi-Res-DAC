# U202 CPLD: OD-16 fit skeleton

OD-16 (owner decisions, 14 Oct 2026) requires a fit before the PCBA order. LINK_SCK arrives on pin 9,
which is not a global-buffer pin, so it must reach a clock network through internal routing. The fit
must show:
1. LINK_SCK on a global or clock network;
2. setup and hold closed at 36 MHz with margin;
3. data crossing into FAM_CLK only through the FIFO.

This folder holds a skeleton design for that fit. It is **not** the product RTL.

| File | Content |
| --- | --- |
| [link_fit_skeleton.v](link_fit_skeleton.v) | SPI receiver clocked by LINK_SCK; 1024 × 32 dual-clock FIFO (Gray pointers); FAM_CLK-domain I²S master (÷2/4/8/16, 32-bit Philips, launched on the BCLK-falling edge); register read path on the LINK_SCK falling edge (9 MHz); the registers of Notes v1.1 §3.2 (ID 0xA6D2, VERSION, STATUS, CLOCK_CTRL, I2S_CTRL); CPLD_IRQ on FIFO under- or overflow |
| [U202_pins.asf](U202_pins.asf) | Pin assignments, in Supra's settings-file syntax (Quartus `.qsf` form). Also: LINK_SCK and FAM_CLK as global clocks; ≤ 8 mA drive and slow slew on LINK_MISO (28) and LRCLK_FB (13) |
| [link_fit.sdc](link_fit.sdc) | LINK_SCK 36 MHz, FAM_CLK 49.152 MHz, asynchronous groups; MOSI/FRAME launched on the SCK falling edge with ±2.7 ns U208 channel skew |
| [link_fit_skeleton_tb.v](link_fit_skeleton_tb.v) | Functional test (iverilog), described below |
| [check_cpld_pins.py](check_cpld_pins.py) | CI check (schematic job): the `.asf` pins and the skeleton's ports must equal the netlist's U202 pin map |

**Clock-domain crossings into FAM_CLK.** These are all of them, for OD-16 condition 3:
- **Audio data:** only through the FIFO.
- **I2S_CTRL (divider, run):** two-flop synchronisers. It is quasi-static: the firmware stops I2S_RUN before changing it (Notes rate-change sequence).
- **STATUS clear:** a toggle handshake.

The registers live in the LINK_SCK domain, because CLOCK_CTRL must work while the family oscillators
are stopped (their default state).

**Functional test.** It covers:
- ID and CLOCK_CTRL access at 9 MHz;
- 36 MHz audio bursts through the FIFO, played at 192 kHz (÷4) and 384 kHz (÷2) from an unrelated-phase 49.152 MHz FAM_CLK, with every word checked in order;
- underflow raising CPLD_IRQ, and a STATUS read clearing it.

```bash
cd hardware/cpld && iverilog -g2012 -o /tmp/link_tb link_fit_skeleton.v link_fit_skeleton_tb.v && vvp -n /tmp/link_tb
```

Result (14 Oct 2026, Icarus Verilog): **PASS** (306 and 383 words in order).

**The fit itself (owner, Windows).**
1. Synthesize `link_fit_skeleton.v` in Quartus for the AGM-recommended compatible device.
2. Run Supra with `U202_pins.asf` and `link_fit.sdc`.
3. Record from the reports:
   - the clock-network assignment of LINK_SCK;
   - the setup and hold slack at 36 MHz;
   - the drive and slew settings applied to pins 13 and 28. If Supra rejects these assignment names, use its own.

Neither tool is installed on the layout machine (macOS).

**OD-16 fallback.** If the fit does not close at 36 MHz, run the link at 18 MHz; the maximum sample rate
is then 192 kHz until a board revision.

**Known skeleton limit, for the product RTL.** Stopping I2S_RUN mid-frame does not flush the FIFO, so the
next run can start on the wrong channel. The product RTL must flush the FIFO, or realign L/R, on the
rising edge of I2S_RUN.
