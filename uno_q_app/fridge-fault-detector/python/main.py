"""Refrigeration fault detector for the Arduino UNO Q.

Replays a recorded day of air-temperature readings minute by minute and scores
each ten-minute window with the saved LightGBM fault model. Everything runs on
the board: feature calculation with pandas, tree evaluation with numpy
(lgbm_lite), the web page, and the LED matrix. Explanations are optional.
"""
import json
import os
from pathlib import Path
import threading
import time
from urllib.request import Request, urlopen

import numpy as np

from arduino.app_bricks.web_ui import WebUI
from arduino.app_utils import App, Bridge

from features import make_windows
from lgbm_lite import Booster

HERE = Path(__file__).resolve().parent
MODEL = "demo_fault_10m"
SPEEDS = (1, 2, 5, 10, 30)  # recorded minutes per second of replay
MAX_READINGS = 30  # most readings per channel sent to Nemotron for one block
PROVIDERS = {"nemotron": "OPENAI", "gemini": "AI_STUDIO"}
endpoint_locks = {provider: threading.Lock() for provider in PROVIDERS}


def endpoint_settings(provider):
    prefix = PROVIDERS[provider]
    keys = tuple(f"{prefix}_{suffix}" for suffix in ("BASE_URL", "MODEL", "API_KEY"))
    defaults = {}
    for directory in HERE.parents:
        config = directory / ".env"
        if config.is_file():
            for line in config.read_text(encoding="utf-8-sig").splitlines():
                key, separator, value = line.partition("=")
                if separator and key.strip() in keys:
                    defaults.setdefault(key.strip(), value.strip().strip("\"'"))
    return [os.getenv(key, defaults.get(key, "")) for key in keys]

settings = json.loads((HERE / "models" / f"{MODEL}.json").read_text(encoding="utf-8"))
LABELS = settings["labels"]
CHANNELS = settings["input_channels"]
LOOKBACK = settings["window_minutes"]
model = Booster(HERE / "models" / f"{MODEL}.txt")

# The scenario each recording was made under, from the dataset file names.
SCENARIOS = {
    "Baseline": 0, "Fault1": 1, "Fault2": 2, "Fault3": 3, "Fault4": 4, "Fault5": 5, "Fault6": 6,
}
RECORDINGS = {
    path.name.removesuffix(".csv.gz"): path for path in sorted((HERE / "data").glob("*.csv.gz"))
}


def scenario(name):
    return LABELS[next(index for prefix, index in SCENARIOS.items() if name.startswith(prefix))]


class Player:
    def __init__(self):
        self.lock = threading.RLock()
        self.cache = {}
        self.name = None
        self.minute = self.features = self.matrix = None
        self.position = 0
        self.playing = False
        self.speed = 5
        self.predicted = []
        self.timings = {}
        self.shown = None
        self.latest = None
        self.sequence = 0
        self.explanations = {}

    def load(self, name):
        if name not in RECORDINGS:
            raise ValueError("Unknown recording.")
        if name not in self.cache:
            started = time.perf_counter()
            minute, features = make_windows(RECORDINGS[name], CHANNELS, LOOKBACK)
            print(f"Loaded {name}: {len(features)} windows in {time.perf_counter() - started:.1f} s")
            self.cache = {name: (minute, features)}  # keep one recording in memory
        with self.lock:
            self.minute, self.features = self.cache[name]
            self.matrix = self.features[settings["feature_names"]].to_numpy()
            self.name, self.position, self.playing = name, 0, False
            self.predicted = [None] * len(self.features)
            self.timings.clear()
            self.latest = None
            self.explanations = {}

    def describe(self):
        with self.lock:
            return {
                "recording": self.name,
                "scenario": scenario(self.name) if self.name else None,
                "windows": len(self.predicted),
                "position": self.position,
                "playing": self.playing,
                "speed": self.speed,
                "predicted": self.predicted,
            }

    def score(self, position):
        """Score one window and return the message for the page."""
        started = time.perf_counter()
        scores = model.predict(self.matrix[position])[0]
        elapsed = (time.perf_counter() - started) * 1000
        winner = int(scores.argmax())
        self.predicted[position] = winner
        self.timings[position] = elapsed
        end = self.features.index[position]
        window = self.minute.reindex(
            [end - np.timedelta64(offset, "m") for offset in range(LOOKBACK - 1, -1, -1)]
        )
        self.sequence += 1
        self.latest = {
            "id": self.sequence,
            "position": position,
            "start": window.index[0].isoformat(),
            "end": (end + np.timedelta64(1, "m")).isoformat(),
            "class": winner,
            "label": LABELS[winner],
            "scores": [round(float(score), 4) for score in scores],
            "inference_ms": round(elapsed, 2),
            "traces": {
                channel: [None if np.isnan(value) else round(float(value), 2) for value in window[channel]]
                for channel in CHANNELS
            },
        }
        return self.latest

    def step(self):
        with self.lock:
            if self.features is None or self.position >= len(self.features):
                self.playing = False
                return None
            previous = self.predicted[self.position - 1] if self.position else None
            message = self.score(self.position)
            # A fault block is a run of consecutive windows with the same fault class.
            # Replay stops once, on the first window of each block.
            message["onset"] = message["class"] != 0 and message["class"] != previous
            self.position += 1
            if message["onset"] or self.position >= len(self.features):
                self.playing = False
            message["playing"] = self.playing
            return message

    def block(self, position):
        """Describe the run of same-class windows around a scored position."""
        with self.lock:
            scored = self.features is not None and 0 <= position < len(self.predicted)
            if not scored or self.predicted[position] is None:
                return None
            winner = self.predicted[position]
            first = last = position
            while first > 0 and self.predicted[first - 1] == winner:
                first -= 1
            while last + 1 < len(self.predicted) and self.predicted[last + 1] == winner:
                last += 1
            start = self.features.index[first] - np.timedelta64(LOOKBACK - 1, "m")
            end = self.features.index[last]
            readings = self.minute.loc[start:end, CHANNELS]
            minutes = -(-len(readings) // MAX_READINGS)  # minutes summarized by each reading
            if minutes > 1:
                times = readings.index[::minutes]
                readings = readings.groupby(np.arange(len(readings)) // minutes).median()
                readings.index = times
            self.sequence += 1
            return {
                "id": self.sequence,
                "recording": self.name,
                "first": first,
                "last": last,
                "class": winner,
                # Exactly what is sent to Nemotron for a fault block.
                "edge_ms": round(float(np.median([self.timings[i] for i in range(first, last + 1)])), 2),
                "sent": {
                    "label": LABELS[winner],
                    "start": start.isoformat(),
                    "end": (end + np.timedelta64(1, "m")).isoformat(),
                    "windows_in_block": last - first + 1,
                    "minutes_per_reading": minutes,
                    "times": [stamp.strftime("%H:%M") for stamp in readings.index],
                    "traces": {
                        channel: [None if np.isnan(value) else round(float(value), 2) for value in readings[channel]]
                        for channel in CHANNELS
                    },
                },
            }


player = Player()
ui = WebUI()


def show_on_matrix(winner):
    """Show the predicted class on the LED matrix. The app still works if the sketch is absent."""
    if winner == player.shown:
        return
    player.shown = winner
    try:
        Bridge.notify("show_class", winner)
    except Exception as error:  # the bridge is optional for the web demo
        print(f"LED matrix update skipped: {error}")


def publish(message):
    if message:
        show_on_matrix(message["class"])
        ui.send_message("window", message)
        if message["onset"]:
            show_block(message["position"], explain=False)


def show_block(position, explain, provider="nemotron"):
    """Send a block's details to the page. Request the selected provider when a person clicks a fault block."""
    block = player.block(position)
    if block:
        block["provider"] = provider
        block["requested"] = explain and block["class"] != 0
        ui.send_message("block", block)
        if block["requested"]:
            threading.Thread(target=explain_with_provider, args=(block, provider), daemon=True).start()


def send_state(client=None):
    ui.send_message("state", player.describe(), client)


def on_hello(client, data):
    ui.send_message("setup", {
        "labels": LABELS,
        "channels": CHANNELS,
        "window_minutes": LOOKBACK,
        "speeds": SPEEDS,
        "model": {"name": MODEL, "trees": model.num_trees, "features": model.num_features},
        "recordings": [{"id": name, "scenario": scenario(name)} for name in RECORDINGS],
    }, client)
    send_state(client)


def on_select(client, data):
    name = (data or {}).get("recording")
    ui.send_message("loading", {"recording": name})
    try:
        player.load(name)
    except Exception as error:
        ui.send_message("problem", {"message": f"Could not load the recording: {error}"})
        return
    send_state()
    publish(player.step())


def on_play(client, data):
    with player.lock:
        if player.features is None:
            return
        if player.position >= len(player.features):
            player.position = 0
            player.predicted = [None] * len(player.features)
        player.playing = bool((data or {}).get("playing", True))
    send_state()


def on_step(client, data):
    with player.lock:
        player.playing = False
    publish(player.step())
    send_state()


def on_speed(client, data):
    speed = (data or {}).get("speed")
    if speed in SPEEDS:
        player.speed = speed
        send_state()


def on_seek(client, data):
    with player.lock:
        if player.features is None:
            return
        position = int((data or {}).get("position", 0))
        player.playing = False
        player.position = min(max(position, 0), len(player.features) - 1)
    publish(player.step())
    send_state()


def on_block(client, data):
    with player.lock:
        player.playing = False
    send_state()
    provider = (data or {}).get("provider", "nemotron")
    if provider not in PROVIDERS:
        ui.send_message("problem", {"message": "Choose a supported explanation model."}, client)
        return
    show_block(int((data or {}).get("position", -1)), explain=True, provider=provider)


def explain_with_provider(result, provider):
    cache_key = (provider, result["recording"], result["first"], result["last"])
    known = player.explanations.get(cache_key)
    if known:
        ui.send_message("explanation", {"id": result["id"], "provider": provider, **known, "cached": True})
        return
    endpoint_lock = endpoint_locks[provider]
    if not endpoint_lock.acquire(blocking=False):
        ui.send_message("explanation", {
            "id": result["id"], "provider": provider, "error": "This provider is still processing the previous block. Click this block again to retry.",
        })
        return
    try:
        request_explanation(result, provider, cache_key)
    finally:
        endpoint_lock.release()


PAPER_FAULTS = {
    1: ("BaselineTestA", "The LT freezer door was opened for 5%, 10%, or 15% of the test time."),
    2: ("BaselineTestB", "The researchers changed defrost timing to build mild, moderate, or severe ice on the LT evaporator."),
    3: ("BaselineTestC", "The LT freezer evaporator expansion valve was manually moved to partially or fully closed positions."),
    4: ("BaselineTestD", "The researchers sequentially disabled three of four MT chilled-case evaporator fans to test 25%, 50%, and 75% fan loss."),
    5: ("BaselineTestE", "The researchers obstructed the shared gas cooler inlet air path at 25%, 50%, and 75% blockage."),
    6: ("BaselineTestA", "The researchers obstructed the MT evaporator return-air path at 25%, 50%, and 75% blockage."),
}
PAPER_ALTERNATIVES = {1: 2, 2: 3, 3: 2, 4: 6, 5: 6, 6: 4}


def paper_reference(class_id):
    return {
        "source": "Sun et al. (2021), Scientific Data, doi:10.1038/s41597-021-00927-6",
        "Figure 1": (
            "The laboratory CO2 system has a low-temperature freezer case (LT), a medium-temperature "
            "open chilled case (MT), and a shared air-cooled gas cooler. "
            "T-LTcase-Ret and T-LTcase-Sup measure freezer return and supply air. "
            "T-MTCase-Ret and T-MTCase-Sup measure chilled-case return and supply air. "
            "T-GC-Fan2-In and T-GC-Fan2-Out measure air at gas cooler fan 2."
        ),
        "Tables 3 and 4": [
            {"class": LABELS[index], "experimental_method": PAPER_FAULTS[index][1],
             "matched_baseline_file": PAPER_FAULTS[index][0] + ".csv"}
            for index in (class_id, PAPER_ALTERNATIVES[class_id])
        ],
        "Figures 4 and 5": (
            "In the reported door-opening example, freezer return air warmed immediately while "
            "supply air initially stayed near its setpoint. Both air temperatures rose during defrost. "
            "This observation is specific to the reported door test."
        ),
    }


def request_explanation(result, provider, cache_key):
    response = {"id": result["id"], "provider": provider}
    base, endpoint_model, key = endpoint_settings(provider)
    base = base.rstrip("/")
    if not base.startswith("https://") or not endpoint_model or (provider == "gemini" and not key):
        response["error"] = "This provider is not configured on this board."
    else:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        body = {
            "model": endpoint_model,
            "messages": [
                {"role": "system", "content": (
                    "Review a refrigeration replay alert from the Sun et al. CO2 test rig. "
                    "The alert is a block: a run of consecutive ten-minute windows that the edge "
                    "classifier gave the same fault class. The inputs are consecutive air temperature "
                    "medians in Fahrenheit, each covering minutes_per_reading minutes and listed "
                    "with its start time, "
                    "for the freezer coil, chilled-case coil and shared gas cooler fan 2. "
                    "For the coils compare return minus supply; for the gas cooler compare outlet "
                    "minus inlet. The expansion valve fault class refers to the freezer valve. "
                    "Use paper_reference and cite the supplied figure or table when stating study facts. "
                    "First explain how the predicted fault and comparison fault were induced. Then cite "
                    "two timestamped readings from sensor_block and say which hypothesis, if any, they "
                    "support. A timestamp denotes the start of an aggregated reading. Avoid inferring "
                    "fault onset or severity from this block. Matched baseline filenames identify the "
                    "study comparisons; no baseline readings are supplied. Air temperatures alone cannot "
                    "establish fan speed, airflow, valve position, pressure, or superheat. Suggest one "
                    "operator check that would distinguish the hypotheses. For fan failure versus "
                    "airflow blockage, compare fan operation and return-path obstruction."
                )},
                {"role": "user", "content": json.dumps({
                    "paper_reference": paper_reference(result["class"]),
                    "sensor_block": result["sent"],
                })},
            ],
        }
        sent = result["sent"]
        print(f"{provider} request: {sent['label']}, {sent['start']} to {sent['end']}")
        try:
            request = Request(base + "/chat/completions", json.dumps(body).encode(), headers)
            started = time.perf_counter()
            with urlopen(request, timeout=60) as remote:
                response["text"] = json.load(remote)["choices"][0]["message"]["content"]
            if not response["text"]:
                raise ValueError("Empty explanation")
            response["response_ms"] = round((time.perf_counter() - started) * 1000, 2)
            if result["recording"] == player.name:
                player.explanations[cache_key] = {
                    "text": response["text"], "response_ms": response["response_ms"],
                }
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            response["error"] = "The provider could not return an explanation. The edge result is still available."
    ui.send_message("explanation", response)


ui.on_message("hello", on_hello)
ui.on_message("select", on_select)
ui.on_message("play", on_play)
ui.on_message("step", on_step)
ui.on_message("speed", on_speed)
ui.on_message("seek", on_seek)
ui.on_message("block", on_block)
ui.expose_api("GET", "/status", lambda: {key: value for key, value in player.describe().items() if key != "predicted"})


def replay():
    while True:
        if player.playing:
            try:
                publish(player.step())
            except Exception as error:
                player.playing = False
                ui.send_message("problem", {"message": f"Replay stopped: {error}"})
            if not player.playing:
                send_state()
            time.sleep(1 / player.speed)
        else:
            time.sleep(0.1)


threading.Thread(target=replay, daemon=True).start()
print(f"Fault model ready: {model.num_trees} trees, {model.num_features} features, {len(RECORDINGS)} recordings")
App.run()
