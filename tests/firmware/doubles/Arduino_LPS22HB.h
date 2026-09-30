#pragma once
struct Barometer {
  int reads = 0;
  bool begin() { return true; }
  float readPressure() { ++reads; return 101.325f; }
};
inline Barometer BARO;
