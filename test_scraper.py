import requests
import json
import time

# Wait for server to be ready
time.sleep(2)

url = "http://localhost:8000/scrape-menu"
test_url = "https://www.google.com/maps/search/?api=1&query=CAVA&query_place_id=ChIJEap078gNK4cRbo_r4-TMPE8"

payload = {"url": test_url}

print(f"Testing with URL: {test_url}")
print("Sending request...")

response = requests.post(url, json=payload, timeout=120)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

