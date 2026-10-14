# OD-16 timing for the fit skeleton. Close setup and hold at 36 MHz on LINK_SCK with margin.
create_clock -name LINK_SCK -period 27.778 [get_ports LINK_SCK]
create_clock -name FAM_CLK  -period 20.345 [get_ports FAM_CLK]     ;# 49.152 MHz (45.1584 MHz is slower)
set_clock_groups -asynchronous -group {LINK_SCK} -group {FAM_CLK}  ;# crossings: FIFO Gray pointers + 2-FF syncs
# SPI mode 0: the MCU launches MOSI/FRAME on the SCK falling edge; SCK, MOSI and FRAME all pass through U208,
# so the skew between them is at most its channel-to-channel tpd spread (1.4-4.1 ns): +-2.7 ns.
set_input_delay -clock LINK_SCK -clock_fall -max  2.7 [get_ports {LINK_MOSI LINK_FRAME}]
set_input_delay -clock LINK_SCK -clock_fall -min -2.7 [get_ports {LINK_MOSI LINK_FRAME}]
# LINK_MISO is used only for 9 MHz register reads (read margin +36.6 ns, Notes v1.1 3.2); no output delay here.
