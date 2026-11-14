"""Check on the board that local scores equal the LightGBM reference scores.

models/reference_scores.json holds LightGBM's own output for 40 windows of each
recording (written by uno_q_app/tools/verify.py on a laptop). This recomputes
those windows from the recordings with the app's code and reports the gap and
the time per window.
"""
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

from features import make_windows
from lgbm_lite import Booster

HERE = Path(__file__).resolve().parent
settings = json.loads((HERE / "models" / "demo_fault_10m.json").read_text(encoding="utf-8"))
model = Booster(HERE / "models" / "demo_fault_10m.txt")
reference = json.loads((HERE / "models" / "reference_scores.json").read_text(encoding="utf-8"))

worst, mismatches, checked = 0.0, 0, 0
for name, expected in reference.items():
    started = time.perf_counter()
    _, features = make_windows(
        HERE / "data" / f"{name}.csv.gz", settings["input_channels"], settings["window_minutes"]
    )
    loaded = time.perf_counter() - started
    rows = features.loc[pd.to_datetime(expected["times"]), settings["feature_names"]].to_numpy()
    wanted = np.array(expected["scores"])
    started = time.perf_counter()
    scores = np.vstack([model.predict(row) for row in rows])
    each = (time.perf_counter() - started) / len(rows) * 1000
    gap = float(np.abs(scores - wanted).max())
    wrong = int((scores.argmax(axis=1) != wanted.argmax(axis=1)).sum())
    worst, mismatches, checked = max(worst, gap), mismatches + wrong, checked + len(rows)
    print(f"{name:32s} load {loaded:4.1f} s  {each:5.2f} ms/window  gap {gap:.1e}  mismatches {wrong}")

print(f"{checked} windows, largest score gap {worst:.1e}, {mismatches} label mismatches")
sys.exit(1 if mismatches or worst > 1e-9 else 0)
