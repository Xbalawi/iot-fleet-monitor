import json
from datetime import datetime
import paho.mqtt.client as mqtt
from sqlalchemy.exc import SQLAlchemyError

# Import the database and model we just created
from models import db, Reading

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
    app = userdata  # We passed the Flask app via user_data_set()
    
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        print(f"[WARNING] Received malformed JSON: {msg.payload}")
        return
    
    if not isinstance(data["value"], (int, float)):
        print(f"[WARNING] 'value' is not numeric: {data['value']!r}")
        return

    elif not REQUIRED_FIELDS.issubset(data.keys()):
        print(f"[WARNING] Missing required fields. Payload keys: {list(data.keys())}")
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
            new_reading = Reading(
                sensor_id=data['sensor_id'],
                type=data['type'],
                value=data['value'],
                timestamp=timestamp_obj
            )
            db.session.add(new_reading)
            db.session.commit()
            print(f"[SAVED] {data['sensor_id']} ({data['type']}): {data['value']}")
            
        except (SQLAlchemyError, TypeError, ValueError) as e:
            # 3. Rollback the session if the database throws an error (e.g. constraints, connection drop)
            db.session.rollback()
            print(f"[DB ERROR] Failed to insert record, transaction rolled back. Error: {e}")


def create_client():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message
    return client


def start_listener(app):
    """Initializes the MQTT client, attaches the Flask app, and starts a background thread."""
    client = create_client()
    
    # Pass the Flask app object into the client so callbacks can use it
    client.user_data_set(app)
    
    print(f"Connecting to MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    
    # Non-blocking: loop_start() spins up a background thread for MQTT
    # This leaves the main thread free to run the Flask web server
    client.loop_start()
    
    return client