import requests
import json

# Test data
test_data = {
    "client_id": 1,
    "date_issued": "2025-09-16",
    "due_date": "2025-10-16",
    "tax_rate": 10.0,
    "notes": "Test invoice from API",
    "terms": "Payment due in 30 days",
    "status": "draft",
    "items": [
        {
            "description": "Test Item 1",
            "quantity": 2,
            "unit_price": 50.00
        },
        {
            "description": "Test Item 2",
            "quantity": 1,
            "unit_price": 75.00
        }
    ]
}

# Send POST request to the API endpoint
url = "http://127.0.0.1:8000/api/invoices/add/"
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, data=json.dumps(test_data), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")