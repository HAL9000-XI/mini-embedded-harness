#include <Arduino.h>

// External LED: GPIO18 -> 220-330 ohm resistor -> LED anode.
// LED cathode -> GND.
constexpr uint8_t LED_PIN = 18;
constexpr uint32_t BLINK_INTERVAL_MS = 500;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(115200);
  delay(1000);
  Serial.println("HARNESS:BOOT");
}

void loop() {
  static bool led_on = false;
  static uint32_t last_toggle = 0;
  const uint32_t now = millis();

  if (now - last_toggle >= BLINK_INTERVAL_MS) {
    last_toggle = now;
    led_on = !led_on;
    digitalWrite(LED_PIN, led_on ? HIGH : LOW);

    Serial.printf("HARNESS:LED=%d;T=%lu\n",
                  led_on ? 1 : 0,
                  static_cast<unsigned long>(now));
  }
}
