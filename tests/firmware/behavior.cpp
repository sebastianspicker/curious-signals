#include <cassert>
#include <cmath>
#include <string>
#include <limits>
#include SKETCH_SOURCE

void reset() {
  imuOk = htsOk = baroOk = apdsOk = true;
  IMU = Imu{}; HTS = TemperatureHumidity{}; BARO = Barometer{}; APDS = Light{};
  analogReads = blePolls = 0;
  clockMs = startMs = lastSendMs = 0;
  mode = Mode::kAcceleration;
  centralPresent = true;
  connectionPolls = 1;
  dataCharacteristic.subscription = true;
  dataCharacteristic.writes.clear();
  configCharacteristic.writes.clear();
  configCharacteristic.pending = false;
}

// Runs first: reset() would otherwise hide the sketch's own defaults.
void checkSetup() {
  setup();
  assert(BLE.deviceName == expectedDeviceName);
  assert(BLE.localName == expectedDeviceName);
  assert(BLE.services.size() == 1 && BLE.services[0] == &phyphoxService);
  assert(phyphoxService.uuid == expectedServiceUuid);
  assert(BLE.advertiseCalls == 1);
  assert(phyphoxService.characteristics.size() == 2);
  assert(phyphoxService.characteristics[0] == &dataCharacteristic);
  assert(phyphoxService.characteristics[1] == &configCharacteristic);
  assert(dataCharacteristic.addedToService && configCharacteristic.addedToService);
  assert(dataCharacteristic.uuid == expectedDataUuid);
  assert(dataCharacteristic.properties == expectedDataProperties);
  assert(dataCharacteristic.storageSize == expectedDataSize);
  assert(configCharacteristic.uuid == expectedConfigUuid);
  assert(configCharacteristic.properties == expectedConfigProperties);
  // Config storage is wire size + 1: the oversized-write reject sentinel.
  assert(configCharacteristic.storageSize == expectedConfigSize + 1);
  assert(static_cast<int>(mode) == expectedDefaultMode);
  assert(configCharacteristic.writes.size() == 1);
  uint8_t encoded[4] = {};
  writeFloat32LE(encoded, sizeof(encoded), 0, static_cast<float>(expectedDefaultMode));
  assert(configCharacteristic.writes.back().size() == static_cast<size_t>(expectedConfigSize));
  assert(configCharacteristic.writes.back() == std::vector<uint8_t>(encoded, encoded + 4));
  assert(kSendPeriodMs == static_cast<unsigned long>(expectedSendPeriodMs));
}

void checkModes() {
  for (int raw : expectedActiveModes) {
    setModeFromConfig(static_cast<float>(raw));
    assert(static_cast<int>(mode) == raw);
  }
  for (int raw : expectedReservedModes) {
    mode = Mode::kPressure;
    setModeFromConfig(static_cast<float>(raw));
    assert(mode == Mode::kPressure);
  }
  for (float value : {0.0f, -1.0f, 0.499f, 6.5f, 7.0f, 8.0f, 9.5f,
                      std::nextafterf(expectedSelectionMinimum, 0.0f),
                      expectedSelectionMaximumExclusive,
                      std::nextafterf(expectedSelectionMaximumExclusive, 100.0f),
                      std::numeric_limits<float>::infinity(),
                      -std::numeric_limits<float>::infinity(),
                      std::numeric_limits<float>::quiet_NaN()}) {
    mode = Mode::kPressure;
    setModeFromConfig(value);
    assert(mode == Mode::kPressure);
  }
  mode = Mode::kPressure;
  setModeFromConfig(expectedSelectionMinimum);
  assert(static_cast<int>(mode) == expectedActiveModes[0]);
  mode = Mode::kPressure;
  setModeFromConfig(std::nextafterf(expectedSelectionMaximumExclusive, 0.0f));
  assert(static_cast<int>(mode) == expectedActiveModes[std::size(expectedActiveModes) - 1]);
  for (auto example : {std::pair<float, int>{0.5f, 1}, {1.499f, 1}, {1.5f, 2},
                       {8.5f, 9}, {9.499f, 9}}) {
    setModeFromConfig(example.first);
    assert(static_cast<int>(mode) == example.second);
  }
}

void checkCodec() {
  uint8_t buffer[8] = {};
  writeFloat32LE(buffer, sizeof(buffer), 0, 1.0f);
  writeFloat32LE(buffer, sizeof(buffer), 4, -2.5f);
  const uint8_t expected[] = {0, 0, 0x80, 0x3f, 0, 0, 0x20, 0xc0};
  assert(std::equal(buffer, buffer + 8, expected));
  assert(readFloat32LE(buffer, 4) == 1.0f);
  assert(readFloat32LE(buffer + 4, 4) == -2.5f);
  writeFloat32LE(buffer, sizeof(buffer), -1, 7.0f);
  writeFloat32LE(buffer, sizeof(buffer), 5, 7.0f);
  writeFloat32LE(nullptr, sizeof(buffer), 0, 7.0f);
  assert(std::equal(buffer, buffer + 8, expected));
  assert(readFloat32LE(buffer, 3) == 0.0f);
  assert(readFloat32LE(nullptr, 4) == 0.0f);
}

void checkSensors() {
  const float expected[][4] = {
    {3, 4, 0, 5}, {0, -5, 12, 13}, {-8, 0, 15, 17}, {101.325f, NAN, NAN, NAN},
    {-12.5f, 45, NAN, NAN}, {44, 11, 22, 33}, {100, 200, 300, NAN}
  };
  int index = 0;
  for (int raw : expectedActiveModes) {
    reset();
    mode = static_cast<Mode>(raw);
    float channels[4] = {};
    readChannels(channels[0], channels[1], channels[2], channels[3]);
    for (int i = 0; i < 4; ++i) {
      assert(std::isnan(expected[index][i]) ? std::isnan(channels[i])
                                          : channels[i] == expected[index][i]);
    }
    assert(IMU.accelerationReads == (raw == 1));
    assert(IMU.gyroscopeReads == (raw == 2));
    assert(IMU.magneticReads == (raw == 3));
    assert(BARO.reads == (raw == 4));
    assert(HTS.temperatureReads == (raw == 5) && HTS.humidityReads == (raw == 5));
    assert(APDS.reads == (raw == 6));
    assert(analogReads == (raw == 9 ? 3 : 0));
    ++index;
  }
  for (int raw : {1, 2, 3, 4, 5, 6}) {
    reset(); mode = static_cast<Mode>(raw);
    imuOk = htsOk = baroOk = apdsOk = false;
    float channels[4] = {1, 2, 3, 4};
    readChannels(channels[0], channels[1], channels[2], channels[3]);
    for (float value : channels) { assert(std::isnan(value)); }
    assert(IMU.accelerationReads + IMU.gyroscopeReads + IMU.magneticReads + BARO.reads
           + HTS.temperatureReads + HTS.humidityReads + APDS.reads == 0);
  }
  for (int raw : {1, 2, 3, 6}) {
    reset(); mode = static_cast<Mode>(raw);
    IMU.available = APDS.available = false;
    float channels[4] = {1, 2, 3, 4};
    readChannels(channels[0], channels[1], channels[2], channels[3]);
    for (float value : channels) { assert(std::isnan(value)); }
  }
}

void checkConfigWrites() {
  reset();
  const uint8_t modeFive[] = {0, 0, 0xa0, 0x40};
  configCharacteristic.incoming.assign(modeFive, modeFive + 4);
  configCharacteristic.pending = true;
  pollConfigCharacteristic();
  assert(mode == Mode::kTemperatureHumidity);
  assert(configCharacteristic.writes.back() == std::vector<uint8_t>(modeFive, modeFive + 4));
  for (int length : {0, 1, 2, 3}) {
    configCharacteristic.incoming.assign(length, 0);
    configCharacteristic.pending = true;
    pollConfigCharacteristic();
    assert(mode == Mode::kTemperatureHumidity);
  }
  for (int length : {5, 6, 20}) {
    configCharacteristic.incoming = {0, 0, 0x10, 0x41};  // Valid mode 9 prefix.
    configCharacteristic.incoming.resize(length, 0xaa);
    configCharacteristic.pending = true;
    pollConfigCharacteristic();
    assert(mode == Mode::kTemperatureHumidity);
    assert(configCharacteristic.writes.back() == std::vector<uint8_t>(modeFive, modeFive + 4));
  }
  for (float invalid : {7.0f, NAN, 0.0f}) {
    configCharacteristic.incoming.resize(4);
    writeFloat32LE(configCharacteristic.incoming.data(), 4, 0, invalid);
    configCharacteristic.pending = true;
    pollConfigCharacteristic();
    assert(mode == Mode::kTemperatureHumidity);
    assert(configCharacteristic.writes.back() == std::vector<uint8_t>(modeFive, modeFive + 4));
  }
}

void tick(uint32_t time) {
  clockMs = time;
  connectionPolls = 1;
  loop();
}

void checkTimingAndSubscription() {
  reset();
  tick(49); assert(dataCharacteristic.writes.empty());
  tick(50); assert(dataCharacteristic.writes.size() == 1);
  tick(99); assert(dataCharacteristic.writes.size() == 1);
  tick(100); assert(dataCharacteristic.writes.size() == 2);
  assert(dataCharacteristic.writes.back().size() == static_cast<size_t>(expectedDataSize));
  const auto& packet = dataCharacteristic.writes.back();
  const float expected[] = {0.1f, 3, 4, 0, 5};
  assert(std::size(expected) == std::size(expectedDataOffsets));
  assert(packet.size() == static_cast<size_t>(expectedDataSize));
  for (size_t i = 0; i < std::size(expected); ++i) {
    assert(readFloat32LE(packet.data() + expectedDataOffsets[i], 4) == expected[i]);
  }

  reset();
  dataCharacteristic.subscription = false;
  configCharacteristic.incoming = {0, 0, 0x80, 0x40};  // Mode 4, even before subscription.
  configCharacteristic.pending = true;
  for (uint32_t time = 50; time <= 1000; time += 50) { tick(time); }
  assert(mode == Mode::kPressure && !configCharacteristic.writes.empty());
  assert(dataCharacteristic.writes.empty() && BARO.reads == 0);
  assert(blePolls == 40 && lastSendMs == 1000);
  dataCharacteristic.subscription = true;
  tick(1049); assert(dataCharacteristic.writes.empty());
  tick(1050); assert(dataCharacteristic.writes.size() == 1 && BARO.reads == 1);
  dataCharacteristic.subscription = false;
  tick(1100); assert(dataCharacteristic.writes.size() == 1 && BARO.reads == 1);

  reset();
  startMs = lastSendMs = UINT32_MAX - 24;
  tick(24); assert(dataCharacteristic.writes.empty());
  tick(25); assert(dataCharacteristic.writes.size() == 1);
  assert(readFloat32LE(dataCharacteristic.writes.back().data(), 4) == 0.05f);
  tick(74); assert(dataCharacteristic.writes.size() == 1);
  tick(75); assert(dataCharacteristic.writes.size() == 2);
  centralPresent = false;
  tick(200); assert(dataCharacteristic.writes.size() == 2);
}

int main() {
  checkSetup(); reset(); checkModes(); checkCodec(); checkSensors(); checkConfigWrites();
  checkTimingAndSubscription();
}
