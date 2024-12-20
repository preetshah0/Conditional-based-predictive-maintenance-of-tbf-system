#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135_PIN 33
#define CURRENT_SENSOR_PIN 34

const char* ssid = "SIH";
const char* password = "sih@2024";

const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_user = "ventraguardai";
const char* mqtt_pass = "ventraguardai";
const char* topic_temperature = "/temperature";
const char* topic_humidity = "/humidity";
const char* topic_mq135 = "/mq135";
const char* topic_current = "/current";

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

// WiFi connection setup
void setup_wifi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
}

// MQTT reconnection setup
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client", mqtt_user, mqtt_pass)) {
      Serial.println("connected.");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 3 seconds.");
      delay(3000);
    }
  }
}

// Function to read current sensor
float readCurrent() {
  int raw = analogRead(CURRENT_SENSOR_PIN);
  float voltage = (raw / 4095.0) * 3.3;
  return -((voltage - 2.5) / 0.185); // Conversion to current in Amps
}

// Function to read MQ135 sensor
float readMQ135() {
  int raw = analogRead(MQ135_PIN);
  return (raw / 4095.0) * 1000; // Conversion to ppm
}

// Publish temperature data
void publishTemperature(float temperature) {
  char buffer[64];
  snprintf(buffer, sizeof(buffer), "{\"Temperature (C)\": %.2f}", temperature);
  client.publish(topic_temperature, buffer);
}

// Publish humidity data
void publishHumidity(float humidity) {
  char buffer[64];
  snprintf(buffer, sizeof(buffer), "{\"Humidity (%)\": %.2f}", humidity);
  client.publish(topic_humidity, buffer);
}

// Publish MQ135 data
void publishMQ135(float mq135PPM) {
  char buffer[64];
  snprintf(buffer, sizeof(buffer), "{\"MQ135 (ppm)\": %.2f}", mq135PPM);
  client.publish(topic_mq135, buffer);
}

// Publish current data
void publishCurrent(float current) {
  char buffer[64];
  snprintf(buffer, sizeof(buffer), "{\"Current (mA)\": %.2f}", current);
  client.publish(topic_current, buffer);
}

// Unified function to publish all data
void publishAllData() {
  char buffer[256]; // Combined buffer for all data if needed

  // Read and publish temperature
  float temperature = dht.readTemperature();
  if (!isnan(temperature)) { // Validate reading
    snprintf(buffer, sizeof(buffer), "{\"Temperature (C)\": %.2f}", temperature);
    client.publish(topic_temperature, buffer);
  } else {
    Serial.println("Failed to read temperature.");
  }

  // Read and publish humidity
  float humidity = dht.readHumidity();
  if (!isnan(humidity)) { // Validate reading
    snprintf(buffer, sizeof(buffer), "{\"Humidity (%)\": %.2f}", humidity);
    client.publish(topic_humidity, buffer);
  } else {
    Serial.println("Failed to read humidity.");
  }

  // Read and publish MQ135 data
  float mq135PPM = readMQ135();
  snprintf(buffer, sizeof(buffer), "{\"MQ135 (ppm)\": %.2f}", mq135PPM);
  client.publish(topic_mq135, buffer);

  // Read and publish current data
  float current = readCurrent();
  snprintf(buffer, sizeof(buffer), "{\"Current (mA)\": %.2f}", current);
  client.publish(topic_current, buffer);
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  reconnect();
}

void loop() {
  // Ensure WiFi stays connected
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  // Ensure MQTT stays connected
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Track the time for publishing all data
  static unsigned long lastPublishTime = 0;
  unsigned long currentTime = millis();

  if (currentTime - lastPublishTime > 5000) { // Publish every 5 seconds
    publishAllData();
    lastPublishTime = currentTime;
  }
}
