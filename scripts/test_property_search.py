import urllib.request
import json
import time

def test_property_search():
    url = "http://localhost:8001/query"
    # Question: Find a house near Yonsei University
    data = {"question": "연세대학교 근처에 있는 집 찾아줘"}
    headers = {'Content-Type': 'application/json'}
    
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
    
    print(f"Sending request to {url} with data: {data}")
    
    max_retries = 10
    for i in range(max_retries):
        try:
            with urllib.request.urlopen(req) as response:
                result = response.read().decode('utf-8')
                print("Response:")
                print(result)
                return
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            time.sleep(5)
            
    print("Failed to connect to RAG service after multiple attempts.")

if __name__ == "__main__":
    test_property_search()
