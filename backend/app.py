from flask import Flask, jsonify, request
from models import db, Reading
from mqtt_listener import start_listener

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
        return jsonify({"status": "ok"})

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
        # (This dynamically grabs all columns from the Reading model)
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