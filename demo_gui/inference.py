import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import lightgbm as lgb
import numpy as np
import pandas as pd

# Load project-local defaults. Explicit environment values take precedence.
def load_endpoint_settings(path):
    settings = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            key, separator, value = line.strip().partition("=")
            key, value = key.strip(), value.strip()
            if separator and key in {"OPENAI_BASE_URL", "OPENAI_MODEL", "OPENAI_API_KEY"}:
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                settings[key] = value
    return settings

ROOT = Path(__file__).resolve().parents[1]
endpoint_settings = load_endpoint_settings(ROOT / ".env")

ENDPOINT_BASE = os.getenv("OPENAI_BASE_URL", endpoint_settings.get("OPENAI_BASE_URL", ""))
ENDPOINT_MODEL = os.getenv("OPENAI_MODEL", endpoint_settings.get("OPENAI_MODEL", ""))
CONTEXT_MINUTES = 10

def load_model(name):
    root = ROOT / "models"
    settings = json.loads((root / f"{name}.json").read_text(encoding="utf-8"))
    return lgb.Booster(model_file=str(root / f"{name}.txt")), settings

binary, binary_settings = load_model("binary")
fault, fault_settings = load_model("fault")
AIR = binary_settings["input_channels"]
LOOKBACK = binary_settings["window_minutes"]
if LOOKBACK != 1 or fault_settings["window_minutes"] != 1 or fault_settings["input_channels"] != AIR:
    raise ValueError("Replay requires matching one-minute models and sensor channels.")

# The feature calculation matches the training notebooks.
def make_windows(path):
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
    features["End"] = features.index + pd.Timedelta(minutes=1)
    features["Start"] = features["End"] - pd.Timedelta(minutes=LOOKBACK)
    return minute, features


def request_body(position, minute, features, binary_scores, fault_scores):
    row = features.iloc[position]
    end = row["End"]
    context = minute.loc[(minute.index >= end - pd.Timedelta(minutes=CONTEXT_MINUTES)) &
                         (minute.index < end)]
    class_position = int(fault_scores[position].argmax())
    status = {
        "binary_alert": True,
        "binary_score": float(binary_scores[position]),
        "binary_threshold": binary_settings["threshold"],
        "fault_model_prediction": fault_settings["labels"][class_position],
        "fault_model_scores": dict(zip(fault_settings["labels"], fault_scores[position].tolist())),
        "alert_time_recorded_clock": end.isoformat(),
    }
    payload = {
        "status": status,
        "table_description": "One-minute temperature medians and air temperature differences in degrees Fahrenheit. Timestamps mark minute starts. Missing readings are blank.",
        "temperature_csv": context.rename_axis("minute_start").to_csv(float_format="%.3f"),
    }
    return {
        "model": ENDPOINT_MODEL,
        "messages": [
            {"role": "system", "content": (
                "Analyze refrigeration alerts from the ORNL laboratory supermarket refrigeration rig "
                "described by Sun et al. (2021), DOI 10.1038/s41597-021-00927-6. The rig uses "
                "a shared transcritical CO2 compressor rack with low-temperature (LT) and medium-temperature "
                "(MT) stages, an LT four-door freezer case, an MT open chilled display case, simulated loads "
                "on both circuits, and an air-cooled gas cooler that rejects heat for the shared system. "
                "The case controllers regulate temperature and defrost. Normal load changes and defrost can "
                "also change the measured air temperatures. "
                "For each evaporator, return air enters the coil and supply air leaves it. The reported air "
                "drop is return minus supply. The gas cooler readings are air temperatures at fan 2, and "
                "the reported air rise is outlet minus inlet. All temperatures are in degrees Fahrenheit. "
                "The six lab scenarios are LT door open, LT evaporator icing, LT expansion valve failure, "
                "MT evaporator fan failure, gas cooler air path blockage, and MT evaporator air path blockage. "
                "Interpret the six sensor channels in that context. Distinguish classifier scores from "
                "observed evidence. If the table has only one minute, avoid inferring a trend or fault onset. "
                "Describe the observed evidence and plausible causes, "
                "note classifier disagreement and uncertainty, and suggest checks an operator can perform. "
                "Use the supplied data as evidence and avoid claiming a confirmed diagnosis."
            )},
            {"role": "user", "content": json.dumps(payload, allow_nan=False)},
        ],
    }


def send_for_analysis(body, opener=urlopen):
    if not ENDPOINT_BASE.startswith(("https://", "http://")) or not ENDPOINT_MODEL:
        raise ValueError("Set OPENAI_BASE_URL and OPENAI_MODEL before sending.")
    headers = {"Content-Type": "application/json"}
    if key := os.getenv("OPENAI_API_KEY", endpoint_settings.get("OPENAI_API_KEY")):
        headers["Authorization"] = f"Bearer {key}"
    request = Request(ENDPOINT_BASE.rstrip("/") + "/chat/completions",
                      data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    with opener(request, timeout=30) as response:
        return json.load(response)["choices"][0]["message"]["content"]


def analyze_waveform(source, analyze=send_for_analysis):
    minute, features = make_windows(source)
    if features.empty:
        raise ValueError("The recording has no complete scoring windows.")
    binary_scores = binary.predict(features[binary_settings["feature_names"]], num_threads=2)
    fault_scores = fault.predict(features[fault_settings["feature_names"]], num_threads=2)
    alerts = pd.Series(binary_scores >= binary_settings["threshold"], index=features.index)
    gaps = alerts.index.to_series().diff().ne(pd.Timedelta(minutes=1))
    onsets = alerts & (~alerts.shift(fill_value=False) | gaps)

    chart = minute[AIR].astype(object).where(minute[AIR].notna(), None)
    positions = np.flatnonzero(onsets.to_numpy())
    result = {
        "minutes": len(features), "flagged": int(alerts.sum()), "onsets": len(positions),
        "fault": None, "time": None, "alert_index": None,
        "traces": chart.to_dict(orient="list"),
        "analysis": "No fault alert was detected.",
    }
    if len(positions):
        position = positions[0]
        body = request_body(position, minute, features, binary_scores, fault_scores)
        status = json.loads(body["messages"][-1]["content"])["status"]
        result.update(
            fault=status["fault_model_prediction"],
            time=status["alert_time_recorded_clock"],
            alert_index=int(minute.index.get_loc(features.index[position])),
        )
        try:
            analysis = analyze(body)
            result["analysis"] = analysis or "The endpoint returned no analysis text."
        except HTTPError as error:
            result["analysis"] = f"Verda returned HTTP {error.code}."
        except (URLError, TimeoutError):
            result["analysis"] = "Verda was unavailable or timed out."
        except (ValueError, KeyError, IndexError, TypeError):
            result["analysis"] = "Check the endpoint settings or response format."
    return result
