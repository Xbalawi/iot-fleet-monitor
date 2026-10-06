from anomaly import _threshold_check as threshold_check
from anomaly import TEMP_MIN, TEMP_MAX, VIBRATION_MAX

def test_normal_temperature_is_not_anomalous():
    assert threshold_check("temperature", 25) == False

def test_low_temperature_is_anomalous():
    assert threshold_check("temperature", 5) == True

def test_high_temperature_is_anomalous():
    assert threshold_check("temperature", 45) == True

def test_normal_vibration_is_not_anomalous():
    assert threshold_check("vibration", VIBRATION_MAX) == False

def test_high_vibration_is_anomalous():
    assert threshold_check("vibration", VIBRATION_MAX + 1) == True

def test_low_vibration_is_not_anomalous():
    assert threshold_check("vibration", 0) == False

    