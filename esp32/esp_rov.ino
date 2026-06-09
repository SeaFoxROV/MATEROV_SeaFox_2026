#if !defined(ESP32)
  #error ESP32 only
#endif

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "LSM6DS3.h"
#include <MS5837.h>

#include <WebServer_WT32_ETH01.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

/* ===================== RED ===================== */

IPAddress myIP (192, 168, 1, 21);
IPAddress myGW (192, 168, 1,  1);
IPAddress mySN (255, 255, 255, 0);
IPAddress myDNS(8,   8,   8,  8);

/* ===================== UDP ===================== */

WiFiUDP udp;
const int UDP_PORT = 8888;
char packetBuffer[64];

WiFiUDP udpSend;
const int UDP_SEND_PORT = 8889;
IPAddress hostIP;

/* ===================== I2C ===================== */

#define I2C_SDA 32
#define I2C_SCL 33

/* ===================== PCA9685 ===================== */

Adafruit_PWMServoDriver pca9685(0x40);

#define PWM_FREQ   50
#define OSC_FREQ   25000000
#define NUM_MOTORS 8

#define ESC_NEUTRAL_US 1500
#define ESC_MIN_US     1100
#define ESC_MAX_US     1900

//Imu temp variables
float accelX, accelY, accelZ, gyroX, gyroY, gyroZ = 0;

//bar02 temp variables
float pressure, temperature, depth, altitude = 0;

/* ===================== IMU LSM6DS3 ===================== */
LSM6DS3 imu(I2C_MODE, 0x6B); 

/* ===================== BAR30 MS5837 ===================== */
MS5837 bar30;

/* ===================== UTILS ===================== */
const uint8_t PWM_CHANNEL[NUM_MOTORS] = {14, 13, 12, 11, 10, 9, 8, 6};

void setMotors(uint16_t pwms[NUM_MOTORS])
{
  for (int i = 0; i < NUM_MOTORS; i++)
    pca9685.writeMicroseconds(PWM_CHANNEL[i], pwms[i]);
}

bool parsePacket(const char* buf, uint16_t out[NUM_MOTORS])
{
  char tmp[64];
  strncpy(tmp, buf, sizeof(tmp) - 1);
  tmp[sizeof(tmp) - 1] = '\0';

  int count = 0;
  char* token = strtok(tmp, ";");

  while (token != NULL && count < NUM_MOTORS)
  {
    int val = atoi(token);
    if (val < ESC_MIN_US || val > ESC_MAX_US) return false;
    out[count++] = (uint16_t)val;
    token = strtok(NULL, ";");
  }

  return (count == NUM_MOTORS);
}

void sendData()
{
  if (!hostIP) return;  

  char buf[128];
  snprintf(buf, sizeof(buf),
    "%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.2f;%.2f;%.2f;%.2f",
    accelX, accelY, accelZ,
    gyroX,  gyroY,  gyroZ,
    pressure, temperature, depth, altitude
  );

  udpSend.beginPacket(hostIP, UDP_SEND_PORT);
  udpSend.print(buf);
  udpSend.endPacket();
}

void readSensors()
{

  accelX = imu.readFloatAccelX();
  accelY = imu.readFloatAccelY();
  accelZ = imu.readFloatAccelZ();
  gyroX = imu.readFloatGyroX();
  gyroY = imu.readFloatGyroY();
  gyroZ = imu.readFloatGyroZ();

  bar30.read();
  pressure = bar30.pressure();
  temperature = bar30.temperature();
  depth = bar30.depth();
  altitude = bar30.altitude();

}

/* ===================== SETUP ===================== */

void setup()
{
  Serial.begin(115200);

  WT32_ETH01_onEvent();
  ETH.begin(ETH_PHY_ADDR, ETH_PHY_POWER);
  ETH.config(myIP, myGW, mySN, myDNS);
  WT32_ETH01_waitForConnect();

  Serial.print("IP: ");
  Serial.println(ETH.localIP());

  udp.begin(UDP_PORT);
  Serial.print("UDP escuchando en puerto ");
  Serial.println(UDP_PORT);

  Wire.begin(I2C_SDA, I2C_SCL);
  pca9685.begin();
  pca9685.setOscillatorFrequency(OSC_FREQ);
  pca9685.setPWMFreq(PWM_FREQ);

  for (int i = 0; i < 16; i++)
    pca9685.writeMicroseconds(i, ESC_NEUTRAL_US);

  Serial.println("PCA9685 OK");
  

    if (imu.begin() != 0) {
    Serial.println("ERROR: LSM6DS3 no encontrado en 0x6B");
    while (true);
  }
  Serial.println("LSM6DS3 OK");

    if (!bar30.init()) {
    Serial.println("ERROR: Bar30 no encontrado en 0x76");
    while (true);
  }
  bar30.setModel(MS5837::MS5837_30BA);
  bar30.setFluidDensity(1029); // agua salada — usa 997 para agua dulce
  Serial.println("Bar30 OK");
  
}

/* ===================== LOOP ===================== */

void loop()
{

  readSensors();

  int packetSize = udp.parsePacket();

  if (packetSize > 0)
  {
    hostIP = udp.remoteIP();
    
    int len = udp.read(packetBuffer, sizeof(packetBuffer) - 1);
    if (len > 0) packetBuffer[len] = '\0';
    Serial.println(packetBuffer);
    uint16_t pwms[NUM_MOTORS];
    if (parsePacket(packetBuffer, pwms))
      setMotors(pwms);
  }

  sendData(); 
}
