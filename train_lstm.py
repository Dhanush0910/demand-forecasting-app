import pymysql
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import os
import matplotlib.pyplot as plt
from datetime import timedelta

# connect to mysql and fetch real-time sales data
conn = pymysql.connect(host="localhost", user="root", password="Dhanush@7", database="demand_forecasting")
query = "SELECT date, sales FROM sales_data ORDER BY date ASC"
df = pd.read_sql(query, conn)
conn.close()

# ensure date is in datetime format
df["date"] = pd.to_datetime(df["date"])
df.set_index("date", inplace=True)

# remove duplicate dates by aggregating sales (e.g., taking the mean)
df = df.groupby(df.index).mean()

print("✅ real-time data fetched successfully from mysql!")
print(df.head())  # preview cleaned data

# check if we have enough data points
if len(df) < 31:  # need at least 31 rows for sequence_length = 30
    raise ValueError(f"❌ not enough data! at least 31 rows required, found {len(df)}")

# normalize sales data using min-max scaling
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(df.values)

# prepare dataset for lstm (sequence length = 30 days)
sequence_length = 30
X, y = [], []
for i in range(len(scaled_data) - sequence_length):
    X.append(scaled_data[i:i+sequence_length])
    y.append(scaled_data[i+sequence_length])

X, y = np.array(X), np.array(y)

# check if X is empty
if X.shape[0] == 0:
    raise ValueError("❌ X is empty! check data preprocessing.")

# reshape input to (samples, time steps, features)
X = X.reshape(X.shape[0], X.shape[1], 1)
y = y.reshape(-1, 1)

print("✅ dataset prepared successfully!")
print("X shape:", X.shape)  # should be (samples, 30, 1)
print("y shape:", y.shape)  # should be (samples, 1)

# define lstm model
model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(sequence_length, 1)),
    Dropout(0.2),
    LSTM(50, return_sequences=False),
    Dropout(0.2),
    Dense(25),
    Dense(1)
])

# compile model
model.compile(optimizer="adam", loss="mean_squared_error")

# train model
model.fit(X, y, batch_size=16, epochs=50)

# create models directory if not exists
if not os.path.exists("models"):
    os.makedirs("models")

# save trained model
model.save("models/lstm_model.h5")
print("✅ lstm model trained and saved successfully!")

# Load the model for forecasting
model = tf.keras.models.load_model("models/lstm_model.h5")

# Forecast future sales
forecast_days = int(input("Enter the number of days to forecast: "))
last_sequence = scaled_data[-sequence_length:]
predictions = []

for _ in range(forecast_days):
    pred_input = last_sequence[-sequence_length:].reshape((1, sequence_length, 1))
    predicted_value = model.predict(pred_input)[0, 0]
    predictions.append(predicted_value)
    last_sequence = np.append(last_sequence, predicted_value).reshape(-1, 1)

# Reverse the normalization of the predictions
forecasted_sales = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

# Plot actual vs. forecasted sales
forecast_dates = [df.index[-1] + timedelta(days=i) for i in range(1, forecast_days + 1)]

plt.figure(figsize=(10, 6))
plt.plot(df.index, df['sales'], label="Actual Sales", color="blue")
plt.plot(forecast_dates, forecasted_sales, label="Forecasted Sales", color="red", linestyle="--")
plt.xlabel("Date")
plt.ylabel("Sales")
plt.title("Actual vs. Forecasted Sales")
plt.legend()
plt.grid(True)
plt.show()
