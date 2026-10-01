import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

BIOTIME_SERVER_URL = os.getenv('BIOTIME_SERVER_URL', 'http://127.0.0.1:8090')
BIOTIME_USERNAME = os.getenv('BIOTIME_USERNAME', '')
BIOTIME_PASSWORD = os.getenv('BIOTIME_PASSWORD', '')

print(f"Testing POST to {BIOTIME_SERVER_URL}")

url = f"{BIOTIME_SERVER_URL}/jwt-api-token-auth/"
try:
    response = requests.post(url, json={
        "username": BIOTIME_USERNAME,
        "password": BIOTIME_PASSWORD
    }, timeout=10)
    
    if response.status_code == 200:
        token = response.json().get('token')
        print("Got token!")
        
        # Test POST to transactions
        tx_url = f"{BIOTIME_SERVER_URL}/iclock/api/transactions/"
        
        payload = {
            "emp_code": "103",
            "punch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "punch_state": "0", # 0 for Check-in
            "verify_type": 1,
            "terminal_sn": "WEB_PUNCH"
        }
        
        print("Sending POST request with payload:", payload)
        tx_res = requests.post(tx_url, headers={"Authorization": f"JWT {token}"}, json=payload)
        
        print("Transaction Status:", tx_res.status_code)
        print("Transaction Response:", tx_res.text)
        
except Exception as e:
    print(f"Error: {e}")
