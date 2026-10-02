TEMP_MIN = 10.0
TEMP_MAX = 40.0
VIBRATION_MAX = 4.5

def is_anomalous(sensor_type: str, value: float) -> bool:
    """
    Evaluates whether a single sensor reading is anomalous based on static threshold rules.
    
    Keeping this logic in its own module isolates domain rules from ingestion code.
    In Step 2, this function can be extended with statistical or ML approaches
    without changing mqtt_listener.py or models.py.
    """

    if sensor_type == "temperature":
        return value < TEMP_MIN or value > TEMP_MAX

    if sensor_type == "vibration":
        return value > VIBRATION_MAX

    if sensor_type == "occupancy":
        return False  # Occupancy is binary; no anomaly detection needed

    return False  # Unknown sensor types are not considered anomalous