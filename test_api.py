import requests
import json

# Test the API endpoint
url = "http://localhost:8000/scrape-menu"
test_url = "https://www.google.com/maps/place/CAVA/@33.5087058,-112.0458579,17z/data=!3m1!4b1!4m6!3m5!1s0x872b0dc8ef74aa11:0x4f3ccce4e3eb8f6e!8m2!3d33.5087058!4d-112.0458579!16s%2Fg%2F11rq8nl6lt?entry=ttu&g_ep=EgoyMDI1MTEyMy4xIKXMDSoASAFQAw%3D%3D"

payload = {"url": test_url}

print("Testing FastAPI server...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload, timeout=120)
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse JSON:")
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.ConnectionError:
    print("\n❌ Connection refused. Make sure the server is running:")
    print("   python server.py")
except Exception as e:
    print(f"\n❌ Error: {e}")

