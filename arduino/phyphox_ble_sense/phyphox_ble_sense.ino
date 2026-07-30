#include <ArduinoBLE.h>
#include <algorithm>
#include <cmath>

#include <Arduino_APDS9960.h>
#include <Arduino_HTS221.h>
#include <Arduino_LPS22HB.h>
#include <Arduino_LSM9DS1.h>

namespace {

constexpr const char* kPhyphoxServiceUuid = "cddf0001-30f7-4671-8b43-5e40ba53514a";
constexpr const char* kDataCharUuid = "cddf1002-30f7-4671-8b43-5e40ba53514a";
constexpr const char* kConfigCharUuid = "cddf1003-30f7-4671-8b43-5e40ba53514a";

// These mode IDs match the <config> values in experiments/*.phyphox.
enum class Mode : int {
  kAcceleration = 1,
  kGyroscope = 2,
  kMagnetometer = 3,
  kPressure = 4,
  kTemperatureHumidity = 5,
  kLightRgb = 6,
  kAnalogInputs = 9,
};

constexpr Mode kSupportedModes[] = {
    Mode::kAcceleration,
    Mode::kGyroscope,
    Mode::kMagnetometer,
    Mode::kPressure,
    Mode::kTemperatureHumidity,
    Mode::kLightRgb,
    Mode::kAnalogInputs,
};

// Payload = 5× float32; BLE default MTU is often 20–23, so this fits one packet.
constexpr int kPayloadSizeBytes = 20;
constexpr unsigned long kSendPeriodMs = 50;

BLEService phyphoxService(kPhyphoxServiceUuid);
BLECharacteristic dataCharacteristic(kDataCharUuid, BLENotify, kPayloadSizeBytes);
BLECharacteristic configCharacteristic(kConfigCharUuid, BLERead | BLEWrite, 4);

// Sensor init success; readChannels only uses a sensor when its flag is true.
bool imuOk = false;
bool htsOk = false;
bool baroOk = false;
bool apdsOk = false;

unsigned long startMs = 0;
unsigned long lastSendMs = 0;

Mode mode = Mode::kAcceleration;

void writeFloat32LE(uint8_t* buf, size_t len, int offset, float value) {
  static_assert(sizeof(float) == 4, "Expected IEEE-754 float32");
  if (buf == nullptr || offset < 0 || (size_t)offset + 4 > len) {
    return;
  }
  uint32_t raw = 0;
  memcpy(&raw, &value, sizeof(raw));
  buf[offset + 0] = (uint8_t)(raw & 0xFFu);
  buf[offset + 1] = (uint8_t)((raw >> 8) & 0xFFu);
  buf[offset + 2] = (uint8_t)((raw >> 16) & 0xFFu);
  buf[offset + 3] = (uint8_t)((raw >> 24) & 0xFFu);
}

// Requires len >= 4; returns 0.0f if buf is null or len < 4 to avoid over-read.
float readFloat32LE(const uint8_t* buf, size_t len) {
  if (buf == nullptr || len < 4) {
    return 0.0f;
  }
  uint32_t raw = ((uint32_t)buf[0]) | ((uint32_t)buf[1] << 8) | ((uint32_t)buf[2] << 16) | ((uint32_t)buf[3] << 24);
  float value = 0.0f;
  memcpy(&value, &raw, sizeof(value));
  return value;
}

bool findSupportedMode(int raw, Mode& supportedMode) {
  const Mode requestedMode = (Mode)raw;
  const Mode* const end = kSupportedModes + (sizeof(kSupportedModes) / sizeof(kSupportedModes[0]));
  const Mode* const match = std::find(kSupportedModes, end, requestedMode);
  if (match == end) {
    return false;
  }
  supportedMode = *match;
  return true;
}

void setModeFromConfig(float configValue) {
  if (!std::isfinite(configValue) || configValue < 0.5f || configValue >= 9.5f) {
    return;
  }
  const int raw = (int)roundf(configValue);
  Mode supportedMode = mode;
  if (findSupportedMode(raw, supportedMode)) {
    mode = supportedMode;
  }
}

void writeActiveModeToConfigCharacteristic() {
  uint8_t configValue[4] = {0};
  writeFloat32LE(configValue, sizeof(configValue), 0, (float)(int)mode);
  configCharacteristic.writeValue(configValue, sizeof(configValue));
}

// Fills ch2..ch5 from x,y,z and sets ch5 = magnitude (for IMU modes).
void setChannelsFromXYZ(float x, float y, float z, float& ch2, float& ch3, float& ch4, float& ch5) {
  ch2 = x;
  ch3 = y;
  ch4 = z;
  ch5 = sqrtf(x * x + y * y + z * z);
}

void readAcceleration(float& ch2, float& ch3, float& ch4, float& ch5) {
  if (!imuOk || !IMU.accelerationAvailable()) {
    return;
  }
  float x = 0, y = 0, z = 0;
  IMU.readAcceleration(x, y, z);
  setChannelsFromXYZ(x, y, z, ch2, ch3, ch4, ch5);
}

void readGyroscope(float& ch2, float& ch3, float& ch4, float& ch5) {
  if (!imuOk || !IMU.gyroscopeAvailable()) {
    return;
  }
  float x = 0, y = 0, z = 0;
  IMU.readGyroscope(x, y, z);
  setChannelsFromXYZ(x, y, z, ch2, ch3, ch4, ch5);
}

void readMagnetometer(float& ch2, float& ch3, float& ch4, float& ch5) {
  if (!imuOk || !IMU.magneticFieldAvailable()) {
    return;
  }
  float x = 0, y = 0, z = 0;
  IMU.readMagneticField(x, y, z);
  setChannelsFromXYZ(x, y, z, ch2, ch3, ch4, ch5);
}

void readPressure(float& ch2) {
  if (baroOk) {
    // kPa (matches pressure_plot_v1-2.phyphox, which converts to hPa in analysis)
    ch2 = BARO.readPressure();
  }
}

void readTemperatureHumidity(float& ch2, float& ch3) {
  if (htsOk) {
    ch2 = HTS.readTemperature();
    ch3 = HTS.readHumidity();
  }
}

void readLightRgb(float& ch2, float& ch3, float& ch4, float& ch5) {
  if (!apdsOk || !APDS.colorAvailable()) {
    return;
  }
  int r = 0, g = 0, b = 0, c = 0;
  APDS.readColor(r, g, b, c);
  ch2 = (float)c;
  ch3 = (float)r;
  ch4 = (float)g;
  ch5 = (float)b;
}

void readAnalogInputs(float& ch2, float& ch3, float& ch4) {
  ch2 = (float)analogRead(A0);
  ch3 = (float)analogRead(A1);
  ch4 = (float)analogRead(A2);
}

void readChannels(float& ch2, float& ch3, float& ch4, float& ch5) {
  ch2 = NAN;
  ch3 = NAN;
  ch4 = NAN;
  ch5 = NAN;

  switch (mode) {
    case Mode::kAcceleration:
      readAcceleration(ch2, ch3, ch4, ch5);
      break;
    case Mode::kGyroscope:
      readGyroscope(ch2, ch3, ch4, ch5);
      break;
    case Mode::kMagnetometer:
      readMagnetometer(ch2, ch3, ch4, ch5);
      break;
    case Mode::kPressure:
      readPressure(ch2);
      break;
    case Mode::kTemperatureHumidity:
      readTemperatureHumidity(ch2, ch3);
      break;
    case Mode::kLightRgb:
      readLightRgb(ch2, ch3, ch4, ch5);
      break;
    case Mode::kAnalogInputs:
      readAnalogInputs(ch2, ch3, ch4);
      break;
  }
}

void sendSample() {
  // Unsigned wrap-around is well-defined; t is correct for ~49 days, then wraps.
  const unsigned long elapsedMs = (unsigned long)(millis() - startMs);
  float t = (float)elapsedMs / 1000.0f;
  float ch2 = 0, ch3 = 0, ch4 = 0, ch5 = 0;
  readChannels(ch2, ch3, ch4, ch5);

  uint8_t payload[kPayloadSizeBytes] = {0};
  writeFloat32LE(payload, sizeof(payload), 0, t);
  writeFloat32LE(payload, sizeof(payload), 4, ch2);
  writeFloat32LE(payload, sizeof(payload), 8, ch3);
  writeFloat32LE(payload, sizeof(payload), 12, ch4);
  writeFloat32LE(payload, sizeof(payload), 16, ch5);

  dataCharacteristic.writeValue(payload, sizeof(payload));
}

}  // namespace

void setup() {
  startMs = millis();

  imuOk = IMU.begin();
  htsOk = HTS.begin();
  baroOk = BARO.begin();
  apdsOk = APDS.begin();

  if (!BLE.begin()) {
    while (true) {
      delay(1000);
    }
  }

  BLE.setDeviceName("phyphox-sense");
  BLE.setLocalName("phyphox-sense");

  phyphoxService.addCharacteristic(dataCharacteristic);
  phyphoxService.addCharacteristic(configCharacteristic);
  BLE.addService(phyphoxService);

  writeActiveModeToConfigCharacteristic();

  BLE.advertise();
}

void pollConfigCharacteristic() {
  if (!configCharacteristic.written()) {
    return;
  }
  uint8_t buf[4] = {0};
  const int bytesRead = configCharacteristic.readValue(buf, sizeof(buf));
  if (bytesRead == static_cast<int>(sizeof(buf))) {
    setModeFromConfig(readFloat32LE(buf, sizeof(buf)));
  }
  writeActiveModeToConfigCharacteristic();
}

void loop() {
  BLE.poll();
  pollConfigCharacteristic();

  BLEDevice central = BLE.central();
  if (!central) {
    return;
  }

  while (central.connected()) {
    BLE.poll();
    pollConfigCharacteristic();

    const unsigned long now = millis();
    if (now - lastSendMs >= kSendPeriodMs) {
      lastSendMs = now;
      sendSample();
    }
  }
}
