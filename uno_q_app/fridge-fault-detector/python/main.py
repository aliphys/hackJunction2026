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
endpoint_lock = threading.Lock()


def endpoint_settings():
    keys = ("OPENAI_BASE_URL", "OPENAI_MODEL", "OPENAI_API_KEY")
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
        self.shown = None
        self.latest = None
        self.sequence = 0

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
            self.latest = None

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
            message = self.score(self.position)
            self.position += 1
            if message["class"] != 0 or self.position >= len(self.features):
                self.playing = False
            message["playing"] = self.playing
            return message


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
        if message["class"] != 0:
            threading.Thread(target=explain_fault, args=(message,), daemon=True).start()


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


def explain_fault(result):
    if not endpoint_lock.acquire(blocking=False):
        ui.send_message("explanation", {
            "id": result["id"], "error": "Nemotron is still processing the previous window. Select this window again to retry.",
        })
        return
    try:
        request_explanation(result)
    finally:
        endpoint_lock.release()


def request_explanation(result):
    response = {"id": result["id"]}
    base, endpoint_model, key = endpoint_settings()
    base = base.rstrip("/")
    if not base.startswith("https://") or not endpoint_model:
        response["error"] = "Nemotron is not configured on this board."
    else:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        body = {
            "model": endpoint_model,
            "messages": [
                {"role": "system", "content": (
                    "Review a refrigeration replay alert from the Sun et al. CO2 test rig. "
                    "The inputs are ten consecutive one-minute air temperature medians in Fahrenheit "
                    "for the freezer coil, chilled-case coil and shared gas cooler fan 2. "
                    "For the coils compare return minus supply; for the gas cooler compare outlet "
                    "minus inlet. The expansion valve fault class refers to the freezer valve. "
                    "Give a brief assessment, cite two readings as evidence, and give one operator "
                    "check. Treat the predicted class as a hypothesis."
                )},
                {"role": "user", "content": json.dumps({
                    key: result[key] for key in ("start", "end", "label", "traces")
                })},
            ],
        }
        try:
            request = Request(base + "/chat/completions", json.dumps(body).encode(), headers)
            with urlopen(request, timeout=30) as remote:
                response["text"] = json.load(remote)["choices"][0]["message"]["content"]
            if not response["text"]:
                raise ValueError("Empty explanation")
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            response["error"] = "Nemotron could not return an explanation. The edge result is still available."
    ui.send_message("explanation", response)


ui.on_message("hello", on_hello)
ui.on_message("select", on_select)
ui.on_message("play", on_play)
ui.on_message("step", on_step)
ui.on_message("speed", on_speed)
ui.on_message("seek", on_seek)
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
