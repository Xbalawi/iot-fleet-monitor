from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Reading(db.Model):
    __tablename__ = "readings"

    id = db.Column(db.Integer, primary_key=True)
    
    # Indexed because dashboards will query "give me all data for sensor X"
    sensor_id = db.Column(db.String(50), index=True, nullable=False)
    
    type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    
    # When the sensor recorded the event
    timestamp = db.Column(db.DateTime, nullable=False)
    
    # When our database ingested it (using a lambda to evaluate exact time of insert)
    received_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    is_anomaly = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Reading {self.sensor_id} | {self.type}: {self.value}>"