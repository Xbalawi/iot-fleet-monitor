import json
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "sensors/readings"
REQUIRED_FIELDS = {"sensor_id", "type", "value", "timestamp"}


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"Connected to broker successfully (Code: {reason_code})")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: '{TOPIC}'\nWaiting for messages...")
    else:
        print(f"Connection failed with reason code: {reason_code}")


def on_message(client, userdata, msg):
    try:
        # Decode the byte payload to a string, then parse it into a Python dictionary
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        print(f"[WARNING] Received malformed JSON: {msg.payload}")
        return

    # Check if all required fields exist in the parsed dictionary keys
    if not REQUIRED_FIELDS.issubset(data.keys()):
        print(f"[WARNING] Missing required fields. Payload keys: {list(data.keys())}")
        return

    # If it passes both checks, it's a valid reading
    print(f"[RECEIVED] {data['sensor_id']} ({data['type']}): {data['value']} at {data['timestamp']}")


def create_client():
    # Handle paho-mqtt v2.x and v1.x compatibility smoothly
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()

    # Attach the callback functions to the client
    client.on_connect = on_connect
    client.on_message = on_message
    
    return client


if __name__ == "__main__":
    client = create_client()
    print(f"Connecting to MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    
    # loop_forever() handles reconnections and blocks the main thread to listen for messages
    client.loop_forever()