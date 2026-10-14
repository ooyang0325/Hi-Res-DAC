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
| [run_supra_fit.sh](run_supra_fit.sh) | The fit, end to end: Supra setup, Supra's Yosys mapper, Supra place-and-route and timing; prints the summary |
| [sim_routed.py](sim_routed.py) | The functional test on Supra's routed netlist (Icarus Verilog), run by the fit script |

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

Result (14 Oct 2026, Icarus Verilog): **PASS** (306 and 383 words in order). Re-run 15 Oct on the RTL as
edited for the fit, Icarus Verilog 12.0 on Windows: **PASS**, the same counts. The same test also passes on
Supra's routed netlist (below).

## Fit result, 15 Oct 2026

Supra 2026.09.b0 (b2dd0a76), device `AGRV2KQ32`, native flow (Supra's bundled Yosys as the mapper):

```bash
IVERILOG_BIN='C:\iverilog\bin' hardware/cpld/run_supra_fit.sh /c/baidunetdiskdownload/Supra-2026.09.b0-b2dd0a76-win64-all
```

With Icarus Verilog available (`IVERILOG_BIN`, or on `PATH`), the script then runs the functional test on
the routed netlist with Supra's cell models ([sim_routed.py](sim_routed.py)): **PASS** (306 and 383 words in
order), so the fitted design itself behaves like the RTL.

The Quartus flow needs the NTU licence server, which was unreachable. Supra does the placement, routing
and timing in both flows.

| OD-16 condition | Result |
| --- | --- |
| 1. LINK_SCK on a clock network | Yes: `LINK_SCK_i|o~ALTA_GCLK`, routed from pin 9 into a global clock (insertion about 5.8 ns, which the timing includes). Global signals 4 of 5: LINK_SCK, FAM_CLK, CPLD_NRST, the frame clear |
| 2. Setup and hold at 36 MHz | LINK_SCK: setup +8.98 ns (Fmax 102 MHz), hold +0.29 ns (internal; from LINK_MOSI ≥ +7.80 ns). FAM_CLK at 49.152 MHz: setup +12.06 ns (Fmax 121 MHz), hold +0.62 ns. 0 errors. Repeat runs on the same input vary by about 0.5 ns (LINK_SCK setup +8.98 to +9.50 ns); these are the worst |
| 3. Audio into FAM_CLK only through the FIFO | Yes: `set_clock_groups -asynchronous`; the FIFO is 4 M9K. Use: 274 of 2112 logic cells, 208 flops |

Pins 28 (LINK_MISO) and 13 (LRCLK_FB): `SLEW_RATE 0` sets `CFG_SLR = 1` on those two pins only. A control
run without it gives 0. `CURRENT_STRENGTH_NEW 8MA` is accepted but changes nothing: `CFG_PDRCTRL` stays
`4'b0100` on every output. So **slow slew** is how layout review R2 is met. The drive in mA that code
`0100` means is not in the Supra data. The fields are in `link_fit_skeleton_routed.v` in the work directory.

Not timed: the 11 outputs (no output delay; the I²S lines all leave FAM_CLK flops, and LINK_MISO is
read at 9 MHz) and the CPLD_NRST reset network.

**Changes the fit needed.**
- **Pin 4 is the NRST pad.** Supra has no `PIN_4`; it names the pad `PIN_NRST` and routes it into the
  fabric. The `.asf` uses `PIN_NRST`, and `check_cpld_pins.py` maps it to pin 4. Check in the AGRV2K
  datasheet whether NRST also restarts configuration. If it does, the RTL reset is redundant but harmless.
- **One asynchronous clear per flop.** Yosys rejects `negedge LINK_FRAME or negedge CPLD_NRST`, so under
  `ALTA_SYN` (defined by Supra's mapper) the flops clear on `frame_clr_n = LINK_FRAME & CPLD_NRST`.
  Simulators and Quartus keep the two-edge form. With only the combined clear, the RTL test fails: the
  testbench pulses CPLD_NRST while LINK_FRAME is already low, so `frame_clr_n` never has an edge in
  simulation. Silicon holds the clear by level, and the routed-netlist test passes.
- **FIFO read register without a reset.** The M9K read port has no reset, so `word <= 0` on underflow kept
  the 1024 × 32 RAM in 33 k flops. The read register `rd_q` now has no reset; a per-slot flag `slot_ok`
  zeroes the word on underflow. Same output timing.
- **SDC: one false path, LINK_FRAME → LINK_MISO_reg.** That clear sits on a falling-edge flop. The
  single-clock model pairs FRAME's change with the same falling edge (removal −1.3 ns), but FRAME
  changes only while SCK idles. The first real falling edge comes at least 1.5 periods after release.
  Supra's `set_false_path` has no `-hold` option, so the recovery check on that endpoint is dropped too.

**OD-16 fallback.** If the fit does not close at 36 MHz, run the link at 18 MHz; the maximum sample rate
is then 192 kHz until a board revision.

**Known skeleton limit, for the product RTL.** Stopping I2S_RUN mid-frame does not flush the FIFO, so the
next run can start on the wrong channel. The product RTL must flush the FIFO, or realign L/R, on the
rising edge of I2S_RUN.
