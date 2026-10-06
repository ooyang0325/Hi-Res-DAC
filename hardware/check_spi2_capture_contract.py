#!/usr/bin/env python3
"""Check the proposed SPI2 post-CPLD capture *arithmetic* and bit framing.

No MCU, RTL, electrical timing, DMA arbitration, or fault behavior is exercised.
See MCU_SPI2_CAPTURE_ECO.md before treating these numbers as design evidence.
"""

from __future__ import annotations

from fractions import Fraction
from random import Random


RATES_HZ = (44_100, 48_000, 88_200, 96_000, 176_400, 192_000, 352_800, 384_000)
I2S_LIMIT_HZ = 8_000_000  # WCH CH32V307 datasheet v3.9, Table 4-29
SPI_SLAVE_LIMIT_HZ = 72_000_000  # Same datasheet, Table 4-28
BITS_PER_STEREO_FRAME = 64
SPI_WORD_BITS = 16
DMA_HALF_TARGET_S = Fraction(1, 2_500)  # 0.40 ms, leaving room for next-word lookahead
PROCESS_BUDGET_S = Fraction(1, 10_000)  # 0.10 ms, to be measured
P1_RUN_S = Fraction(22, 1_000)
SWITCH_OPEN_S = Fraction(1_008, 1_000_000)  # Calculation-package assumption
DMA_STALL_S = Fraction(2, 1_000)  # Existing proposed firmware rule
MASK32 = (1 << 32) - 1
MASK64 = (1 << 64) - 1


def require(ok: bool, why: str) -> None:
    if not ok:
        raise SystemExit(f"SPI2 capture contract FAIL: {why}")


def bit_vector(word: int) -> list[int]:
    return [(word >> bit) & 1 for bit in range(31, -1, -1)]


def raw_philips_frame(previous_right: int, left: int, right: int) -> int:
    """Sample 64 BCLKs from a WS edge; each new MSB is delayed one bit.

    Raw frame = previous right LSB, all 32 left bits, upper 31 right bits.
    The current right LSB becomes the first bit of the next raw frame.
    """
    bits = [previous_right & 1] + bit_vector(left) + bit_vector(right)[:31]
    require(len(bits) == BITS_PER_STEREO_FRAME, "Philips frame is not 64 bits")
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


def reconstruct(raw: int, following_raw: int) -> tuple[int, int]:
    shifted = ((raw << 1) & MASK64) | (following_raw >> 63)
    return shifted >> 32, shifted & MASK32


def check_framing() -> int:
    rng = Random(0xDAC2026)
    tested = 0
    ws = [0] * 32 + [1] * 32
    require(len(ws) == 64 and ws[31] == 0 and ws[32] == 1,
            "WS must divide each 64-bit frame into two 32-bit slots")
    for word_width in (16, 24, 32):
        # Include extrema, bit patterns, and deterministic pseudo-random samples.
        samples = [
            (0, 0),
            (MASK32 & (~((1 << (32 - word_width)) - 1)), 0),
            (0xAAAAAAAA & (~((1 << (32 - word_width)) - 1)),
             0x55555555 & (~((1 << (32 - word_width)) - 1))),
        ]
        samples.extend(
            (rng.getrandbits(word_width) << (32 - word_width),
             rng.getrandbits(word_width) << (32 - word_width))
            for _ in range(256)
        )
        raw = []
        previous_right = 0
        for left, right in samples:
            frame = raw_philips_frame(previous_right, left, right)
            words = [(frame >> shift) & 0xFFFF for shift in (48, 32, 16, 0)]
            require(len(words) == 4, "SPI2 must receive four 16-bit words per frame")
            require(sum(word << shift for word, shift in zip(words, (48, 32, 16, 0))) == frame,
                    "SPI word ordering changed the raw bitstream")
            raw.append(frame)
            previous_right = right
        raw.append(raw_philips_frame(previous_right, 0, 0))
        for (left, right), current, following in zip(samples, raw, raw[1:]):
            require(reconstruct(current, following) == (left, right),
                    f"{word_width}-bit left/right reconstruction failed")
            tested += 1
        # A known non-periodic test stream must expose a one-BCLK start-phase error.
        index = 100
        one_bit_late = ((raw[index] << 1) & MASK64) | (raw[index + 1] >> 63)
        following_late = ((raw[index + 1] << 1) & MASK64) | (raw[index + 2] >> 63)
        require(reconstruct(one_bit_late, following_late) != samples[index],
                f"{word_width}-bit known-pattern test missed a one-bit phase slip")
    return tested


def check_ws_witness_limits() -> None:
    """Show what an EXTI edge-presence latch and pin-13 frame count miss."""
    frames = 17  # Smallest proposed DMA half-buffer, at 44.1 kHz.
    normal_ws = ([0] * 32 + [1] * 32) * frames

    def edges(levels: list[int]) -> int:
        return sum(a != b for a, b in zip(levels, levels[1:]))

    def exti_edge_seen(levels: list[int]) -> bool:
        # EXTI_INTFR is a sticky flag: one edge and many edges look alike.
        return edges(levels) != 0

    require(edges(normal_ws) == 2 * frames - 1,
            "normal WS transition count within a half-buffer changed")
    require(exti_edge_seen(normal_ws), "normal PB12 WS has no edge")
    require(not exti_edge_seen([0] * len(normal_ws)),
            "PB12 EXTI witness failed to distinguish a stuck source")

    glitched_source = normal_ws.copy()
    glitched_source[10] ^= 1
    require(exti_edge_seen(glitched_source) == exti_edge_seen(normal_ws),
            "edge-presence latch unexpectedly identifies a short WS glitch")

    # A fault after R205 changes U301's WS while PB12 and pin-13 LRCLK_FB
    # retain their nominal source waveforms. Neither present witness detects it.
    dac_ws_stuck = [0] * len(normal_ws)
    dac_ws_wrong_phase = [1 - level for level in normal_ws]
    source_pin13_frames = frames
    require(exti_edge_seen(normal_ws) and source_pin13_frames == frames,
            "the existing MCU witnesses should remain nominal in this example")
    require(dac_ws_stuck != normal_ws and dac_ws_wrong_phase != normal_ws,
            "DAC-side WS fault examples are not distinct from normal")
    require(edges(dac_ws_wrong_phase) == edges(normal_ws),
            "same-count DAC-side phase fault should retain the edge count")
    print("WS witness model: PB12 edge presence catches a stuck source,"
          " but misses short glitches and faults after R205")


def check_rates() -> None:
    require(len(RATES_HZ) == 8 and len(set(RATES_HZ)) == 8,
            "expected eight distinct advertised rates")
    require(BITS_PER_STEREO_FRAME // SPI_WORD_BITS == 4,
            "one stereo frame must be four 16-bit DMA transfers")
    print("fs (kHz)  BCLK (MHz)  SPI words/s  frames/half  half (ms)  full DMA (B)")
    max_decision = Fraction(0)
    max_p1_to_open = Fraction(0)
    for fs in RATES_HZ:
        bclk = BITS_PER_STEREO_FRAME * fs
        transfers_per_second = bclk // SPI_WORD_BITS
        frames_per_half = fs // 2_500
        half_interval = Fraction(frames_per_half, fs)
        lookahead_interval = Fraction(SPI_WORD_BITS, bclk)
        half_words = 4 * frames_per_half
        full_buffer_bytes = 2 * half_words * 2
        decision = half_interval + lookahead_interval + PROCESS_BUDGET_S
        p1_count = (22 * fs + 999) // 1_000
        p1_run = Fraction(p1_count, fs)
        p1_to_open = p1_run + decision + SWITCH_OPEN_S
        require(bclk <= SPI_SLAVE_LIMIT_HZ, f"{fs} Hz exceeds the SPI slave limit")
        require(transfers_per_second == 4 * fs, f"{fs} Hz transfer-rate mismatch")
        require(0 < half_interval <= DMA_HALF_TARGET_S,
                f"{fs} Hz half-buffer interval exceeds 0.4 ms")
        require(decision <= Fraction(6, 10_000),
                f"{fs} Hz exceeds the assumed 0.60 ms decision time")
        require(full_buffer_bytes <= 2_448, f"{fs} Hz buffer exceeds 2,448 B")
        require(p1_run >= P1_RUN_S, f"{fs} Hz P1 sample count is too short")
        max_decision = max(max_decision, decision)
        max_p1_to_open = max(max_p1_to_open, p1_to_open)
        print(f"{fs/1000:8.1f}  {bclk/1e6:10.4f}  {transfers_per_second:11,d}"
              f"  {frames_per_half:11,d}  {float(half_interval*1000):9.6f}"
              f"  {full_buffer_bytes:12,d}")

    over_i2s = tuple(fs for fs in RATES_HZ if BITS_PER_STEREO_FRAME * fs > I2S_LIMIT_HZ)
    require(over_i2s == (176_400, 192_000, 352_800, 384_000),
            "expected four rates above the published I2S2 limit")
    stall_to_open = DMA_STALL_S + SWITCH_OPEN_S
    require(max_p1_to_open <= Fraction(24, 1_000),
            "P1 isolation assumption exceeds 24 ms")
    require(stall_to_open == Fraction(3_008, 1_000_000),
            "DMA-stall isolation assumption changed")
    print(f"\nAssumed worst post-CPLD decision: {float(max_decision*1000):.3f} ms")
    print(f"Assumed P1 run-to-switch-open:    {float(max_p1_to_open*1000):.3f} ms")
    print(f"Assumed DMA-stall-to-open:        {float(stall_to_open*1000):.3f} ms")


def main() -> None:
    check_rates()
    framing_vectors = check_framing()
    check_ws_witness_limits()
    print(f"Philips one-bit framing: {framing_vectors} deterministic vectors checked")
    print("Contract arithmetic PASS; DAC-side WS integrity and F01 remain on HOLD")
    print("Hardware, RTL, firmware and PCB timing UNVERIFIED")


if __name__ == "__main__":
    main()
