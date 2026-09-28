# All-rate post-CPLD capture using MCU SPI2

**Status: proposed functional correction and verification contract.** This does not change the KiCad netlist, PCB, firmware or CPLD RTL. It is not evidence that the post-CPLD guard works on a board. Do not freeze the all-rate guard claim until the firmware, RTL and tests below exist.

## Why the present I²S2 plan fails

WCH's current CH32V303/305/307/317 datasheet **v3.9** (14 August 2026), §4.3.15 Table 4-29, limits the MCU I²S clock to **8 MHz in both master and slave modes**. The captured 64-bit stereo stream needs `BCLK = 64 × fs`: 11.2896, 12.288, 22.5792 and 24.576 MHz at 176.4, 192, 352.8 and 384 kHz. The earlier v2.9 finding remains true in v3.9. Its Table 4-28 specifies **72 MHz maximum SPI clock in slave mode**, with 4 ns input setup and hold requirements. The SPI limit makes a different use of the *same* U201 pins worth implementing and testing; it does not prove DMA throughput, capture framing or routed edge timing.

The user-supplied functional review identified this as F01 at baseline `59b4b27`. The versioned Spec v1.1 §3.2/§8 and Notes v1.0 still describe I²S2 capture. Their all-rate post-CPLD guard and R-28 frozen-word energy claim need this correction or another qualified capture architecture.

## Proposed pin and peripheral contract

| Existing signal | Existing circuit | MCU use after firmware change |
| --- | --- | --- |
| `N2_CAP_CK` | U202 pin 18 → `N2_BCLK_SRC` → R228 330 Ω → U201 pin 34/PB13 | SPI2 SCK input |
| `N2_CAP_SD` | U202 pin 20 → `N2_SDATA_SRC` → R230 330 Ω → U201 pin 36/PB15 | SPI2 MOSI input |
| `N2_CAP_WS` | U202 pin 19 → `N2_LRCLK_SRC` → R229 330 Ω → U201 pin 33/PB12 | GPIO/EXTI witness of the U202 **pin-19 source branch**; **not** SPI2 hardware NSS |
| `LRCLK_FB` | U202 pin 13 → U201 pin 54/PD2 | Existing TIM3 external-clock frame count from a **different U202 output** |
| `N2_MCLK_PERMIT` | U201 pin 35/PB14 → U206 pin 6 | Keep PB14 as GPIO; never configure it as SPI2 MISO |

Use the default SPI2 pin map; no pin remap or schematic net change is proposed. Configure **SPI2 slave, 16-bit, MSB first, receive-only, software NSS (`SSM=1`, `SSI=0`)**, with CPOL/CPHA selected from measured U202 BCLK/SDATA timing. WCH's reference manual v2.5 §§20.2.3–20.2.6 describes software-NSS slave reception and RX DMA. Its SPI GPIO table says NSS is not used in software mode. Confirm on the exact U201 silicon that receive-only mode leaves PB14 under GPIO control; MCLK permit must never pulse when SPI2 starts, stops or errors.

Reserve **DMA1 channel 4 for SPI2_RX** during playback. The reference manual's CH32V30x DMA map also assigns USART1_TX, I2C2_TX, TIM1 and TIM4 requests to that channel; do not schedule their DMA transfers concurrently. SPI1_TX uses channel 3. The actual USB, SPI1, SPI2, ADC and CPU arbitration still needs a worst-case instrumented run.

## Frame alignment and fail-closed behavior

SPI2 has no I²S word-select logic. `PB12` as GPIO cannot magically frame a continuously clocked SPI bitstream, and an EXTI interrupt at every LRCLK edge would create an unnecessary high-rate interrupt load. These **RTL and firmware invariants** are required:

1. With `I2S_RUN=0`, U202 holds its physical BCLK output idle and WS/SDATA at documented levels. During a family or rate change, open the output switches, stop the stream and reset the I²S serializer before rearming capture.
2. Firmware clears SPI2 status/overrun, arms circular RX DMA and SPI2 while BCLK is still idle, then commands one deterministic serializer start. U202 must emit a defined first BCLK edge and known WS phase. No clock edge may precede the arm acknowledgement. The first incomplete frame is discarded before release of `RELAY_EN`.
3. Capture **four 16-bit SPI words per 64-bit stereo frame**. Philips I²S changes WS one bit before each channel's MSB, so reconstruct the 32-bit left and right slots with a one-bit shift across successive 64-bit raw frames. Verify both the sign/padding of 16/24-bit formats and the left/right order against a logic analyzer at the **U301 input pads**, not only at U202 output pins.
4. Compare SPI2 DMA progress with `LRCLK_FB` at PD2/TIM3_ETR: four 16-bit DMA words per frame, allowing only the precisely documented boundary offset. **This is U202 pin 13, not the pin-19 WS output**, so the count alone cannot prove WS integrity. Check PB12 WS phase at start/restart. As a low-overhead *partial* runtime witness, configure PB12 as GPIO with EXTI12 on both edges, keep its PFIC interrupt masked, and poll/clear the sticky EXTI edge flag at each ≤0.4 ms DMA half-buffer. A normal half-buffer has at least 17 frames, hence at least 33 WS transitions strictly inside the block; absence of an edge is a stuck-source fault. Validate on the exact MCU that the flag sets with this configuration and that clearing it does not disturb SPI2. A sticky flag cannot count edges or prove 32-BCLK half-frame phase.
5. Treat SPI overrun, DMA error, wrong frame count, an absent PB12 WS edge, a *detected* phase loss, or >2 ms without capture progress as a fault: immediately drive `RELAY_EN` low, zero/log the pair, and require the full pre-close sequence before reconnecting. Do not close the switches unless capture is armed and synchronized.
6. The existing hardware analog protection and DAC lock checks remain active. Their coverage is not a substitute for falsely claiming the post-CPLD P1–P4 guard at a rate where capture failed.

Known-phase startup is the key unresolved feasibility item. If U202 cannot guarantee it, add an explicit hardware frame marker or an independently clocked capture bridge and rerun the electrical and placement review; a one-time EXTI ISR timestamp alone cannot establish a bit-exact 24.576 MHz boundary.

**Open physical WS fault / F01 hold:** R229 taps U202 pin 19 **before** R205; `LRCLK_FB` comes from U202 pin 13. A stuck, open or glitched `LRCLK` branch **after R205 at U301 pin 26** can leave both MCU witnesses apparently normal while the DAC receives a wrong WS waveform. A transient pin-19 WS glitch can also set the EXTI sticky flag and evade its edge-presence check. No current timer input or DMA route timestamps PB12 edges against BCLK continuously; PB12's alternate timer function is TIM1 break input, not a frame capture channel. Consequently, this proposed SPI2 contract does **not** close F01 for physical WS-path faults or justify R-28 fault-energy credit in those cases. Keep F01 open until the fault scope is explicitly accepted or a controlled schematic/placement ECO adds a monitor at the DAC-side WS pad with proved count **and phase** coverage. Moving PD2/TIM3_ETR from U202 pin 13 to the DAC-side `LRCLK` would detect missing/extra edges, but a same-count phase glitch still needs another check.

The **bit-perfect word comparison is a directed test with known source samples**, including at every rate. The runtime P1–P4 guard instead examines the captured samples for the specified dangerous patterns. Neither the current design nor this proposal continuously compares arbitrary music against the USB source. A corruption that preserves clock/frame counts and avoids all P1–P4 thresholds can remain undetected; DAC DPLL lock does not close that gap.

## Rate and latency budget

At 384 kHz the stream is **24.576 Mbit/s**, or **1.536 million 16-bit DMA transfers/s = 3.072 MB/s**. Use a circular ping-pong buffer with each half holding `4 × floor(fs/2500)` halfwords. Its duration is at most 0.400 ms at every advertised rate: 17/19/35/38/70/76/141/153 stereo frames per half for 44.1/48/88.2/96/176.4/192/352.8/384 kHz. The maximum full buffer is **2,448 bytes**. This is incremental to the guard, USB and link buffers; a complete SRAM and DMA-bus budget is still required.

The right-channel LSB in a Philips frame arrives in the **next** raw frame; with 16-bit SPI receives, software may wait one more DMA word (`16/BCLK`, at most **5.67 µs** at 44.1 kHz) after a half-buffer boundary. Retaining the current **≤0.60 ms post-CPLD decision** therefore assumes ≤0.40 ms to that boundary, the next word, and ≤0.10 ms for reconstruction and rule evaluation under worst concurrent load. The arithmetic model gives **≤0.501 ms** including the lookahead. With the calculated **≤1.008 ms switch opening**, a P1 run of at least 22.0 ms rounded up to a full sample isolates a frozen word by **≤23.517 ms**. These are planning targets, not measured latencies. The separate >2 ms DMA-stall rule can take up to 3.008 ms to physically open the switch after capture stops.

The v1.1 guard calculation uses fixed **0.5 ms** block sums (100 blocks for P2's 50 ms and 300 for P4's 150 ms). A 0.4 ms DMA block does **not** preserve those counts. Implement the P1/P2/P3/P4 windows from exact per-rate sample counts or equivalently proved variable block sums, and redo CPU, SRAM, false-trigger and fault-energy calculations. The old 13.3% CPU, 12.5 KB RAM and R-28 13.8/25.3 mJ results cannot simply be carried into this architecture.

Run `python3 hardware/check_spi2_capture_contract.py` from the repository root for the rate, buffer, bit-framing and assumed-latency arithmetic. A passing script says nothing about actual MCU peripheral behavior, U202 RTL, routing or audio performance.

## Qualification before schematic freeze or routing release

- Implement U202 idle/start/phase control and U201 SPI2/DMA code. Prove PB14 stays in the requested MCLK-permit state across reset, start, rate change and all SPI errors.
- Scope U202 and U301 BCLK/WS/SDATA, PB13/PB15 input setup/hold and rise/fall at both 45.1584/49.152 MHz families, supply and temperature corners. Review R228–R230, branch capacitance, continuous L2 return and routed stub geometry.
- At **all eight rates** and **16/24/32-bit** source formats, compare known PRBS/edge-case streams to the reconstructed post-CPLD data, with no missing, duplicated, swapped or shifted word; compare the same pattern at U301 pins. Preserve the existing **≥10⁹-frame** stress test at 352.8 and 384 kHz. Record SPI OVR, DMA errors and `LRCLK_FB` deltas. This is a qualification test, not a statistical device-clock guarantee.
- Inject each OD-1 P1–P4 condition *after* U202 while USB-side samples remain clean; measure decision and switch-open time, output energy, re-arm behavior and non-triggering 20 Hz content. Inject BCLK stops, one-bit slips, DMA starvation and rate/family changes. Inject **WS stuck low/high, a short WS glitch and a 32-bit slot-phase error at U301 pin 26 while U202 pin 13 continues toggling**. Record which are detected and the isolation time; an undetected case is a hold, not a pass. Repeat with simultaneous USB, SPI1, ADC and logging traffic.
- Update Spec v1.1/Notes v1.0, calculation package R-28/A-26, firmware/RTL requirements and test register only after the architecture is implemented and measured. Until then, retain a visible F01 hold; do not publish all-rate post-CPLD guard or bit-perfect results.

## Reference architectures and primary sources

- [WCH CH32V307 datasheet download, v3.9](https://www.wch-ic.com/downloads/CH32V307DS0_PDF.html): Tables 4-28/4-29, printed pp.73–74. [WCH CH32FV2x/V3x reference manual download, v2.5](https://www.wch-ic.com/downloads/CH32FV2x_V3xRM_PDF.html): GPIO SPI table, TIM3_ETR mapping, DMA1 request map and SPI §§20.2.3–20.2.7.
- [ESS ES9018K2M datasheet v3.7](https://www.esstech.com/wp-content/uploads/2024/09/ES9018K2M-Datasheet-v3.7.pdf): 32-bit/384 kHz PCM input; GPIO2 DPLL-lock status and register 64 status. Lock confirms synchronization, **not** bit equality.
- [RME ADI-2 DAC FS User's Guide v1.8](https://rme-audio.de/downloads/adi2dac_e.pdf), pp.5 and 65: USB playback up to 768 kHz and a built-in special-pattern Bit Test with supplied 44.1/96/192 kHz files. This illustrates that a product's playback-rate claim and its offered bit-test procedure are distinct. It does not establish that limited capture is safe for this project's frozen-word energy requirement.
