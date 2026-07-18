import requests

try:
    resp = requests.post("http://127.0.0.1:10000/chat", json={"query": "Inception", "exclude_ids": []})
    print(resp.status_code)
    print(resp.json())
except Exception as e:
    print(f"Error: {e}")
