#pragma once
struct TemperatureHumidity {
  int temperatureReads = 0, humidityReads = 0;
  bool begin() { return true; }
  float readTemperature() { ++temperatureReads; return -12.5f; }
  float readHumidity() { ++humidityReads; return 45.0f; }
};
inline TemperatureHumidity HTS;
