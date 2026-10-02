import numpy as np
from sklearn.ensemble import IsolationForest

# Lock the random seed so this script produces the exact same results every time it runs
np.random.seed(42)

def generate_normal_vibration(n):
    # Real sensor noise usually follows a bell curve (Gaussian/Normal distribution)
    # Mean of 2.0 mm/s, standard deviation of 0.8
    values = np.random.normal(loc=2.0, scale=0.8, size=n)
    # Sensors have physical limits; clip to a plausible 0.0 to 5.0 range
    return np.clip(values, 0.0, 5.0)

def generate_injected_outliers(n):
    # Generate values that represent a machine physically tearing itself apart
    # (Uniformly distributed between 10.0 and 15.0 mm/s)
    return np.random.uniform(low=10.0, high=15.0, size=n)

def run_validation():
    # 1. Generate the dataset
    n_normal = 200
    n_outliers = 10
    
    normal = generate_normal_vibration(n_normal)
    outliers = generate_injected_outliers(n_outliers)
    
    # Combine into a single 1D array
    all_values = np.concatenate([normal, outliers])
    
    # 2. Build the Ground Truth labels (0 = normal, 1 = anomaly)
    labels_normal = np.zeros(n_normal, dtype=int)
    labels_outliers = np.ones(n_outliers, dtype=int)
    ground_truth = np.concatenate([labels_normal, labels_outliers])
    
    # 3. Reshape for Scikit-Learn (needs 2D array: [[v1], [v2], ...])
    X = all_values.reshape(-1, 1)
    
    # 4. Train the Isolation Forest
    # contamination=0.05 tells it to expect roughly 5% anomalies
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)
    
    # 5. Get predictions (-1 = anomaly, 1 = normal)
    raw_predictions = model.predict(X)
    
    # Convert predictions to match our 0/1 label format (1 = anomaly)
    predicted_labels = (raw_predictions == -1).astype(int)
    
    # 6. Calculate True Positives and False Positives
    true_positives = np.sum((ground_truth == 1) & (predicted_labels == 1))
    false_positives = np.sum((ground_truth == 0) & (predicted_labels == 1))
    
    # 7. Print the Summary
    print("=== Isolation Forest Validation Report ===")
    print(f"Total dataset: {len(all_values)} readings ({n_normal} normal, {n_outliers} injected outliers)")
    print("-" * 40)
    print(f"True Positives:  {true_positives}/{n_outliers} injected outliers detected")
    print(f"False Positives: {false_positives}/{n_normal} normal readings falsely flagged (~{(false_positives/n_normal)*100:.1f}%)")
    print("-" * 40)

    true_positive_rate = true_positives / n_outliers
    false_positive_rate = false_positives / n_normal

    if true_positive_rate >= 0.8 and false_positive_rate <= 0.08:
        print("Verdict: Model is performing well.")
    else:
        print("Verdict: Model needs tuning (adjust contamination or dataset size).")
    

if __name__ == "__main__":
    run_validation()