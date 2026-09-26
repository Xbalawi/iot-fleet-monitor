import json
import random
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

# Broker settings
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "sensors/readings"

# Sensor definitions
SENSORS = [
    {"id": "temp-01", "type": "temperature"},
    {"id": "vib-01", "type": "vibration"},
    {"id": "occ-01", "type": "occupancy"},
]

def generate_sensor_value(sensor_type: str):
    """Generate plausible mock data based on sensor type."""
    if sensor_type == "temperature":
        return round(random.uniform(18.0, 30.0), 2)  # °C
    elif sensor_type == "vibration":
        return round(random.uniform(0.0, 5.0), 2)    # mm/s
    elif sensor_type == "occupancy":
        return random.choice([0, 1])                 # 0 = vacant, 1 = occupied
    return 0.0

def main():
    # Handle paho-mqtt v2.x and v1.x compatibility seamlessly
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()

    print(f"Connecting to MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
    
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_start()  # Runs network loop in background thread
        print(f"Connected! Publishing live readings to topic '{TOPIC}'...\n")

        while True:
            for sensor in SENSORS:
                payload = {
                    "sensor_id": sensor["id"],
                    "type": sensor["type"],
                    "value": generate_sensor_value(sensor["type"]),
                    # UTC timestamp (ISO 8601 format)
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                json_payload = json.dumps(payload)
                client.publish(TOPIC, json_payload)
                print(f"[SENT] {json_payload}")

            # Sleep between 2 to 5 seconds per batch
            delay = random.uniform(2, 5)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\nStopping simulator...")
    except Exception as e:
        print(f"\nBroker connection failed: {e}")
        print("Ensure your Mosquitto service/container is running on localhost:1883.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Disconnected cleanly.")

if __name__ == "__main__":
    main()