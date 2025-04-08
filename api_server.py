from flask import Flask, request, jsonify
import pymysql

app = Flask(__name__)

# mysql database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Dhanush@7",
    "database": "demand_forecasting"
}

# function to insert sales data into mysql
def insert_sales_data(date, sales):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    query = "INSERT INTO sales_data (date, sales) VALUES (%s, %s)"
    cursor.execute(query, (date, sales))
    conn.commit()
    conn.close()

# api route to add sales data
@app.route("/add_sales", methods=["POST"])
def add_sales():
    data = request.get_json()

    # validate input data
    if "date" not in data or "sales" not in data:
        return jsonify({"error": "missing date or sales value"}), 400

    try:
        insert_sales_data(data["date"], data["sales"])
        return jsonify({"message": "✅ sales data added successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# run the flask api
if __name__ == "__main__":
    app.run(debug=True)
