import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Parameters
num_samples = 500000  # Total number of samples
time_interval = 1  # Time interval in minutes

# Sensor ranges based on the provided table
temperature_range = (20, 45)  # Temperature in C
humidity_range = (40, 70)  # Humidity in %
current_range = (0, 0.03)  # Current in A (0 to 30 mA)
voltage_range = (0, 5)  # Voltage in V
vibration_range = (0.02, 0.07)  # Vibration in g
mq135_range = (300, 600)  # Air Quality (MQ135) in ppm

# Sensor standard deviations for variability
temperature_std = 1.0
humidity_std = 1.5
current_std = 0.001  # Lower variation for milliampere range
voltage_std = 0.1
vibration_std = 0.005
mq135_std = 20.0

# Threshold Values for Sensors
thresholds = {
    "Temperature (C)": 50,
    "Humidity (%)": 85,
    "Current (A)": 0.028,  # ~28 mA
    "Voltage (V)": 5,
    "Vibration (g)": 0.1,
    "MQ135 (ppm)": 1000,
}

# Weights for each sensor contributing to failure level
failure_weights = {
    "Temperature (C)": 20,  # Weight in %
    "Humidity (%)": 20,
    "Current (A)": 15,
    "Voltage (V)": 15,
    "Vibration (g)": 15,
    "MQ135 (ppm)": 15,
}

# Generate Timestamps
start_date = datetime.now() - timedelta(minutes=num_samples)
timestamps = [(start_date + timedelta(minutes=i)).replace(microsecond=0) for i in range(num_samples)]

# Sensor data generation with normal distributions
np.random.seed(42)

# Generate synthetic data
temperature = np.clip(np.random.normal(np.mean(temperature_range), temperature_std, num_samples), *temperature_range)
humidity = np.clip(np.random.normal(np.mean(humidity_range), humidity_std, num_samples), *humidity_range)
current = np.clip(np.random.normal(np.mean(current_range), current_std, num_samples), *current_range)
voltage = np.clip(np.random.normal(np.mean(voltage_range), voltage_std, num_samples), *voltage_range)
vibration = np.clip(np.random.normal(np.mean(vibration_range), vibration_std, num_samples), *vibration_range)
mq135 = np.clip(np.random.normal(np.mean(mq135_range), mq135_std, num_samples), *mq135_range)

# Function to calculate failure level
def calculate_failure_level(row):
    failure_level = 0
    for sensor, threshold in thresholds.items():
        if row[sensor] > threshold * 0.8:  # Near-failure condition
            failure_level += failure_weights[sensor] * 0.5
        if row[sensor] > threshold:  # Critical condition
            failure_level += failure_weights[sensor]
    return min(failure_level, 100)  # Cap failure level at 100%

# Function to calculate Remaining Useful Life (RUL)
def calculate_rul(failure_level, total_life=1500):
    degradation_factor = failure_level / 100  # Percentage of degradation
    return max(0, total_life * (1 - degradation_factor))  # RUL is reduced proportionally

# Create DataFrame with sensor data
data = {
    "Timestamp": timestamps,
    "Temperature (C)": temperature,
    "Humidity (%)": humidity,
    "Current (A)": current,
    "Voltage (V)": voltage,
    "Vibration (g)": vibration,
    "MQ135 (ppm)": mq135,
}

df = pd.DataFrame(data)

# Add Failure Level and RUL columns
df["Failure Level (%)"] = df.apply(calculate_failure_level, axis=1)
df["RUL (minutes)"] = df["Failure Level (%)"].apply(calculate_rul)

# Save the dataset to CSV
output_file = "exhaust_fan_500k_samples_with_rul.csv"
df.to_csv(output_file, index=False)

print(f"Dataset with {num_samples} samples has been saved to {output_file}.")
