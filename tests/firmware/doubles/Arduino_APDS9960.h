#pragma once
struct Light {
  bool available = true;
  int reads = 0;
  bool begin() { return true; }
  bool colorAvailable() { return available; }
  void readColor(int& r, int& g, int& b, int& c) {
    ++reads; r = 11; g = 22; b = 33; c = 44;
  }
};
inline Light APDS;
