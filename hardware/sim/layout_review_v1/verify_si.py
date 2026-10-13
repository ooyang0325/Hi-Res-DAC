"""Re-run the reviewer's SI transient study (si/sim_nets.py) for the LINK bus on the revised board:
each U208 output now drives its line through R247/R248/R249 (33 ohm). Same driver/receiver models and corners
(LINK_SCK: full 27-corner factorial; MOSI/FRAME: the reviewer's 6-corner set; clamps on, plus off at tr_min)."""
import sys, os, json, time
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "si_run")
sys.path.insert(0, S); os.chdir(S)
import sim_nets as sn
sn.CASES.update({
    "LINK_SCK_v2": dict(nets=["N2_LINK_SCK_OUT", "LINK_SCK"], series=[("R247", 33.0)], drv=("U208.7", "LVC"), rx=[("U202.9", "CPLD")], f=36e6),
    "LINK_MOSI_v2": dict(nets=["N2_LINK_MOSI_OUT", "LINK_MOSI"], series=[("R248", 33.0)], drv=("U208.5", "LVC"), rx=[("U202.27", "CPLD")], f=18e6),
    "LINK_FRAME_v2": dict(nets=["N2_LINK_FRAME_OUT", "LINK_FRAME"], series=[("R249", 33.0)], drv=("U208.2", "LVC"), rx=[("U202.26", "CPLD")], f=18e6),
})
out = {}
for case in ("LINK_SCK_v2", "LINK_MOSI_v2", "LINK_FRAME_v2"):
    t0 = time.time(); rows = []
    trmin = sn.DRIVERS["LVC"]["tr"][0]
    for tr, rf, cf in sn.corners(case, full=case == "LINK_SCK_v2"):
        for cl in ((True, False) if tr == trmin else (True,)):
            r, _ = sn.run_case(case, tr, rf, cf, clamps=cl); rows.append(r)
    pad = sn.CASES[case]["rx"][0][0]
    on = [r for r in rows if r["clamps"]]
    summ = {"runs": len(rows),
            "max_overshoot_V": max(max(r[pad]["rise"]["over"], r[pad]["fall"]["over"]) for r in on),
            "max_clamp_mA": max(max(r[pad]["clamp_up_peak_mA"], r[pad]["clamp_dn_peak_mA"]) for r in on),
            "max_mid_crossings": max(max(r[pad]["rise"]["n_cross_mid"], r[pad]["fall"]["n_cross_mid"]) for r in rows),
            "min_ringback_margin_V": min(min(r[pad]["rise"]["ringback_margin"], r[pad]["fall"]["ringback_margin"]) for r in rows)}
    out[case] = {"summary": summ, "rows": rows}
    print(case, summ, round(time.time() - t0), "s", flush=True)
    json.dump(out, open(os.path.join(os.path.dirname(S), "link_si_results.json"), "w"), indent=0, default=float)
