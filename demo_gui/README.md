# Local refrigeration demo

From the project root:

```powershell
python -m pip install -r demo_gui/requirements.txt
python demo_gui/app.py
```

Open http://127.0.0.1:8765, select a CSV recording, and click **Run inference**. The page plots one-minute temperature medians and shows the alert counts. The dashed line marks the first alert.

The demo loads the existing binary and fault models from `models/`. A binary alert triggers one analysis request for the first alert in the recording, using up to ten minutes of readings available at that point. It uses the project-root `.env` settings. Endpoint errors appear alongside the local classifier result. The CSV recordings are from the source dataset used by the training notebooks.
