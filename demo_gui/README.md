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

Open http://127.0.0.1:8765, select a CSV recording, and click **Run inference**. The page plots one-minute temperature medians and shows the alert counts. The dashed line marks the first alert.

The demo loads the existing binary and fault models from `models/`. A binary alert triggers one analysis request for the first alert in the recording, sending a waveform image and up to 20 minutes of matching sensor data around the alert. Follow-up readings are included for this retrospective replay. Expand the evidence panel to see the image supplied to Nemotron. It uses the project-root `.env` settings. Endpoint errors appear alongside the local classifier result. The CSV recordings are from the source dataset used by the training notebooks.

