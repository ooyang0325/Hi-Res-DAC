// Functional check of link_fit_skeleton.v (iverilog): register access at 9 MHz, audio bursts at
// 36 MHz through the dual-clock FIFO, I2S out at 192 kHz (/4) and 384 kHz (/2) from a 49.152 MHz
// FAM_CLK with an unrelated phase, and the underflow flag, IRQ and read-to-clear.
//   iverilog -g2012 -o /tmp/link_tb link_fit_skeleton.v link_fit_skeleton_tb.v && vvp /tmp/link_tb
`timescale 1ps/1ps
module link_fit_skeleton_tb;
    reg fam = 0, sck = 0, mosi = 0, frame = 0, nrst = 1;
    wire miso, bclk, lrclk, sdata, cpy_ck, cpy_sd, lrclk_fb, irq, osc48, osc44, mclk_en;
    link_fit_skeleton dut(.FAM_CLK(fam), .LINK_SCK(sck), .LINK_MOSI(mosi), .LINK_FRAME(frame),
        .CPLD_NRST(nrst), .LINK_MISO(miso), .N2_BCLK_SRC(bclk), .N2_LRCLK_SRC(lrclk),
        .N2_SDATA_SRC(sdata), .N2_CPY_CK(cpy_ck), .N2_CPY_SD(cpy_sd), .LRCLK_FB(lrclk_fb),
        .CPLD_IRQ(irq), .OSC48_EN(osc48), .OSC44_EN(osc44), .MCLK_EN(mclk_en));

    initial begin #3711; forever #10173 fam = ~fam; end      // 49.152 MHz, arbitrary phase

    integer errors = 0;
    task check(input bit ok, input [255:0] what);
        if (!ok) begin errors = errors + 1; $display("FAIL: %0s", what); end
    endtask

    // One SPI transfer, mode 0: MOSI changes while SCK is low, both sides sample on the rising edge.
    reg [15:0] rx;
    task xfer(input [15:0] h0, input [15:0] h1, input integer n, input integer half_ps,
              input [31:0] words_base, input integer nwords);
        integer i, b, k; reg [15:0] w;
        begin
            frame = 1; #(half_ps);
            for (i = 0; i < n + 2 * nwords; i = i + 1) begin
                w = i == 0 ? h0 : (nwords == 0 ? h1 : (i % 2 ? (words_base + (i - 1) / 2) >> 16
                                                             : (words_base + (i - 1) / 2) & 16'hFFFF));
                for (b = 15; b >= 0; b = b - 1) begin
                    mosi = w[b]; #(half_ps); sck = 1; rx = {rx[14:0], miso}; #(half_ps); sck = 0;
                end
            end
            #(half_ps); frame = 0; #(4 * half_ps);
        end
    endtask
    localparam W36 = 13889, R9 = 55556;                         // half periods: 36 MHz, 9 MHz
    task reg_write(input [7:0] a, input [15:0] d); xfer({8'h80, a}, d, 2, R9, 0, 0); endtask
    task reg_read(input [7:0] a, output [15:0] d); begin xfer({8'hC0, a}, 16'h0, 2, R9, 0, 0); d = rx; end endtask
    // Audio: header 0x0000, then words base, base+1, ... (high half first)
    task push(input [31:0] base, input integer n); xfer(16'h0000, 0, 1, W36, base, n); endtask

    // I2S capture (Philips): the LSB of a word coincides with the LRCLK change.
    reg [31:0] acc, got [0:1023]; integer cnt = 0, ngot = 0; reg last_lr = 0;
    always @(posedge bclk) begin
        if (lrclk != last_lr) begin
            if (cnt == 31) begin got[ngot] = {acc[30:0], sdata}; ngot = ngot + 1; end
            cnt = 0; acc = 0;
        end else begin acc = {acc[30:0], sdata}; cnt = cnt + 1; end
        last_lr = lrclk;
    end

    task stream_check(input [31:0] base, input integer pushed, input [255:0] what);
        integer i, first;
        begin
            first = got[0] - base;
            check(ngot > 100, what);
            for (i = 0; i < ngot; i = i + 1)
                if (got[i] !== base + first + i) begin
                    check(0, what); $display("  word %0d: got %h, expected %h", i, got[i], base + first + i); i = ngot;
                end
            $display("%0s: %0d words in order from FIFO index %0d", what, ngot, first);
        end
    endtask

    reg [15:0] d;
    initial begin
        #10000 nrst = 0; #100000 nrst = 1; #100000;            // power-on reset pulse
        reg_read(8'h00, d); check(d == 16'hA6D2, "ID read at 9 MHz");
        reg_write(8'h03, 16'h0001); check(osc48 && !osc44 && !mclk_en, "CLOCK_CTRL write drives OSC48_EN");
        reg_read(8'h03, d); check(d == 16'h0001, "CLOCK_CTRL read-back");

        // 192 kHz: divider code 1 (/4). Pre-fill 400 words, run, keep feeding in bursts.
        push(32'h1000_0000, 200); push(32'h1000_0000 + 200, 200);
        reg_write(8'h04, 16'h0011);
        #800000000;                                              // ~300 of 400 words played
        stream_check(32'h1000_0000, 400, "192 kHz stream through FIFO");
        check(!irq, "no IRQ while the FIFO had data");
        #400000000;                                              // the other ~100 words, then underflow
        check(irq, "IRQ on FIFO underflow");
        reg_write(8'h04, 16'h0001);                              // stop, then read STATUS (read clears)
        reg_read(8'h02, d); check(d[1], "STATUS shows underflow"); #2000000;
        check(!irq, "STATUS read clears the underflow IRQ");
        reg_read(8'h02, d); check(d[1:0] == 2'b00, "STATUS clear");

        // 384 kHz: divider code 0 (/2) from an empty FIFO.
        ngot = 0; cnt = 0;
        push(32'h2000_0000, 250); push(32'h2000_0000 + 250, 250);
        reg_write(8'h04, 16'h0010);
        #500000000;
        stream_check(32'h2000_0000, 500, "384 kHz stream through FIFO");
        check(!irq, "no IRQ at 384 kHz while the FIFO had data");
        if (errors == 0) $display("PASS"); else $display("FAILED: %0d checks", errors);
        $finish;
    end
endmodule
