import requests

url = "http://127.0.0.1:5000/add_sales"
data = {"date": "2025-02-24", "sales": 150}

response = requests.post(url, json=data)
print(response.json())
