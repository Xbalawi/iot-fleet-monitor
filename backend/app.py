from flask import Flask, jsonify, request
from models import db, Reading
from mqtt_listener import start_listener, connection_state
from datetime import datetime, timezone

def create_app():
    app = Flask(__name__)
    
    # Configure the database URI
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///readings.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Create the tables if they don't exist yet
    with app.app_context():
        db.create_all()

    @app.route("/health")
    def health():
        is_connected = connection_state.get("connected", False)
        last_message_at = connection_state.get("last_message_at")

        # State 1: Disconnected from MQTT broker entirely
        if not is_connected:
            return jsonify({
                "status": "degraded",
                "connected": False,
                "reason": "Broker disconnected",
                "last_message_seconds_ago": None
            }), 503

        # State 2: Connected, but startup window (no messages received yet)
        if last_message_at is None:
            return jsonify({
                "status": "ok",
                "connected": True,
                "reason": "Connected; awaiting initial message stream",
                "last_message_seconds_ago": None
            }), 200

        # State 3: Connected & streaming — check message freshness
        seconds_ago = (datetime.now(timezone.utc) - last_message_at).total_seconds()
        
        if seconds_ago <= 30:
            return jsonify({
                "status": "ok",
                "connected": True,
                "last_message_seconds_ago": round(seconds_ago, 2)
            }), 200
        else:
            return jsonify({
                "status": "degraded",
                "connected": True,
                "reason": f"Message stream stale (silent for {round(seconds_ago, 1)}s)",
                "last_message_seconds_ago": round(seconds_ago, 2)
            }), 503

    @app.route("/readings")
    def readings():
        # Read the ?limit= query param, default to 50
        try:
            limit = int(request.args.get("limit", 50))
            # Cap the limit at 500
            limit = min(limit, 500)
        except ValueError:
            limit = 50  # Fallback if the user passes a non-integer string

        # Query newest first
        recent_readings = Reading.query.order_by(Reading.received_at.desc()).limit(limit).all()
        
        # Convert the SQLAlchemy objects to a list of dictionaries
        result = [
            {column.name: getattr(reading, column.name) for column in reading.__table__.columns}
            for reading in recent_readings
        ]
        
        return jsonify(result)

    return app

if __name__ == "__main__":
    app = create_app()
    start_listener(app)
    # use_reloader=False prevents the MQTT client from connecting twice in dev mode
    app.run(port=5000, use_reloader=False)