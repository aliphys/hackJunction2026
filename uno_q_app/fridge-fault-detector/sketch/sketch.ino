// Shows the fault model's current prediction on the UNO Q LED matrix.
// The Linux side calls show_class(n): 0 is Baseline (a tick), 1 to 6 are the
// fault classes (shown as F1 to F6). Any other value clears the matrix.

#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

#include "frames.h"

Arduino_LED_Matrix matrix;

void show_class(int index) {
  if (index < 0 || index >= FRAME_COUNT) {
    matrix.clear();
    return;
  }
  matrix.loadFrame(FRAMES[index]);
}

void setup() {
  matrix.begin();
  matrix.clear();

  Bridge.begin();
  Bridge.provide("show_class", show_class);
}

void loop() {
  delay(100);
}
