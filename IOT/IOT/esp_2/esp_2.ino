#include <ZMPT101B.h>
#include <WiFi.h>
#include <PubSubClient.h>

#define VIBRATION_SENSOR_PIN 25
#define VOLTAGE_SENSOR_PIN 35
#define MAX_ADC_VALUE 4095.0
#define MAX_VOLTAGE 3.3
#define MAX_VIBRATION 16.0

ZMPT101B voltageSensor(VOLTAGE_SENSOR_PIN);

const char* ssid = "SIH";
const char* password = "sih@2024";
const char* mqtt_server = "broker.hivemq.com";
const char* topic_vibration = "/vibration";
const char* topic_voltage = "/voltage";
const char* sync_topic = "esp/sync";

WiFiClient espClient;
PubSubClient client(espClient);

void connectToWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
  }
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32Client2")) {
      client.subscribe(sync_topic);
    } else {
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  connectToWiFi();
  client.setServer(mqtt_server, 1883);
  pinMode(VIBRATION_SENSOR_PIN, INPUT);
}

void publishData() {
  float adcValue = analogRead(VIBRATION_SENSOR_PIN);
  float voltage = (adcValue / MAX_ADC_VALUE) * MAX_VOLTAGE;
  float vibration = (voltage / MAX_VOLTAGE) * MAX_VIBRATION;
  float rmsVoltage = voltageSensor.getRmsVoltage(500);

  char vibrationPayload[50];
  snprintf(vibrationPayload, sizeof(vibrationPayload), "{\"Vibration (g)\": %.2f}", vibration);
  client.publish(topic_vibration, vibrationPayload);

  char voltagePayload[50];
  snprintf(voltagePayload, sizeof(voltagePayload), "{\"Voltage (V)\": %.2f}", rmsVoltage);
  client.publish(topic_voltage, voltagePayload);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  static unsigned long lastSyncTime = 0;
  if (millis() - lastSyncTime > 5000) {
    publishData();
    lastSyncTime = millis();
  }
}
