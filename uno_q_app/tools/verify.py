"""Check the numpy evaluator against LightGBM and write reference scores.

Run on a laptop from the repository root:
    uv run --with lightgbm --with pandas python uno_q_app/tools/verify.py

It scores every window of every recording twice: once with LightGBM on the
original CSV using the feature code from demo_gui/inference.py, and once with
lgbm_lite on the reduced recording using the app's feature code. It also saves
a sample of LightGBM scores so the board can repeat the check offline
(python/selftest.py).
"""
import json
from pathlib import Path
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "uno_q_app" / "fridge-fault-detector" / "python"
sys.path.insert(0, str(APP))

from features import make_windows  # noqa: E402
from lgbm_lite import Booster  # noqa: E402

settings = json.loads((APP / "models" / "demo_fault_10m.json").read_text())
AIR, LOOKBACK, NAMES = settings["input_channels"], settings["window_minutes"], settings["feature_names"]
reference = lgb.Booster(model_file=str(APP / "models" / "demo_fault_10m.txt"))
lite = Booster(APP / "models" / "demo_fault_10m.txt")


def original_windows(path):
    """Copied from demo_gui/inference.py so the comparison is independent of the app code."""
    raw = pd.read_csv(path, usecols=["Timestamp", *AIR])
    stamps = pd.to_datetime(raw.pop("Timestamp"), format="mixed", errors="raise")
    raw = raw.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    raw["Freezer air drop"] = raw[AIR[0]] - raw[AIR[1]]
    raw["Chilled air drop"] = raw[AIR[2]] - raw[AIR[3]]
    raw["Gas cooler air rise"] = raw[AIR[5]] - raw[AIR[4]]
    ordered = raw.iloc[np.argsort(stamps.to_numpy(), kind="stable")]
    bins = stamps.sort_values(kind="stable").dt.floor("min")
    grouped = ordered.groupby(bins)
    minute = grouped.median()
    features = pd.concat([
        minute.add_suffix(" median"),
        grouped.std(ddof=0).add_suffix(" std"),
        (grouped.last() - grouped.first()).add_suffix(" change"),
    ], axis=1)
    features = features.loc[grouped.count().ge(2).all(axis=1)].copy()
    clock = pd.date_range(minute.index.min(), minute.index.max(), freq="min")
    levels = minute.where(grouped.count().ge(2).all(axis=1), axis=0).reindex(clock)
    history = levels.rolling(LOOKBACK)
    return features.join(pd.concat([
        history.median().add_suffix(" history median"),
        history.std(ddof=0).add_suffix(" history std"),
        levels.diff(LOOKBACK - 1).add_suffix(" history change"),
    ], axis=1)).dropna()


sample, worst, total, disagreements = {}, 0.0, 0, 0
for source in sorted((ROOT / "data").glob("*.csv")):
    expected_features = original_windows(source)
    expected = reference.predict(expected_features[NAMES], num_threads=2)
    _, features = make_windows(APP / "data" / f"{source.stem}.csv.gz", AIR, LOOKBACK)
    if not features.index.equals(expected_features.index):
        raise SystemExit(f"{source.stem}: window times differ")
    scores = lite.predict(features[NAMES].to_numpy())
    gap = float(np.abs(scores - expected).max())
    wrong = int((scores.argmax(axis=1) != expected.argmax(axis=1)).sum())
    worst, total, disagreements = max(worst, gap), total + len(scores), disagreements + wrong
    print(f"{source.stem:32s} windows={len(scores):5d} max score gap={gap:.2e} label mismatches={wrong}")
    picks = np.linspace(0, len(scores) - 1, 40).astype(int)
    sample[source.stem] = {
        "times": [features.index[i].isoformat() for i in picks],
        "scores": expected[picks].tolist(),
    }

(APP / "models" / "reference_scores.json").write_text(json.dumps(sample))
print(f"\n{total} windows, largest score gap {worst:.2e}, {disagreements} label mismatches")
sys.exit(1 if disagreements or worst > 1e-9 else 0)
