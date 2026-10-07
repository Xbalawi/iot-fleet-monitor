import json
from datetime import datetime, timezone
# from backend import app
from sqlalchemy.exc import SQLAlchemyError
from anomaly import is_anomalous, maybe_retrain  

# Import the database and model we just created
from models import db, Reading

import paho.mqtt.client as mqtt
import os


# BROKER_HOST = "localhost" Hardcoded for use in a local machine
BROKER_HOST = os.environ.get("BROKER_HOST", "localhost") #use environment variable if available, otherwise default to localhost
BROKER_PORT = 1883
TOPIC = "sensors/readings"
REQUIRED_FIELDS = {"sensor_id", "type", "value", "timestamp"}
connection_state = {"connected": False, "last_message_at": None}


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        connection_state["connected"] = True
        print(f"Connected to broker successfully (Code: {reason_code})")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: '{TOPIC}'\nWaiting for messages...")
    else:
        connection_state["connected"] = False
        print(f"Connection failed with reason code: {reason_code}")


def on_message(client, userdata, msg):
    connection_state["last_message_at"] = datetime.now(timezone.utc)
    app = userdata  # We passed the Flask app via user_data_set()
    
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        print(f"[WARNING] Received malformed JSON: {msg.payload}")
        return
    
    if not REQUIRED_FIELDS.issubset(data.keys()):
        print(f"[WARNING] Missing required fields. Payload keys: {list(data.keys())}")
        return

    elif not isinstance(data["value"], (int, float)):
        print(f"[WARNING] 'value' is not numeric: {data['value']!r}")
        return

    # 1. Parse the ISO 8601 timestamp safely
    try:
        # Replace 'Z' with '+00:00' to handle older Python version compatibility
        ts_str = data['timestamp'].replace("Z", "+00:00")
        timestamp_obj = datetime.fromisoformat(ts_str)
    except ValueError:
        print(f"[WARNING] Invalid timestamp format: {data['timestamp']}")
        return

    # 2. Push the Flask application context so SQLAlchemy knows which database to use
    with app.app_context():
        try:
            anomaly_flag = is_anomalous(data['type'], data['value'])

            new_reading = Reading(
                sensor_id=data['sensor_id'],
                type=data['type'],
                value=data['value'],
                timestamp=timestamp_obj,
                is_anomaly=anomaly_flag
            )

            db.session.add(new_reading)
            db.session.commit()
            maybe_retrain(data['type'])  # Update ML retraining counters after successful commit

            status_tag = "[ANOMALY]" if anomaly_flag else ""
            print(f"[SAVED] {status_tag} {data['sensor_id']} ({data['type']}): {data['value']}")
            
        except (SQLAlchemyError, TypeError, ValueError) as e:
            # 3. Rollback the session if the database throws an error (e.g. constraints, connection drop)
            db.session.rollback()
            print(f"[DB ERROR] Failed to insert record, transaction rolled back. Error: {e}")


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    connection_state["connected"] = False
    if reason_code != 0:
        # Paho will attempt to reconnect automatically when the connection drops unexpectedly.
        print(f"[WARNING] Unexpected disconnection. Reason code: {reason_code}")
    else:
        print("Disconnected from broker gracefully.")
    


def create_client():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    return client


def start_listener(app):
    """Initializes the MQTT client, attaches the Flask app, and starts a background thread."""
    client = create_client()
    
    # Pass the Flask app object into the client so callbacks can use it
    client.user_data_set(app)

    print(f"Connecting to MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    except (ConnectionRefusedError, OSError) as e:
        print(f"[WARNING] Could not reach MQTT broker at startup: {e}")
        print("The app will keep running; paho will keep retrying via loop_start().")

    # Non-blocking: loop_start() spins up a background thread for MQTT
    # This leaves the main thread free to run the Flask web server
    client.loop_start()

    return client