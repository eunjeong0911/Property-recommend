import requests

try:
    response = requests.get("http://localhost:8000/api/listings/lands/")
    print(f"Status Code: {response.status_code}")
    with open("error_full.html", "w", encoding="utf-8") as f:
        f.write(response.text)
except Exception as e:
    print(e)
