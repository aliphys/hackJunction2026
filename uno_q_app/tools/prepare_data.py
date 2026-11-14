"""Shrink the ORNL recordings to the six air-temperature channels the model uses.

Run on a laptop from the repository root:
    uv run --with pandas python uno_q_app/tools/prepare_data.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "uno_q_app" / "fridge-fault-detector" / "python"
channels = json.loads((APP / "models" / "demo_fault_10m.json").read_text())["input_channels"]

for source in sorted((ROOT / "data").glob("*.csv")):
    raw = pd.read_csv(source, usecols=["Timestamp", *channels])
    raw["Timestamp"] = pd.to_datetime(raw["Timestamp"], format="mixed", errors="raise")
    target = APP / "data" / f"{source.stem}.csv.gz"
    raw[["Timestamp", *channels]].to_csv(target, index=False, date_format="%Y-%m-%dT%H:%M:%S.%f")
    print(f"{source.name}: {len(raw)} rows -> {target.stat().st_size / 1e6:.1f} MB")
