# UNO Q demo

Run `fridge-fault-detector` on the UNO Q in Arduino App Lab. In its web view, click **Try normal operation** and then **Try freezer door open**. The board scores the first ten-minute window, reports its scoring time, and updates the LED matrix through the sketch. The check mark means baseline and F1â€“F6 identify the fault classes.

Baseline windows exit on the board. Fault windows pause replay and automatically send the same ten-minute temperature medians to Nemotron after the edge result is displayed. Configure OPENAI_BASE_URL (including /v1), OPENAI_MODEL, and OPENAI_API_KEY through the board app environment or a .env beside app.yaml. During local development the repository-root .env also works. Keep the key private.
