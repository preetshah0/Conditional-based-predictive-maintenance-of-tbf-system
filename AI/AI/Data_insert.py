from flask import Flask, jsonify, request
import threading
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from pymongo import MongoClient

# MQTT Broker details
broker = "broker.hivemq.com"  # Same broker as the publisher
port = 1883  # Default MQTT port
topics = ["/voltage", "/temperature", "/vibration", "/current", "/mq135", "/humidity"]  # Different topics

# MQTT authentication
mqtt_user = "ventraguardai"  # Username for the broker
mqtt_pass = "ventraguardai"  # Password for the broker

# Shared data storage (holds the latest valid data for all topics)
mqtt_data = {
    "/voltage": None,
    "/temperature": None,
    "/vibration": None,
    "/current": None,
    "/mq135": None,
    "/humidity": None
}

# MongoDB connection setup
client = MongoClient("mongodb+srv://ronitrathod:ronit@cluster0.lvq61.mongodb.net/")  # Replace with your MongoDB URI if different
db = client["tunnel_station"]
collection = db["fan_sensors_final"]

# Flask app
app = Flask(__name__)

# REST API endpoint to get the latest MQTT data
@app.route('/get_data', methods=['GET'])
def get_data():
    # Check if all topics have valid, non-null data
    if all(mqtt_data[topic] is not None for topic in topics):
        return jsonify(mqtt_data)
    else:
        return jsonify({"error": "Data from one or more topics is missing or invalid"}), 404


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

        try:
            # Parse the JSON payload
            parsed_data = json.loads(payload)

            # Map topic to expected key
            topic_key_mapping = {
                "/temperature": "Temperature (C)",
                "/humidity": "Humidity (%)",  # Expect 'Humidity (%)' but handle variations
                "/vibration": "Vibration (g)",
                "/mq135": "MQ135 (ppm)",
                "/voltage": "Voltage (V)",
                "/current": "Current (A)"
            }

            # Check if the topic matches expected keys
            if msg.topic == "/humidity":
                # Handle different possible variations of the humidity key
                if "Humidity (%)" in parsed_data:
                    mqtt_data[msg.topic] = parsed_data["Humidity (%)"]
                elif "Humidity ()" in parsed_data:
                    mqtt_data[msg.topic] = parsed_data["Humidity ()"]
                else:
                    print(f"Warning: Neither 'Humidity (%)' nor 'Humidity ()' found in /humidity. Skipping.")
            elif msg.topic in topic_key_mapping:
                expected_key = topic_key_mapping[msg.topic]

                # Handle key mismatches and update mqtt_data
                if expected_key in parsed_data:
                    mqtt_data[msg.topic] = parsed_data[expected_key]
                else:
                    print(f"Warning: Key '{expected_key}' not found in {msg.topic}. Skipping.")

            # If all required data is available, insert into MongoDB
            if all(mqtt_data[topic] is not None for topic in topics):
                document = {
                    "Temperature (C)": mqtt_data["/temperature"],
                    "Humidity (%)": mqtt_data["/humidity"],
                    "Vibration (g)": mqtt_data["/vibration"],
                    "MQ135 (ppm)": mqtt_data["/mq135"],
                    "Voltage (V)": mqtt_data["/voltage"],
                    "Current (A)": mqtt_data["/current"],
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Insert data into MongoDB
                collection.insert_one(document)
                print("Inserted into MongoDB:", document)

                # Reset mqtt_data for the next round
                for key in mqtt_data.keys():
                    mqtt_data[key] = None

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
