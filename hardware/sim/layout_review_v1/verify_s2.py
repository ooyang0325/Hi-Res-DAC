"""Re-run the reviewer's MCLK-alive detector MNA study (analog/s2_mclk.py) on the revised layout (block b25).
Path lengths/vias measured from INTEGRATED_AUDIO_MANUAL_DELTA.json after b25; same corners as the reviewer."""
import sys, os, json, time
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analog_run")
sys.path.insert(0, A)
import s2_mclk as s

C_TP_MM = s.C_TP / s.CPM["F.Cu"]          # TP747 pad, now on N6_MCK_CMP, as equivalent F.Cu length
V2 = {
    "buf": ({"F.Cu": 5.40, "In2.Cu": 5.27}, 2, "F2"),          # N6_MCK_BUF unchanged
    "pmp": ({"F.Cu": 3.53}, 0, "F2"),                           # C624.2 -> D609.3 (was 5.90)
    "rc_main": ({"F.Cu": 1.27}, 0, "F2"),                       # D609.2 -> C625.1 (was 11.29 F + 10.21 B, 4 vias)
    "rc_r667": ({"F.Cu": 3.39}, 0, "F2"),                       # D609.2 -> R667.1 (was 10.04 F + 25.51 In2, 4 vias)
    "rc_tp": None,                                              # TP747 left the hold node (ECO F13)
    "mck_in": ({"F.Cu": 1.86}, 0, "F2"),
    "cmp": ({"F.Cu": 15.28 + C_TP_MM, "In2.Cu": 21.12}, 4, "F2"),  # R667.2 -> U606.7, the old trunk, + TP747
}
P0 = s.P0
VTH = {"typ": 3.852 * 100 / 1100, "dead_worst": 0.326, "alive_worst": 0.384}
eq_corners = {
    "typ": dict(P0),
    "alive_worst": dict(P0, v3d=3.20, diode="maxVF", rout607=175.0, tr=4.5e-9, duty=0.45, tpd607=4.6e-9),
    "dead_worst": dict(P0, v3d=3.40, diode="typ", rout607=50.0, tr=1.5e-9, duty=0.55, c625=82e-12 * 1.05, c624=105e-12, r666=1.01e6),
}
corners = {k: dict(v, vth=VTH[k]) for k, v in eq_corners.items()}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "detector_s2_results.json")
res = json.load(open(out)) if os.path.exists(out) else {}
res["parasitics"] = {k: {"mm": sum(v[0].values()), "vias": v[1], "C_pF": s.path_rlc(v[0], v[1], kind=v[2])[0] * 1e12}
                     for k, v in V2.items() if v}
for cn, p in eq_corners.items():
    if cn in res.get("eq", {}): continue
    t0 = time.time(); veq, _ = s.equilibrium(V2, p, p["v3d"] - 0.55)
    i_eq, v_mean, t, X, probes, c, holdC = s.pump_point(V2, p, veq, ncyc=40)
    T = 1 / p["fclk"]; m = t >= t[-1] - 10 * T
    rp = {n: float(X[m, i].max() - X[m, i].min()) for i, n in enumerate(probes)}
    res.setdefault("eq", {})[cn] = {"v_eq": veq, "hold_C_parasitic_pF": holdC * 1e12, "ripple_pp_V": rp}
    print("eq", cn, round(veq, 4), "holdC pF", round(holdC * 1e12, 2), {k: round(v * 1e3, 1) for k, v in rp.items()}, round(time.time() - t0), "s", flush=True)
    json.dump(res, open(out, "w"), indent=1, default=float)
for cn in ("typ", "dead_worst"):
    for lev in ("high", "low"):
        key = f"{cn}/{lev}"
        if key in res.get("dead", {}): continue
        tc, *_ = s.dead_run(V2, corners[cn], res["eq"][cn]["v_eq"], lev)
        res.setdefault("dead", {})[key] = tc
        print("dead", key, tc, flush=True); json.dump(res, open(out, "w"), indent=1, default=float)
for cn in ("typ", "alive_worst"):
    if cn in res.get("alive", {}): continue
    tc, *_ = s.alive_run(V2, corners[cn], t_end=1.0e-6)
    res.setdefault("alive", {})[cn] = tc
    print("alive", cn, tc, flush=True); json.dump(res, open(out, "w"), indent=1, default=float)
