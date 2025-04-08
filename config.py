import os

class Config:
    SECRET_KEY = 'your_secret_key'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'your_mysql_password'
    MYSQL_DB = 'demand_forecasting'
    MYSQL_CURSORCLASS = 'DictCursor'
