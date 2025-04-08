import os
import secrets
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, ResetRequestForm, ResetPasswordForm
from dotenv import load_dotenv
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from tensorflow.keras.metrics import MeanSquaredError 
from tensorflow.keras.models import load_model
import joblib
import logging
import sys

# suppress tensorflow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# logging configuration
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
logging.error("App started successfully!")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# CSRF Protection
csrf = CSRFProtect(app)

# Configure MySQL
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "Dhanush@7")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "demand_forecasting")
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

# Configure Flask-Mail
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
mail = Mail(app)

# Load trained models
try:
    lstm_model = load_model("models/lstm_model.h5", custom_objects={'mse': MeanSquaredError()})
except Exception as e:
    lstm_model = None
    logging.error(f"ERROR - LSTM model not loaded: {e}")

# Load scaler
try:
    scaler = joblib.load("models/scaler.pkl")
except Exception as e:
    scaler = None
    logging.error(f"ERROR - Scaler not loaded: {e}")

# ==============================
# Function to Fetch Sales Data
# ==============================
def get_sales_data():
    cur = mysql.connection.cursor()
    cur.execute("SELECT date, sales, promotion, temperature, feature4, feature5 FROM sales_data ORDER BY date")
    data = cur.fetchall()
    cur.close()
    
    df = pd.DataFrame(data, columns=["date", "sales", "promotion", "temperature", "feature4", "feature5"])
    df["date"] = pd.to_datetime(df["date"])

    # Drop rows with missing values
    if df.isnull().values.any():
        df = df.dropna()

    return df

# ==============================
# API to Fetch Sales Data
# ==============================
@app.route("/sales-data")
def sales_data():
    df = get_sales_data()
    return jsonify(df.to_dict(orient="records"))

# ==============================
# API to Predict Future Sales
# ==============================
@app.route("/predict", methods=["POST"])
@csrf.exempt
def predict():
    try:
        data = request.get_json()
        model_type = data.get("model", "lstm")
        days = int(data["days"])
        
        df = get_sales_data()

        # Sort dates to ensure order
        df.sort_values("date", inplace=True)

        if model_type == "lstm" and lstm_model:
            last_values = df[["sales", "temperature", "promotion", "feature4", "feature5"]].values[-30:]
            input_data = np.array(last_values).reshape(1, 30, 5)

            scaled_input = scaler.transform(input_data.reshape(-1, 5))
            scaled_input = scaled_input.reshape(1, 30, 5)

            predictions = lstm_model.predict(scaled_input)
            predictions = scaler.inverse_transform(predictions.reshape(-1, 1)).flatten().tolist()

        elif model_type == "arima":
            model = ARIMA(df["sales"], order=(5, 1, 0))
            fitted = model.fit()
            predictions = fitted.forecast(steps=days).tolist()

        elif model_type == "prophet":
            df.rename(columns={"date": "ds", "sales": "y"}, inplace=True)
            model = Prophet()
            model.fit(df)
            future = model.make_future_dataframe(periods=days)
            forecast = model.predict(future)
            predictions = forecast["yhat"].iloc[-days:].tolist()

        else:
            return jsonify({"error": "Invalid model type or model not loaded"})

        # ✅ generate continuous forecast dates starting after the last actual date
        last_actual_date = pd.to_datetime(df["date"].max())
        forecast_dates = [(last_actual_date + timedelta(days=i + 1)).strftime("%Y-%m-%d") for i in range(len(predictions))]

        return jsonify({"dates": forecast_dates, "forecast": predictions})
    
    except Exception as e:
        logging.error(f"Prediction Error: {str(e)}")
        return jsonify({"error": str(e)})

# ==============================
# User Authentication Routes
# ==============================
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password)

        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", 
                        (username, email, hashed_password))
            mysql.connection.commit()
            cur.close()
            flash("Registration successful!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash("Error registering user.", "danger")
            logging.error(f"Registration Error: {e}")

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials!", "danger")

    return render_template("login.html", form=form)
@app.route("/reset_request", methods=["GET", "POST"])
def reset_request():
    form = ResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            token = secrets.token_hex(16)  # Generate a secure token
            reset_link = url_for("reset_password", token=token, _external=True)

            # Send reset link via email
            try:
                msg = Message("Password Reset Request",
                              sender=os.getenv("MAIL_USERNAME"),
                              recipients=[email])
                msg.body = f"To reset your password, visit the following link: {reset_link}\nIf you did not request this, please ignore this email."
                mail.send(msg)
                flash("An email with instructions to reset your password has been sent.", "info")
            except Exception as e:
                logging.error(f"Error sending reset email: {e}")
                flash("Error sending reset email. Please try again later.", "danger")
        else:
            flash("No account found with that email address.", "warning")
        
        return redirect(url_for("login"))

    return render_template("reset_request.html", form=form)
@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        password = form.password.data
        hashed_password = generate_password_hash(password)

        # Update password in the database
        try:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", 
                        (hashed_password, form.email.data))
            mysql.connection.commit()
            cur.close()
            flash("Your password has been updated!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash("Error updating password.", "danger")
            logging.error(f"Password Reset Error: {e}")

    return render_template("reset_password.html", form=form)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

# ==============================
# Home Route
# ==============================
@app.route("/")
def home():
    return redirect(url_for("dashboard"))

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
