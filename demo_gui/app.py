import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from inference import ROOT, analyze_waveform

DATA = ROOT / "data"
PAGE = (Path(__file__).with_name("index.html")).read_text(encoding="utf-8")

class DemoHandler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def reply_json(self, status, data):
        self.reply(status, json.dumps(data, allow_nan=False).encode(), "application/json")

    def do_GET(self):
        if self.path == "/":
            self.reply(200, PAGE.encode(), "text/html")
        elif self.path == "/waveforms":
            self.reply_json(200, sorted(path.name for path in DATA.glob("*.csv")))
        else:
            self.reply_json(404, {"error": "Page unavailable"})

    def do_POST(self):
        url = urlsplit(self.path)
        if url.path != "/infer":
            self.reply_json(404, {"error": "Page unavailable"})
            return
        if self.headers.get("Origin") != f"http://{self.headers.get('Host')}":
            self.reply_json(403, {"error": "Open the demo page directly to run inference."})
            return
        name = parse_qs(url.query).get("waveform", [""])[0]
        try:
            start = int(parse_qs(url.query).get("start", ["0"])[0])
            if start < 0:
                raise ValueError
        except ValueError:
            self.reply_json(400, {"error": "Enter a nonnegative starting minute."})
            return
        choices = {path.name: path for path in DATA.glob("*.csv")}
        if name not in choices:
            self.reply_json(400, {"error": "Select a recorded waveform."})
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        def emit(stage, data):
            self.wfile.write((json.dumps({"stage": stage, **data}, allow_nan=False) + "\n").encode())
            self.wfile.flush()

        try:
            result = analyze_waveform(
                choices[name], on_local=lambda data: emit("local", data), start_minute=start
            )
            if result["fault"]:
                emit("analysis", {"analysis": result["analysis"]})
            else:
                emit("local", result)
        except (BrokenPipeError, ConnectionResetError):
            return
        except ValueError as error:
            emit("error", {"error": str(error)})
        except OSError:
            emit("error", {"error": "Could not score this recording. Check the CSV and model files."})


if __name__ == "__main__":
    url = "http://127.0.0.1:8765"
    with HTTPServer(("127.0.0.1", 8765), DemoHandler) as server:
        print(f"Open {url}", flush=True)
        server.serve_forever()


