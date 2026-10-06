"""coupling_screen.py [BOARD_DUMP.json] : coupled-length screen: toggling digital aggressors vs audio / high-Z victims.
Same layer: edge gap < 0.5 mm. Broadside: L3(PWR)/L4(SIG) are 0.109 mm apart in the JLC 6L stack -> lateral edge gap < 0.3 mm.
Also F.Cu<->L2 and B.Cu<->L5 are planes, so no broadside there."""
import json, math, collections, fnmatch, numpy as np
d = json.load(open(__import__("sys").argv[1] if len(__import__("sys").argv) > 1 else "board.json"))
AUD = ["DACL", "DACLB", "DACR", "DACRB", "N4_*", "LEG_*", "JACK_*", "VREF", "AVCC_*", "VCCA", "3V3A", "1V3", "N4_VPOS_IV", "N4_VNEG_IV", "VPOS", "VNEG"]
HIGHZ = ["N6_LW*", "N6_TW*", "N6_OR*", "N6_TLP_*", "N6_TLN_*", "N6_V3R_*", "N6_V3AG_*", "N6_VOR*", "N6_VLL*", "N6_DA_*", "N6_DB_*", "N6_DC_*", "N6_DD_*", "N6_VT", "N6_CML", "N6_CMR", "DC_SENSE*", "N6_MCK_RC", "N6_REF*", "N6_SL_*", "N6_SR_*"]
AGG = ["MCLK", "BCLK", "LRCLK", "SDATA", "USB_D?", "N2_X20*", "N2_HSE_*", "N6_MCK_BUF", "N6_MCK_IN", "N6_MCK_CMP", "N6_PMP", "N6_REFMCK", "LINK_*", "N2_LINK_*", "LRCLK_FB",
       "N2_*_SRC", "N2_CPY_*", "N2_CAP_*", "FAM_CLK", "I2C_*", "SWCLK", "SWDIO", "CPLD_J*", "N5_C1?", "N5_CP", "N5_SW*", "LED_*", "CPLD_IRQ"]
m = lambda n, P: any(fnmatch.fnmatchcase(n, p) for p in P)
segs = [t for t in d["trk"] if t["net"]]
A = [t for t in segs if m(t["net"], AGG)]; V = [t for t in segs if m(t["net"], AUD + HIGHZ) and not m(t["net"], AGG)]
PAIR = {("PWR", "SIG"), ("SIG", "PWR")}
def samples(t, step=0.1):
    a, b = np.array(t["a"]), np.array(t["b"]); n = max(1, int(np.hypot(*(b - a)) / step))
    return a + np.outer((np.arange(n) + .5) / n, b - a), np.hypot(*(b - a)) / n
def segdist(P, t):
    a, b = np.array(t["a"]), np.array(t["b"]); ab = b - a; L2 = ab @ ab
    s = np.clip(((P - a) @ ab) / L2, 0, 1) if L2 else np.zeros(len(P))
    return np.hypot(*(a + np.outer(s, ab) - P).T)
res = collections.defaultdict(lambda: [0.0, 9.0, None])
for v in V:
    P, dl = samples(v)
    for a in A:
        if a["l"] == v["l"]: lim = 0.5; kind = "same"
        elif (a["l"], v["l"]) in PAIR: lim = 0.3; kind = "broadside"
        else: continue
        bx = (min(a["a"][0], a["b"][0]) - 2, max(a["a"][0], a["b"][0]) + 2, min(a["a"][1], a["b"][1]) - 2, max(a["a"][1], a["b"][1]) + 2)
        if max(v["a"][0], v["b"][0]) < bx[0] or min(v["a"][0], v["b"][0]) > bx[1] or max(v["a"][1], v["b"][1]) < bx[2] or min(v["a"][1], v["b"][1]) > bx[3]: continue
        gap = segdist(P, a) - a["w"] / 2 - v["w"] / 2
        k = (v["net"], a["net"], kind); hit = gap < lim
        if hit.any():
            r = res[k]; r[0] += hit.sum() * dl; 
            if gap.min() < r[1]: r[1] = gap.min(); r[2] = (round(float(P[gap.argmin()][0]), 1), round(float(P[gap.argmin()][1]), 1), v["l"], a["l"])
for (vn, an, kind), (L, gmin, where) in sorted(res.items(), key=lambda kv: -kv[1][0]):
    if L >= 0.5: print(f"{vn:16s} <- {an:18s} {kind:9s} {L:5.1f} mm  min gap {gmin:5.2f} @ {where}")
