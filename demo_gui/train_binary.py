"""Train the demo binary model offline using time blocks from every recording."""
import json
import numpy as np
import pandas as pd
from lightgbm import Dataset, train
from inference import ROOT, fault_settings, load_model, make_windows

_, binary_settings = load_model("binary")

LOOKBACK = 10
frames = []
for path in sorted((ROOT / "data").glob("*.csv")):
    if not path.stem.startswith(("BaselineTest", "Fault")):
        continue
    minute, features = make_windows(path, lookback=LOOKBACK)
    names = features.columns.drop(["Start", "End"]).tolist()
    elapsed = ((features.index - minute.index.min()).total_seconds() / 60).astype(int)
    valid = elapsed % 60 >= LOOKBACK - 1
    rows = features.loc[valid, names].copy()
    rows["block"] = (elapsed[valid] // 60) % 5
    rows["run"] = path.stem
    rows["target"] = int(path.stem.startswith("Fault"))
    rows["fault"] = int(path.stem[5]) if rows["target"].iat[0] else 0
    frames.append(rows)
data = pd.concat(frames)
training = data[data.block < 3]
validation = data[data.block == 3].copy()
test = data[data.block == 4].copy()
model = train(
    dict(objective="binary", num_leaves=15, learning_rate=.05,
         min_data_in_leaf=30, num_threads=2, verbosity=-1, seed=42),
    Dataset(training[names], label=training.target), num_boost_round=180,
)
for rows in (validation, test):
    rows["score"] = model.predict(rows[names], num_threads=2)

# Target at most 5% flagged minutes in each validation baseline.
threshold = float(np.nextafter(max(
    rows.score.quantile(.95, interpolation="higher")
    for _, rows in validation[validation.target == 0].groupby("run")
), np.inf))
for label, rows in (("validation", validation), ("test", test)):
    print(label, "threshold", threshold)
    print(rows.assign(flagged=rows.score >= threshold).groupby("run").flagged.mean().round(3))
fault_model = train(
    dict(objective="multiclass", num_class=7, num_leaves=15, learning_rate=.05,
         min_data_in_leaf=30, num_threads=2, verbosity=-1, seed=42),
    Dataset(training[names], label=training.fault), num_boost_round=180,
)
print("Fault-type test accuracy:", np.mean(fault_model.predict(test[names]).argmax(axis=1) == test.fault))
for name, booster, settings in [
    ("demo_binary_10m", model, {**binary_settings, "threshold": threshold}),
    ("demo_fault_10m", fault_model, fault_settings),
]:
    booster.save_model(str(ROOT / "models" / f"{name}.txt"))
    settings = {**settings, "window_minutes": LOOKBACK, "feature_names": names}
    (ROOT / "models" / f"{name}.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


