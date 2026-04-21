#include <ArduinoBLE.h>
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

// Writes 4 bytes at buf[offset..offset+3]. Caller must ensure offset + 4 <= buffer size.
void writeFloat32LE(uint8_t* buf, int offset, float value) {
  static_assert(sizeof(float) == 4, "Expected IEEE-754 float32");
  if (buf == nullptr || offset < 0 || offset + 4 > kPayloadSizeBytes) {
    return;  // Guard against misuse; current call sites use offset in {0,4,8,12,16}.
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

void setModeFromConfig(float configValue) {
  if (!std::isfinite(configValue)) {
    return;
  }
  int raw = (int)roundf(configValue);
  // Accept the full reserved range 1..9; values 7 and 8 are reserved for future
  // experiments and fall through to default: below, leaving mode unchanged.
  if (raw < 1 || raw > 9) {
    return;
  }
  switch (raw) {
    case (int)Mode::kAcceleration:
    case (int)Mode::kGyroscope:
    case (int)Mode::kMagnetometer:
    case (int)Mode::kPressure:
    case (int)Mode::kTemperatureHumidity:
    case (int)Mode::kLightRgb:
    case (int)Mode::kAnalogInputs:
      mode = (Mode)raw;
      break;
    default:
      // Reserved mode received; silently keep the current mode rather than
      // resetting to a default.  This allows future modes to be added to the
      // sketch without breaking existing app-side experiments that may send
      // an unrecognised value during a firmware upgrade.
      break;
  }
}

// Fills ch2..ch5 from x,y,z and sets ch5 = magnitude (for IMU modes).
void setChannelsFromXYZ(float x, float y, float z, float& ch2, float& ch3, float& ch4, float& ch5) {
  ch2 = x;
  ch3 = y;
  ch4 = z;
  ch5 = sqrtf(x * x + y * y + z * z);
}

void readChannels(float& ch2, float& ch3, float& ch4, float& ch5) {
  ch2 = NAN;
  ch3 = NAN;
  ch4 = NAN;
  ch5 = NAN;

  if (mode == Mode::kAcceleration) {
    float x = 0, y = 0, z = 0;
    if (imuOk && IMU.accelerationAvailable()) {
      IMU.readAcceleration(x, y, z);
      setChannelsFromXYZ(x, y, z, ch2, ch3, ch4, ch5);
    }
    return;
  }

  if (mode == Mode::kGyroscope) {
    float x = 0, y = 0, z = 0;
    if (imuOk && IMU.gyroscopeAvailable()) {
      IMU.readGyroscope(x, y, z);
      setChannelsFromXYZ(x, y, z, ch2, ch3, ch4, ch5);
    }
    return;
  }

  if (mode == Mode::kMagnetometer) {
    float x = 0, y = 0, z = 0;
    if (imuOk && IMU.magneticFieldAvailable()) {
      IMU.readMagneticField(x, y, z);
      setChannelsFromXYZ(x, y, z, ch2, ch3, ch4, ch5);
    }
    return;
  }

  if (mode == Mode::kPressure) {
    if (baroOk) {
      ch2 = BARO.readPressure(); // kPa (matches pressure_plot_v1-2.phyphox, which converts to hPa in analysis)
    }
    return;
  }

  if (mode == Mode::kTemperatureHumidity) {
    if (htsOk) {
      ch2 = HTS.readTemperature();
      ch3 = HTS.readHumidity();
    }
    return;
  }

  if (mode == Mode::kLightRgb) {
    int r = 0, g = 0, b = 0, c = 0;
    if (apdsOk && APDS.colorAvailable()) {
      APDS.readColor(r, g, b, c);
      ch2 = (float)c;
      ch3 = (float)r;
      ch4 = (float)g;
      ch5 = (float)b;
    }
    return;
  }

  if (mode == Mode::kAnalogInputs) {
    ch2 = (float)analogRead(A0);
    ch3 = (float)analogRead(A1);
    ch4 = (float)analogRead(A2);
    return;
  }
}

void sendSample() {
  // Unsigned wrap-around is well-defined; t is correct for ~49 days, then wraps.
  const unsigned long elapsedMs = (unsigned long)(millis() - startMs);
  float t = (float)elapsedMs / 1000.0f;
  float ch2 = 0, ch3 = 0, ch4 = 0, ch5 = 0;
  readChannels(ch2, ch3, ch4, ch5);

  uint8_t payload[kPayloadSizeBytes] = {0};
  writeFloat32LE(payload, 0, t);
  writeFloat32LE(payload, 4, ch2);
  writeFloat32LE(payload, 8, ch3);
  writeFloat32LE(payload, 12, ch4);
  writeFloat32LE(payload, 16, ch5);

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

  uint8_t cfg[4] = {0, 0, 0, 0};
  configCharacteristic.writeValue(cfg, sizeof(cfg));

  BLE.advertise();
}

void pollConfigCharacteristic() {
  if (!configCharacteristic.written()) {
    return;
  }
  uint8_t buf[4] = {0};
  if (configCharacteristic.readValue(buf, sizeof(buf))) {
    setModeFromConfig(readFloat32LE(buf, sizeof(buf)));
  }
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
