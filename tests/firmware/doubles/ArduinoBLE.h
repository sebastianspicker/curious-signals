#pragma once

// Host-only boundary doubles. The tests include and execute the actual sketch.
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

inline uint32_t clockMs = 0;
inline bool centralPresent = false;
inline int connectionPolls = 0;
inline int blePolls = 0;
inline int analogReads = 0;
constexpr int A0 = 0, A1 = 1, A2 = 2;
constexpr int BLENotify = 1, BLERead = 2, BLEWrite = 4;
inline unsigned long millis() { return clockMs; }
inline void delay(unsigned long) {}
inline int analogRead(int pin) { ++analogReads; return 100 * (pin + 1); }

struct BLECharacteristic {
  std::string uuid;
  int properties;
  int storageSize;
  bool addedToService = false;
  bool subscription = false;
  bool pending = false;
  std::vector<uint8_t> incoming;
  std::vector<std::vector<uint8_t>> writes;
  BLECharacteristic(const char* id, int props, int size)
      : uuid(id), properties(props), storageSize(size) {}
  // ArduinoBLE 1.5.0 truncates an incoming ATT write to private storage first.
  int valueLength() const {
    return static_cast<int>(std::min(incoming.size(), static_cast<size_t>(storageSize)));
  }
  bool subscribed() const { return subscription; }
  bool written() { bool result = pending; pending = false; return result; }
  int readValue(uint8_t* buffer, int capacity) {
    const auto length = static_cast<size_t>(std::min(valueLength(), capacity));
    std::copy_n(incoming.begin(), length, buffer);
    return static_cast<int>(length);
  }
  void writeValue(const uint8_t* bytes, size_t length) {
    writes.emplace_back(bytes, bytes + length);
  }
};

struct BLEService {
  std::string uuid;
  std::vector<BLECharacteristic*> characteristics;
  explicit BLEService(const char* id) : uuid(id) {}
  void addCharacteristic(BLECharacteristic& characteristic) {
    characteristic.addedToService = true;
    characteristics.push_back(&characteristic);
  }
};
struct BLEDevice {
  explicit operator bool() const { return centralPresent; }
  bool connected() { return connectionPolls-- > 0; }
};
struct BLEFacade {
  bool begin() { return true; }
  void poll() { ++blePolls; }
  BLEDevice central() { return {}; }
  std::string deviceName, localName;
  std::vector<BLEService*> services;
  int advertiseCalls = 0;
  void setDeviceName(const char* name) { deviceName = name; }
  void setLocalName(const char* name) { localName = name; }
  void addService(BLEService& service) { services.push_back(&service); }
  void advertise() { ++advertiseCalls; }
};
inline BLEFacade BLE;
