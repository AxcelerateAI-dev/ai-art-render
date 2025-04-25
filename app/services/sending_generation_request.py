import time
import http.client
import json
import os

API_HOST = "cl.imagineapi.dev"
API_AUTH = f"Bearer {os.getenv('IMAGINE_DEV_API_KEY')}"

def send_request(method, path, body=None, headers={}):
    conn = http.client.HTTPSConnection(API_HOST)
    conn.request(method, path, body=json.dumps(body) if body else None, headers=headers)
    response = conn.getresponse()
    data = json.loads(response.read().decode())
    conn.close()
    return data