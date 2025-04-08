import pandas as pd

# Path to your downloaded CSV file
file_path = "C:/Users/dhanu/Downloads/Retail Transactions export 2025-03-31 14-35-51/sales_data.csv"  

# Read the CSV file
df = pd.read_csv(file_path)

# Print the first few rows to see the structure
print("\nFirst 5 Rows:")
print(df.head())

# Print the column names to understand the structure
print("\nColumn Names:")
print(df.columns)

# Check for missing values
print("\nMissing Values:")
print(df.isnull().sum())

# Get basic statistical summary
print("\nStatistical Summary:")
print(df.describe())
