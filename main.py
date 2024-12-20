from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Pathao API configuration
CONFIG = {
    "sandbox_base_url": "https://courier-api-sandbox.pathao.com",
    "production_base_url": "https://api-hermes.pathao.com",
    "client_id": "3YaOy0gdxq",
    "client_secret": "W7aGFZUNBXx6X9irj1ZYVgoE5Hy7RjBilrzcyLhI",
    "client_email": "appealprestige@gmail.com",
    "client_password": "5#!8Cxg3",
    "webhook_secret": "123456789abcdefg",
    "is_production": False,
}

# Helper function to get the appropriate base URL
def get_base_url():
    return CONFIG["production_base_url"] if CONFIG["is_production"] else CONFIG["sandbox_base_url"]

# Authenticate and get an access token
def authenticate():
    url = f"{get_base_url()}/aladdin/api/v1/issue-token"
    payload = {
        "client_id": CONFIG["client_id"],
        "client_secret": CONFIG["client_secret"],
        "username": CONFIG["client_email"],
        "password": CONFIG["client_password"],
        "grant_type": "password",
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception("Authentication failed: " + response.text)

# Webhook signature verification
def verify_webhook_signature(headers, payload):
    expected_signature = CONFIG["webhook_secret"]
    received_signature = headers.get("X-PATHAO-Signature", "")
    return received_signature == expected_signature

# Refresh cache for cities
def refresh_cities_cache(access_token):
    url = f"{get_base_url()}/aladdin/api/v1/city-list"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        cities = response.json()["data"]
        with open("cache/cities.json", "w") as file:
            json.dump(cities, file)
        return cities
    else:
        raise Exception("Failed to fetch cities: " + response.text)

# Route to handle webhook events
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    headers = request.headers
    payload = request.get_json()

    if not verify_webhook_signature(headers, payload):
        return jsonify({"message": "Invalid signature"}), 401

    consignment_id = payload.get("consignment_id")
    merchant_order_id = payload.get("merchant_order_id")
    order_status = payload.get("order_status")
    updated_at = payload.get("updated_at")

    if merchant_order_id:
        print(f"Order {merchant_order_id} updated to status: {order_status}")

    with open("logs/webhook_events.log", "a") as log_file:
        log_file.write(f"{datetime.now()} - Webhook: {payload}\n")

    return jsonify({"message": "Webhook processed successfully"}), 200

# Route to refresh cache for cities, zones, and areas
@app.route("/refresh-cache", methods=["POST"])
def refresh_cache():
    try:
        access_token = authenticate()
        cities = refresh_cities_cache(access_token)
        return jsonify({"message": "Cache refreshed successfully", "cities": cities}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Pathao dashboard
@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        with open("logs/webhook_events.log", "r") as log_file:
            logs = log_file.readlines()
        return jsonify({
            "balance": "1000 BDT (mocked for now, connect with Pathao API)",
            "webhook_logs": logs
        })
    except FileNotFoundError:
        return jsonify({
            "balance": "1000 BDT (mocked for now, connect with Pathao API)",
            "webhook_logs": []
        })

# Route to test if the app is running
@app.route("/", methods=["GET"])
def home():
    return "Pathao Plugin Flask App is Running!"

if __name__ == "__main__":
    app.run(debug=True)
