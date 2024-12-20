from twilio.rest import Client
import torch
import joblib
from threshold_model2 import scaler, window_size, CNNLSTM  # Assuming 'best_c' is your trained model

# Function to send SMS notification
def send_sms(body, to_phone_numbers):
    # Your Twilio Account SID and Auth Token
    account_sid = 'AC3d5672398287f8cb88391e8f74161aa3'
    auth_token = 'da1f49d9e6115a3606678cb4602d1e96'
    
    # Create a Twilio client
    client = Client(account_sid, auth_token)
    
    # Send the SMS to each phone number
    for to_phone_number in to_phone_numbers:
        message = client.messages.create(
            body=body,
            from_='+16282326685',  # Your Twilio phone number
            to=to_phone_number  # Recipient's phone number
        )
        
        # Return the SID of the sent message for each recipient
        print(f"Message sent to {to_phone_number}, SID: {message.sid}")
        return message.sid  # Optionally, return the SID for each message

# Real-time data (example)
real_time_data = {
    "Temperature (C)": 175.0,  # Increased temperature indicating possible overheating
    "Humidity (%)": 95.0,      # High humidity, which may be abnormal for the system
    "Vibration (g)": 2.5,      # High vibration, indicating mechanical stress
    "MQ135 (ppm)": 200.0,      # High air quality value (could indicate a problem)
    "Voltage (V)": 3.2,        # Slightly higher voltage, possibly indicating instability
    "Current (A)": 5.5,        # Higher current, which could indicate a potential overload
    "RUL": 50,                 # Reduced RUL, suggesting a higher likelihood of failure
    "Failure Rate (%)": 80,    # Very high failure rate, indicating a potential issue
    "Timestamp": "2024-12-15 08:30:00"
}

# Display all features for internal use
print("All Features Data:")
for key, value in real_time_data.items():
    print(f"{key}: {value}")

# Model-related features for internal processing (including RUL and Failure Rate)
model_input_data = [
    real_time_data["Temperature (C)"],
    real_time_data["Humidity (%)"],
    real_time_data["Vibration (g)"],
    real_time_data["MQ135 (ppm)"],
    real_time_data["Voltage (V)"],
    real_time_data["Current (A)"],
    real_time_data["RUL"],
    real_time_data["Failure Rate (%)"]
]

# Ensure the scaler is loaded properly
scaler = joblib.load('scaler.pkl')  # Load the saved scaler

# Scaling the data (assuming the scaler is loaded previously)
scaled_input_data = scaler.transform([model_input_data])

# Reshaping the input for the model (based on the window size)
scaled_input_data_windowed = scaled_input_data.reshape(1, 1, len(model_input_data))  # Reshape to (1, 1, 8)

# Load the pre-trained model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Ensure the device is set properly

# Initialize the model with the required 'input_size' (8 in your case)
input_size = len(model_input_data)  # 8 features in the input data
model = CNNLSTM(input_size=input_size)  # Provide the input size

# Now move the model to the desired device
model = model.to(device)  # Move the model to the device (GPU/CPU)

# Predicting with the model
output = model(torch.tensor(scaled_input_data_windowed, dtype=torch.float32).to(device))

# Convert model output to a prediction (binary)
prediction = (output.squeeze() > 0.5).int()

# Checking prediction and sending alert
if prediction.item() == 1:
    print("Alert: Potential failure detected!")
    
    # Prepare the SMS body with all sensor data
    sms_body = f"Alert: A failure has been detected based on the following sensor data:\n\n" \
               f"Temperature (C): {real_time_data['Temperature (C)']}\n" \
               f"Humidity (%): {real_time_data['Humidity (%)']}\n" \
               f"Vibration (g): {real_time_data['Vibration (g)']}\n" \
               f"MQ135 (ppm): {real_time_data['MQ135 (ppm)']}\n" \
               f"Voltage (V): {real_time_data['Voltage (V)']}\n" \
               f"Current (A): {real_time_data['Current (A)']}\n" \
               f"RUL: {real_time_data['RUL']}\n" \
               f"Failure Rate (%): {real_time_data['Failure Rate (%)']}\n" \
               f"Timestamp: {real_time_data['Timestamp']}\n\n" \
               f"Please take necessary action immediately."

    # List of phone numbers to send the alert to
    phone_numbers = ["+919662436766", "+919773422985", "+917622879092"]  # Add more phone numbers as needed

    # Send SMS to all recipients
    send_sms(sms_body, phone_numbers)
else:
    print("System is operating normally.")
