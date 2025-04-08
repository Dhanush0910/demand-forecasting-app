import pandas as pd

# Path to your CSV file
file_path = "C:/Users/dhanu/Downloads/Retail Transactions export 2025-03-31 14-35-51/sales_data.csv"  # Update with actual path

# Load the data
df = pd.read_csv(file_path)

# Feature Engineering
df["date"] = pd.to_datetime(df["Date"])
df["sales"] = df["Units Sold"]  # Mapping "Units Sold" to "sales"
df["promotion"] = df["Discount Percentage"]  # Mapping "Discount Percentage" to "promotion"
df["temperature"] = df["Marketing Spend (USD)"] / 10  # Synthetic temperature
df["feature4"] = df["Day of the Week"].astype("category").cat.codes  # Encode day of the week
df["feature5"] = df["Holiday Effect"].astype(int)  # Convert boolean to int

# Select relevant columns and sort by date
df = df[["date", "sales", "promotion", "temperature", "feature4", "feature5"]].sort_values(by="date")

# Save the preprocessed data to a new CSV file
output_path = "C:/Users/dhanu/OneDrive/Desktop/demand-forecasting-app/preprocessed_data.csv"  # Update with actual path
df.to_csv(output_path, index=False)

print("Data preprocessing complete. Preprocessed data saved to:", output_path)
