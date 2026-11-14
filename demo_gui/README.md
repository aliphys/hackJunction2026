# Local refrigeration demo

From the project root, set up the virtual environment once:

```powershell
uv venv demo_gui/.venv
uv pip install --python demo_gui/.venv/Scripts/python.exe -r demo_gui/requirements.txt
```

Start the demo using its virtual environment:

```powershell
& .\demo_gui\.venv\Scripts\python.exe .\demo_gui\app.py
```

Open http://127.0.0.1:8765, select a recording and a ten-minute interval, then click **Analyze sample**. The demo loads the saved seven-class LightGBM model from models/demo_fault_10m. A Baseline prediction stays local. Any of the six fault predictions triggers a Nemotron request with the chart and sensor table for the exact selected interval. The endpoint uses the project-root .env settings.
