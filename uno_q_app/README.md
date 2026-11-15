# UNO Q demo

Open [fridge-fault-detector](fridge-fault-detector/) in Arduino App Lab and run it on the UNO Q. In **Live monitoring**, choose **Try normal operation** or **Try freezer door open**. The board scores the first ten-minute window, reports its scoring time, and updates the LED matrix. The check mark means baseline and F1–F6 identify the fault classes.

Baseline windows exit on the board. Replay pauses at the start of a fault block. Pick an explanation model in **Incident review**, then click a scored fault block on the live timeline to request analysis from that provider.

## Explanation providers

| Provider | Settings |
| --- | --- |
| Nemotron | `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_API_KEY` |
| Gemini | `AI_STUDIO_BASE_URL`, `AI_STUDIO_MODEL`, `AI_STUDIO_API_KEY` |

Use the board app's environment or a private `.env` next to `app.yaml`. For local development, the repository-root `.env` also works. The base URLs should include their API prefix. LightGBM classification runs independently of either provider.
