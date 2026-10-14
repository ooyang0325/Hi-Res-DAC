# OD-16 timing for the fit skeleton. Close setup and hold at 36 MHz on LINK_SCK with margin.
create_clock -name LINK_SCK -period 27.778 [get_ports LINK_SCK]
create_clock -name FAM_CLK  -period 20.345 [get_ports FAM_CLK]     ;# 49.152 MHz (45.1584 MHz is slower)
set_clock_groups -asynchronous -group {LINK_SCK} -group {FAM_CLK}  ;# crossings: FIFO Gray pointers + 2-FF syncs
# SPI mode 0: the MCU launches MOSI/FRAME on the SCK falling edge; SCK, MOSI and FRAME all pass through U208,
# so the skew between them is at most its channel-to-channel tpd spread (1.4-4.1 ns): +-2.7 ns.
set_input_delay -clock LINK_SCK -clock_fall -max  2.7 [get_ports {LINK_MOSI LINK_FRAME}]
set_input_delay -clock LINK_SCK -clock_fall -min -2.7 [get_ports {LINK_MOSI LINK_FRAME}]
# LINK_MISO is used only for 9 MHz register reads (read margin +36.6 ns, Notes v1.1 3.2); no output delay here.
# LINK_FRAME also clears LINK_MISO_reg (falling-edge flop) asynchronously. FRAME changes only while SCK idles
# (it rises 1/2 period before the first rising edge, falls 1/2 period after the last falling edge), so the
# first falling edge after the release is >= 1.5 periods away. The single-clock model above instead pairs it
# with the same falling edge (removal -1.3 ns, an edge that does not exist). Supra has no -hold option.
set_false_path -from [get_ports LINK_FRAME] -to [get_registers LINK_MISO*]
