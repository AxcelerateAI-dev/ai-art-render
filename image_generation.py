import json
import time
import http.client
import pprint
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

data = {
    "prompt": "boys playing soccer in a park --ar 9:21 --chaos 40 --stylize 1000"
}

headers = {
    'Authorization': f"Bearer {os.getenv('IMAGINE_DEV_API_KEY')}",
    'Content-Type': 'application/json'
}

def send_request(method, path, body=None, headers={}):
    conn = http.client.HTTPSConnection("cl.imagineapi.dev")
    conn.request(method, path, body=json.dumps(body) if body else None, headers=headers)
    response = conn.getresponse()
    data = json.loads(response.read().decode())
    conn.close()
    return data

def append_to_json_file(data, filename="responses.json"):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        else:
            existing_data = []

        existing_data.append(data)

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4)
        print(f"✅ Response saved to {filename}")
    except Exception as e:
        print("❌ Failed to save response:", e)

prompt_response_data = send_request('POST', '/items/images/', data, headers)

def check_image_status():
    response_data = send_request('GET', f"/items/images/{prompt_response_data['data']['id']}", headers=headers)
    if response_data['data']['status'] in ['completed', 'failed']:
        print('✅ Completed image details:')
        pprint.pp(response_data['data'])

        return response_data['data'], True
    else:
        print(f"⏳ Image not finished. Status: {response_data['data']['status']}")
        return None, False

# Polling loop
while True:
    image_data, done = check_image_status()
    if not done:
        time.sleep(5)
    else:
        append_to_json_file(image_data)
        break
