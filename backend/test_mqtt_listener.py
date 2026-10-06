import json
from app import create_app
import pytest
from models import db, Reading 
from mqtt_listener import on_message


class FakeMessage:
    def __init__(self, payload_dict):
        self.payload = json.dumps(payload_dict).encode('utf-8')

@pytest.fixture
def test_app():

    app = create_app(test_config={"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})    

    with app.app_context():
        db.create_all()

    return app 


def test_valid_reading_gets_saved(test_app):
    with test_app.app_context():
        payload = {
            "sensor_id": "temp-01",
            "type": "temperature",
            "value": 25.0,
            "timestamp": "2026-06-10T12:00:00+00:00"
        }

        msg = FakeMessage(payload)
        on_message(None, test_app, msg)

        readings = Reading.query.all()
        assert len(readings) == 1

