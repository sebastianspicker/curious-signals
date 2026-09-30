#pragma once
struct Imu {
  bool available = true;
  int accelerationReads = 0, gyroscopeReads = 0, magneticReads = 0;
  bool begin() { return true; }
  bool accelerationAvailable() { return available; }
  bool gyroscopeAvailable() { return available; }
  bool magneticFieldAvailable() { return available; }
  void readAcceleration(float& x, float& y, float& z) {
    ++accelerationReads; x = 3; y = 4; z = 0;
  }
  void readGyroscope(float& x, float& y, float& z) {
    ++gyroscopeReads; x = 0; y = -5; z = 12;
  }
  void readMagneticField(float& x, float& y, float& z) {
    ++magneticReads; x = -8; y = 0; z = 15;
  }
};
inline Imu IMU;
