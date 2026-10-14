// OD-16 fit skeleton for U202 (AGM AGRV2KQ32): proves LINK_SCK can be a clock on pin 9.
//
// Not the product RTL. It has the paths the fit must close: the SPI receiver clocked by LINK_SCK,
// the FIFO write, the 1024 x 32 dual-clock FIFO, the FAM_CLK-domain I2S master and the register
// read path. Protocol (skeleton only, Notes v1.1 §3.2): SPI mode 0, 16-bit halfwords MSB first,
// LINK_FRAME high for a whole transfer. The first halfword is a header:
//   bit 15 = 0             audio burst: following halfword pairs (high half first) are FIFO words
//   bit 15 = 1, bit 14 = 0  register write: the next halfword is the data for address bits [7:0]
//   bit 15 = 1, bit 14 = 1  register read (9 MHz): the next halfword is shifted out on LINK_MISO
// Registers: 0x00 ID = 0xA6D2, 0x01 VERSION, 0x02 STATUS {.., unf, ovf} (read clears),
// 0x03 CLOCK_CTRL {MCLK_EN, OSC44_EN, OSC48_EN}, 0x04 I2S_CTRL {run (bit 4), divider code [1:0]}.
//
// Clock-domain crossings into FAM_CLK (OD-16 condition 3):
//   audio data      only through the FIFO (Gray pointers, two-flop synchronisers);
//   I2S_CTRL        two-flop synchronisers; quasi-static, written only while run = 0 (Notes 5.x
//                   rate-change sequence stops I2S_RUN first);
//   STATUS clear    toggle handshake into FAM_CLK for the underflow flag.
// Registers live in the LINK_SCK domain because CLOCK_CTRL must work while FAM_CLK is stopped.
`default_nettype none
module link_fit_skeleton (
    input  wire FAM_CLK,      // pin 1 (IO_GB): 49.152 / 45.1584 MHz
    input  wire LINK_SCK,     // pin 9: 36 MHz writes, 9 MHz reads; must be a clock network (OD-16)
    input  wire LINK_MOSI,    // pin 27
    input  wire LINK_FRAME,   // pin 26, active high
    input  wire CPLD_NRST,    // pin 4
    output reg  LINK_MISO,    // pin 28: <= 8 mA or slow slew
    output wire N2_BCLK_SRC,  // pin 18
    output wire N2_LRCLK_SRC, // pin 19
    output wire N2_SDATA_SRC, // pin 20
    output wire N2_CPY_CK,    // pin 21
    output wire N2_CPY_SD,    // pin 22
    output wire LRCLK_FB,     // pin 13: <= 8 mA or slow slew
    output wire CPLD_IRQ,     // pin 3
    output wire OSC48_EN,     // pin 31
    output wire OSC44_EN,     // pin 8
    output wire MCLK_EN       // pin 23
);
    localparam AW = 10;       // 1024 words

    // ------------------------------------------------------------------ LINK_SCK domain
    reg  [3:0]  bitcnt;       // bit within the halfword
    reg  [15:0] sh;           // receive shift register
    reg         in_hdr;       // the next halfword completes the header
    reg  [15:0] hdr;
    reg         hi_valid;     // high half of an audio word received
    reg  [15:0] hi;
    // Frame-scoped counters clear while LINK_FRAME is low (LINK_SCK does not run between frames).
    always @(posedge LINK_SCK or negedge LINK_FRAME or negedge CPLD_NRST)
        if (!LINK_FRAME || !CPLD_NRST) begin
            bitcnt <= 0; in_hdr <= 1'b1; hi_valid <= 1'b0;
        end else begin
            bitcnt <= bitcnt + 1'b1;
            if (bitcnt == 4'd15) begin
                in_hdr <= 1'b0;
                if (!in_hdr && !hdr[15]) hi_valid <= ~hi_valid;
            end
        end
    always @(posedge LINK_SCK) begin
        sh <= {sh[14:0], LINK_MOSI};
        if (bitcnt == 4'd15) begin
            if (in_hdr) hdr <= {sh[14:0], LINK_MOSI};
            if (!in_hdr && !hdr[15] && !hi_valid) hi <= {sh[14:0], LINK_MOSI};
        end
    end
    wire [15:0] half_now = {sh[14:0], LINK_MOSI};
    wire        word_end = LINK_FRAME && !in_hdr && !hdr[15] && hi_valid && bitcnt == 4'd15;
    wire        reg_wr   = LINK_FRAME && !in_hdr && hdr[15] && !hdr[14] && bitcnt == 4'd15;

    // FIFO write side
    reg  [31:0] mem [0:(1 << AW) - 1];
    reg  [AW:0] wptr_bin, wptr_gray;
    reg  [AW:0] rptr_gray_s1, rptr_gray_s2;  // read pointer into LINK_SCK
    wire [AW:0] rptr_gray;
    wire full = wptr_gray == {~rptr_gray_s2[AW:AW-1], rptr_gray_s2[AW-2:0]};
    wire [AW:0] wptr_bin_n = wptr_bin + 1'b1;
    reg  ovf;
    always @(posedge LINK_SCK or negedge CPLD_NRST)
        if (!CPLD_NRST) begin
            wptr_bin <= 0; wptr_gray <= 0; rptr_gray_s1 <= 0; rptr_gray_s2 <= 0;
        end else begin
            {rptr_gray_s2, rptr_gray_s1} <= {rptr_gray_s1, rptr_gray};
            if (word_end && !full) begin
                wptr_bin <= wptr_bin_n; wptr_gray <= wptr_bin_n ^ (wptr_bin_n >> 1);
            end
        end
    always @(posedge LINK_SCK)
        if (word_end && !full) mem[wptr_bin[AW-1:0]] <= {hi, half_now};

    // Registers
    reg [2:0]  clock_ctrl;
    reg [4:0]  i2s_ctrl;
    reg        clr_tgl;       // STATUS read: clear request toggle to FAM_CLK
    reg [1:0]  unf_s;         // underflow flag into LINK_SCK
    wire       unf_fam;
    always @(posedge LINK_SCK or negedge CPLD_NRST)
        if (!CPLD_NRST) begin
            clock_ctrl <= 0; i2s_ctrl <= 0; ovf <= 0; clr_tgl <= 0; unf_s <= 0;
        end else begin
            unf_s <= {unf_s[0], unf_fam};
            if (word_end && full) ovf <= 1'b1;
            if (reg_wr && hdr[7:0] == 8'h03) clock_ctrl <= half_now[2:0];
            if (reg_wr && hdr[7:0] == 8'h04) i2s_ctrl <= half_now[4:0];
            if (in_hdr && bitcnt == 4'd15 && sh[14] && sh[13] && half_now[7:0] == 8'h02) begin
                ovf <= 1'b0; clr_tgl <= ~clr_tgl;   // read of STATUS clears the sticky flags
            end
        end
    assign {MCLK_EN, OSC44_EN, OSC48_EN} = clock_ctrl;

    // Register read: the header's address selects the word, shifted out MSB first, launched on the
    // falling edge so it is valid at the master's next rising edge (9 MHz reads only).
    reg [15:0] rd_sh;
    wire [7:0] rd_addr = half_now[7:0];
    reg [15:0] rd_word;
    always @* case (rd_addr)
        8'h00:   rd_word = 16'hA6D2;
        8'h01:   rd_word = 16'h0001;
        8'h02:   rd_word = {14'b0, unf_s[1], ovf};
        8'h03:   rd_word = {13'b0, clock_ctrl};
        8'h04:   rd_word = {11'b0, i2s_ctrl};
        default: rd_word = 16'h0000;
    endcase
    always @(posedge LINK_SCK)
        if (in_hdr && bitcnt == 4'd15) rd_sh <= rd_word;
    always @(negedge LINK_SCK or negedge LINK_FRAME or negedge CPLD_NRST)
        if (!LINK_FRAME || !CPLD_NRST) LINK_MISO <= 1'b0;
        else if (!in_hdr && hdr[15] && hdr[14]) LINK_MISO <= rd_sh[15 - bitcnt];
    assign CPLD_IRQ = ovf | unf_fam;    // level to the MCU; unf_s would go stale while LINK_SCK idles

    // ------------------------------------------------------------------ FAM_CLK domain
    reg [4:0]  ctrl_s1, ctrl_s2;          // I2S_CTRL, quasi-static
    reg [AW:0] wptr_gray_s1, wptr_gray_s2;
    reg [2:0]  clr_s;
    reg [AW:0] rptr_bin, rptr_gray_r;
    assign rptr_gray = rptr_gray_r;
    wire empty = rptr_gray_r == wptr_gray_s2;
    reg [3:0]  div_cnt;
    reg        bclk, lrclk, sdata;
    reg [5:0]  pos;                       // BCLK falls within the 64-bit frame
    reg [31:0] word, out_sh;
    reg        unf;
    assign unf_fam = unf;
    wire       run = ctrl_s2[4];
    wire [3:0] div_mask = (4'b0001 << ctrl_s2[1:0]) - 1'b1;   // half-period - 1: /2 /4 /8 /16
    wire       half_end = (div_cnt & div_mask) == div_mask;
    wire       fall = run && half_end && bclk;
    wire [AW:0] rptr_bin_n = rptr_bin + 1'b1;
    always @(posedge FAM_CLK or negedge CPLD_NRST)
        if (!CPLD_NRST) begin
            ctrl_s1 <= 0; ctrl_s2 <= 0; wptr_gray_s1 <= 0; wptr_gray_s2 <= 0; clr_s <= 0;
            rptr_bin <= 0; rptr_gray_r <= 0; div_cnt <= 0; bclk <= 0; lrclk <= 0; sdata <= 0;
            pos <= 0; unf <= 0;
        end else begin
            {ctrl_s2, ctrl_s1} <= {ctrl_s1, i2s_ctrl};
            {wptr_gray_s2, wptr_gray_s1} <= {wptr_gray_s1, wptr_gray};
            clr_s <= {clr_s[1:0], clr_tgl};
            if (clr_s[2] ^ clr_s[1]) unf <= 1'b0;
            if (!run) begin
                div_cnt <= 0; bclk <= 0; lrclk <= 0; sdata <= 0; pos <= 0;
            end else begin
                div_cnt <= div_cnt + 1'b1;
                if (half_end) bclk <= ~bclk;
                if (fall) begin                    // SDATA and LRCLK launch on the BCLK-falling edge
                    pos <= pos + 1'b1;
                    lrclk <= pos[5];
                    if (pos[4:0] == 5'd0) begin    // fetch this slot's word (RAM read registered below)
                        if (empty) unf <= 1'b1;
                        else begin rptr_bin <= rptr_bin_n; rptr_gray_r <= rptr_bin_n ^ (rptr_bin_n >> 1); end
                    end
                    if (pos[4:0] == 5'd1) begin sdata <= word[31]; out_sh <= {word[30:0], 1'b0}; end
                    else begin sdata <= out_sh[31]; out_sh <= {out_sh[30:0], 1'b0}; end
                end
            end
        end
    reg fetch_ok;
    always @(posedge FAM_CLK) begin
        fetch_ok <= fall && pos[4:0] == 5'd0 && !empty;
        if (fall && pos[4:0] == 5'd0) word <= 32'd0;        // underflow plays digital zero
        if (fetch_ok) word <= mem[rptr_bin[AW-1:0] - 1'b1];
    end

    assign N2_BCLK_SRC  = bclk;
    assign N2_LRCLK_SRC = lrclk;
    assign N2_SDATA_SRC = sdata;
    assign N2_CPY_CK    = bclk;
    assign N2_CPY_SD    = sdata;
    assign LRCLK_FB     = lrclk;
endmodule
`default_nettype wire
