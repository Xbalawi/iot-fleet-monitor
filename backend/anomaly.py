from sklearn.ensemble import IsolationForest
from models import Reading

_models = {}    # sensor_type -> fitted IsolationForest
_counts = {}    # sensor_type -> readings seen since last (re)train
MIN_SAMPLES = 30  # Minimum number of samples required to train the model
RETRAIN_EVERY = 50  # Retrain the model after every N new readings

TEMP_MIN = 10.0
TEMP_MAX = 40.0
VIBRATION_MAX = 4.5

def train_model_for_type(sensor_type: str):
    # Query the 200 most recent readings for this specific sensor type
    recent_readings = Reading.query.filter_by(type=sensor_type)\
        .order_by(Reading.timestamp.desc())\
            .limit(200)\
            .all()

    if len(recent_readings) < MIN_SAMPLES:
        return None # Not enough data to train a model

    # Reshape the values into a 2D array for sklearn: [[V1], [V2], ...]
    values_2d = [[r.value] for r in recent_readings]

    # Fit the IsolationForest model
    # contamination=0.05 means we expect roughly 5% of the readings to be anomalous
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(values_2d)
    print(f"[ML] Trained model for '{sensor_type}' on {len(recent_readings)} samples")

    _models[sensor_type] = model
    return model


def ml_is_anomalous(sensor_type: str, value: float) -> bool:
    #Try to get the cached model; if missing, attempt to train it
    model = _models.get(sensor_type)
    if model is None:
        model = train_model_for_type(sensor_type)

    # If it's STILL None, we don't have MIN_SAMPLES yet. Skip ML for now and return False (not anomalous).
    if model is None:
        return False  # Not enough data to determine anomaly

    # Predict returns an array (e.g., [-1] for anomaly, [1] for normal). We only have one sample, so we take the first element.
    prediction = model.predict([[value]])
    return prediction[0] == -1  # True if anomalous, False otherwise


def maybe_retrain(sensor_type: str):
    # Initialize count to 0 if it doesn't exist yet, then add 1
    _counts[sensor_type] = _counts.get(sensor_type, 0) + 1

    if _counts[sensor_type] >= RETRAIN_EVERY:
        train_model_for_type(sensor_type)
        _counts[sensor_type] = 0  # Reset the count after retraining

def _threshold_check(sensor_type: str, value: float) -> bool:
    """Check if the value exceeds static thresholds for the given sensor type."""


    """ # 1. Update ML retraining counters
    maybe_retrain(sensor_type)

    # 2. Get ML prediction (will safely return False during warmup)
    is_ml_anomaly = ml_is_anomalous(sensor_type, value)

    # 3. Apply static threshold rules as a fallback/hard boundary
    is_hard_anomaly = False """

    if sensor_type == "temperature":
        return value < TEMP_MIN or value > TEMP_MAX

    elif sensor_type == "vibration":
        return value > VIBRATION_MAX

    """if sensor_type == "occupancy":
        return False  # Occupancy is binary; no anomaly detection needed"""
    
    return False


def is_anomalous(sensor_type: str, value: float) -> bool:
    """Combines static threshold checks with the ML model."""

    threshold_flag = _threshold_check(sensor_type, value) # your existing step 1 logic, renamed for clarity
    ml_flag = ml_is_anomalous(sensor_type, value) # your existing step 2 logic

    return threshold_flag or ml_flag  # If either method flags it, we consider it anomalous

