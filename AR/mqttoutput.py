from flask import Flask, jsonify, request
import threading
import paho.mqtt.client as mqtt
import json

# MQTT Broker details
broker = "broker.hivemq.com"  # Same broker as the publisher
port = 1883  # Default MQTT port
topics = ["/temperature", "/voltage", "/current", "/humidity", "/vibration", "/mq135"]  # Multiple topics

# MQTT authentication
mqtt_user = "ventraguardai"  # Username for the broker
mqtt_pass = "ventraguardai"  # Password for the broker

# Shared data storage (holds the latest valid data from all topics)
mqtt_data = {
    "TEMP": None,
    "HUM": None,
    "VIB": None,
    "MQ135": None,
    "VOLTAGE": None,
    "CUR": None
}

# Flask app
app = Flask(__name__)

# REST API endpoint to get the latest MQTT data
@app.route('/get_data', methods=['GET'])
def get_data():
    if any(value is not None for value in mqtt_data.values()):
        return jsonify(mqtt_data)
    else:
        return jsonify({"error": "No valid data received yet"}), 404

# Callback when connected to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to all topics
        for topic in topics:
            client.subscribe(topic)
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
    global mqtt_data
    try:
        # Decode the message payload
        payload = msg.payload.decode('utf-8')
        print(f"Message received on topic {msg.topic}: {payload}")

        # Parse the payload as JSON
        try:
            parsed_data = json.loads(payload)
            print(f"Parsed JSON: {parsed_data}")

            if msg.topic == "/temperature":
                mqtt_data["TEMP"] = float(parsed_data.get("Temperature (C)", 0))
            elif msg.topic == "/humidity":
                mqtt_data["HUM"] = float(parsed_data.get("Humidity ()", 0))
            elif msg.topic == "/vibration":
                mqtt_data["VIB"] = float(parsed_data.get("Vibration (g)", 0))
            elif msg.topic == "/mq135":
                mqtt_data["MQ135"] = float(parsed_data.get("MQ135 (ppm)", 0))
            elif msg.topic == "/voltage":
                mqtt_data["VOLTAGE"] = float(parsed_data.get("Voltage (V)", 0))
            elif msg.topic == "/current":
                mqtt_data["CUR"] = float(parsed_data.get("Current (A)", 0))

            # Print the updated data
            print("\nUpdated MQTT Data:")
            for key, value in mqtt_data.items():
                print(f"{key}: {value}")
        except json.JSONDecodeError:
            print("Received data is not valid JSON.")
    except Exception as e:
        print(f"Error processing message: {e}")

# MQTT Client setup
def start_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(mqtt_user, mqtt_pass)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print("Connecting to broker...")
        client.connect(broker, port, keepalive=60)
        client.loop_forever()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

# Start the Flask app and MQTT client
if __name__ == '__main__':
    # Start the MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Start the Flask app
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    flask_thread.daemon = True
    flask_thread.start()

    # Wait for manual key press to exit
    input("Press Enter to terminate the program...\n")
