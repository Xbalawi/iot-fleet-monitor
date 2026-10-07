from flask import Flask, jsonify, request, render_template
from models import db, Reading
from mqtt_listener import start_listener, connection_state
from datetime import datetime, timezone



def create_app(test_config=None):
    app = Flask(__name__)
    
    # Configure the database URI
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///readings.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 

    if test_config:
        app.config.update(test_config)
    
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
        try:
            limit = int(request.args.get("limit", 50))
            limit = min(limit, 500)
        except ValueError:
            limit = 50

        rows = Reading.query.order_by(Reading.received_at.desc()).limit(limit).all()
        result = []
        for r in rows:
            row_dict = {c.name: getattr(r, c.name) for c in r.__table__.columns}
            row_dict["timestamp"] = r.timestamp.isoformat()
            row_dict["received_at"] = r.received_at.isoformat()
            result.append(row_dict)
        return jsonify(result)

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html")

    return app


if __name__ == "__main__":
    app = create_app()
    start_listener(app)
    # use_reloader=False prevents the MQTT client from connecting twice in dev mode
    # app.run(port=5000, use_reloader=False) works, but to allow external access, we bind to
    app.run(host="0.0.0.0", port=5000, use_reloader=False) # Allow external access to the Flask app