"""Re-run the reviewer's 2.5-D thermal model (power/thermal_run*.py) on the revised board: normal envelope
state and the F1 fault (5V_ANA dead short, Default, U503 1.24 W), both as built (no 'recommended' vias added)."""
import os, sys
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pw", "power")
sys.path.insert(0, P); os.chdir(P)
import thermal_run as tr
tr.RES.clear()
tr.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thermal_results.json")
B = tr.Board()
tr.run("v2_base", B, tr.P0)
PF = dict(tr.P0); PF.update({"U501": 0.0, "U401": 0.0, "U402": 0.0, "U403": 0.0, "U404": 0.0, "U503": 1.24})
tr.run("v2_F1_state", B, PF)
print("ALL DONE")
