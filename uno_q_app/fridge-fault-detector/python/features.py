"""Feature calculation for the refrigeration fault model.

This mirrors ``make_windows`` in demo_gui/inference.py, which matches the
training notebooks. The recordings here already hold only the timestamp and the
six air-temperature channels (see uno_q_app/tools/prepare_data.py).
"""
import numpy as np
import pandas as pd


def make_windows(path, channels, lookback):
    raw = pd.read_csv(path, usecols=["Timestamp", *channels])
    stamps = pd.to_datetime(raw.pop("Timestamp"), errors="raise")
    raw = raw.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    raw["Freezer air drop"] = raw[channels[0]] - raw[channels[1]]
    raw["Chilled air drop"] = raw[channels[2]] - raw[channels[3]]
    raw["Gas cooler air rise"] = raw[channels[5]] - raw[channels[4]]
    ordered = raw.iloc[np.argsort(stamps.to_numpy(), kind="stable")]
    bins = stamps.sort_values(kind="stable").dt.floor("min")
    grouped = ordered.groupby(bins)
    minute = grouped.median()
    features = pd.concat([
        minute.add_suffix(" median"),
        grouped.std(ddof=0).add_suffix(" std"),
        (grouped.last() - grouped.first()).add_suffix(" change"),
    ], axis=1)
    complete = grouped.count().ge(2).all(axis=1)
    features = features.loc[complete].copy()
    if lookback > 1:
        clock = pd.date_range(minute.index.min(), minute.index.max(), freq="min")
        levels = minute.where(complete, axis=0).reindex(clock)
        history = levels.rolling(lookback)
        features = features.join(pd.concat([
            history.median().add_suffix(" history median"),
            history.std(ddof=0).add_suffix(" history std"),
            levels.diff(lookback - 1).add_suffix(" history change"),
        ], axis=1)).dropna()
    return minute, features
